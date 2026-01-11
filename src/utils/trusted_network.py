"""
Trusted Network - Local storage and management of user's trusted humans

This module helps users identify, remember, and reach out to
the real humans in their life. All data stays local.
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional
import random

from config.settings import settings
from utils.scenario_loader import get_scenario_loader


class TrustedNetwork:
    """
    Manages the user's network of trusted humans.

    Helps answer the question: "Who in your life could you talk to about this?"
    All data stored locally. No external calls.
    """

    def __init__(self):
        self.data_file = settings.DATA_DIR / "trusted_network.json"
        self.loader = get_scenario_loader()
        self._ensure_data_file()

    def _ensure_data_file(self):
        """Ensure data file exists with default structure."""
        if not self.data_file.exists():
            self._save_data({
                "people": [],
                "reach_outs": [],  # Log of when user reached out
                "created_at": datetime.now().isoformat()
            })

    def _load_data(self) -> Dict:
        """Load network data from file."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {"people": [], "reach_outs": []}

    def _save_data(self, data: Dict):
        """Save network data to file."""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)

    # ==================== MANAGING TRUSTED PEOPLE ====================

    def add_person(self, name: str, relationship: str = "",
                   contact: str = "", notes: str = "",
                   domains: List[str] = None) -> Dict:
        """
        Add a trusted person to the network.

        Args:
            name: Their name
            relationship: e.g., "friend", "sister", "mentor", "therapist"
            contact: Phone number, email, or how to reach them
            notes: Any notes about this person
            domains: Topics they're good for (e.g., ["money", "relationships"])
        """
        data = self._load_data()

        person = {
            "id": len(data["people"]) + 1,
            "name": name,
            "relationship": relationship,
            "contact": contact,
            "notes": notes,
            "domains": domains or [],
            "added_at": datetime.now().isoformat(),
            "last_contact": None
        }

        data["people"].append(person)
        self._save_data(data)

        return person

    def get_all_people(self) -> List[Dict]:
        """Get all trusted people."""
        data = self._load_data()
        return data.get("people", [])

    def get_person_by_name(self, name: str) -> Optional[Dict]:
        """Find a person by name (case-insensitive partial match)."""
        people = self.get_all_people()
        name_lower = name.lower()
        for person in people:
            if name_lower in person["name"].lower():
                return person
        return None

    def get_people_for_domain(self, domain: str) -> List[Dict]:
        """Get people suited for a particular topic/domain."""
        people = self.get_all_people()
        matches = [p for p in people if domain in p.get("domains", [])]

        # If no specific matches, return all people
        if not matches:
            return people

        return matches

    def update_person(self, person_id: int, updates: Dict) -> Optional[Dict]:
        """Update a person's information."""
        data = self._load_data()

        for person in data["people"]:
            if person["id"] == person_id:
                person.update(updates)
                self._save_data(data)
                return person

        return None

    def remove_person(self, person_id: int) -> bool:
        """Remove a person from the network."""
        data = self._load_data()
        original_count = len(data["people"])
        data["people"] = [p for p in data["people"] if p["id"] != person_id]

        if len(data["people"]) < original_count:
            self._save_data(data)
            return True
        return False

    # ==================== TRACKING REACH OUTS ====================

    def log_reach_out(self, person_name: str, method: str = "unknown",
                      topic: str = "", notes: str = ""):
        """
        Log when user reaches out to someone.

        This is a success metric - we want to see this increase.
        """
        data = self._load_data()

        reach_out = {
            "date": date.today().isoformat(),
            "datetime": datetime.now().isoformat(),
            "person_name": person_name,
            "method": method,  # call, text, in-person, etc.
            "topic": topic,
            "notes": notes
        }

        data["reach_outs"].append(reach_out)

        # Update last_contact for this person
        for person in data["people"]:
            if person["name"].lower() == person_name.lower():
                person["last_contact"] = date.today().isoformat()

        self._save_data(data)
        return reach_out

    def get_recent_reach_outs(self, days: int = 30) -> List[Dict]:
        """Get reach outs from the last N days."""
        data = self._load_data()
        cutoff = (datetime.now().date() - __import__('datetime').timedelta(days=days)).isoformat()

        return [r for r in data.get("reach_outs", [])
                if r.get("date", "") >= cutoff]

    def count_reach_outs_this_week(self) -> int:
        """Count reach outs in the past 7 days."""
        return len(self.get_recent_reach_outs(7))

    def get_neglected_contacts(self, days: int = 30) -> List[Dict]:
        """Get people you haven't contacted in a while."""
        people = self.get_all_people()
        cutoff = (datetime.now().date() - __import__('datetime').timedelta(days=days)).isoformat()

        neglected = []
        for person in people:
            last = person.get("last_contact")
            if not last or last < cutoff:
                neglected.append(person)

        return neglected

    # ==================== PROMPTS AND SUGGESTIONS ====================

    def get_setup_prompt(self) -> str:
        """Get a prompt to help user set up their trusted network."""
        prompts = self.loader.get_all_prompts().get("human_connection", {})
        setup_prompts = prompts.get("trusted_network_prompts", {}).get("initial_setup", [])

        if setup_prompts:
            return random.choice(setup_prompts)
        return "Who are 2-3 people in your life you could call if things got hard?"

    def get_reflection_prompt(self) -> str:
        """Get a prompt for reflecting on relationships."""
        prompts = self.loader.get_all_prompts().get("human_connection", {})
        reflection = prompts.get("trusted_network_prompts", {}).get("reflection", [])

        if reflection:
            return random.choice(reflection)
        return "When did you last have a real conversation with someone you trust?"

    def get_domain_prompt(self, domain: str) -> str:
        """Get a prompt specific to a domain."""
        prompts = self.loader.get_all_prompts().get("human_connection", {})
        by_domain = prompts.get("trusted_network_prompts", {}).get("prompts_by_domain", {})

        domain_prompts = by_domain.get(domain, by_domain.get("general", []))

        if domain_prompts:
            return random.choice(domain_prompts)
        return "Who in your life could you talk to about this?"

    def get_reach_out_template(self, situation: str = "need_to_talk") -> Dict:
        """
        Get a template for reaching out.

        Args:
            situation: One of "reconnecting", "need_to_talk", "checking_in",
                      "hard_conversation", "asking_for_help", "after_argument", "gratitude"
        """
        prompts = self.loader.get_all_prompts().get("human_connection", {})
        templates = prompts.get("reach_out_templates", {})

        if situation in templates:
            template_group = templates[situation]
            return {
                "name": template_group.get("name", situation),
                "template": random.choice(template_group.get("templates", []))
            }

        # Default
        return {
            "name": "Reaching out",
            "template": "Hey, I've been thinking about you. Could we talk sometime?"
        }

    def get_exit_celebration(self, chose_human: bool = True) -> str:
        """Get an exit celebration message."""
        prompts = self.loader.get_all_prompts().get("human_connection", {})
        celebrations = prompts.get("exit_celebrations", {})

        if chose_human:
            messages = celebrations.get("chose_human", [])
        else:
            messages = celebrations.get("ending_session", [])

        if messages:
            return random.choice(messages)
        return "You're choosing human connection. That's the point."

    def suggest_person_for_domain(self, domain: str) -> Optional[Dict]:
        """Suggest a person from the network for a given domain."""
        people = self.get_people_for_domain(domain)

        if people:
            return random.choice(people)
        return None

    # ==================== HEALTH METRICS ====================

    def get_connection_health(self) -> Dict:
        """
        Get metrics about connection health.

        Success = more reach outs, less AI usage.
        """
        people = self.get_all_people()
        reach_outs_week = self.count_reach_outs_this_week()
        reach_outs_month = len(self.get_recent_reach_outs(30))
        neglected = self.get_neglected_contacts()

        return {
            "total_trusted_people": len(people),
            "reach_outs_this_week": reach_outs_week,
            "reach_outs_this_month": reach_outs_month,
            "neglected_contacts": len(neglected),
            "network_configured": len(people) > 0,
            "is_reaching_out": reach_outs_week > 0
        }

    def clear_data(self):
        """Clear all network data."""
        self._save_data({
            "people": [],
            "reach_outs": [],
            "created_at": datetime.now().isoformat()
        })
