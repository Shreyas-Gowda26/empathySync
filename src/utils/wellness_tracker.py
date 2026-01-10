"""
Simple wellness tracking for empathySync users
Local storage of wellness check-ins and patterns
"""

import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import settings

class WellnessTracker:
    """Track user wellness patterns locally"""
    
    def __init__(self):
        self.data_file = settings.DATA_DIR / "wellness_data.json"
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """Ensure wellness data file exists"""
        if not self.data_file.exists():
            self._save_data({
                "check_ins": [],
                "usage_sessions": [],
                "created_at": datetime.now().isoformat()
            })
    
    def add_check_in(self, feeling_score: int, notes: str = ""):
        """Add a wellness check-in (1-5 scale)"""
        data = self._load_data()
        
        check_in = {
            "date": date.today().isoformat(),
            "datetime": datetime.now().isoformat(),
            "feeling_score": feeling_score,
            "notes": notes
        }
        
        data["check_ins"].append(check_in)
        self._save_data(data)
        
        return check_in
    
    def get_recent_check_ins(self, days: int = 7) -> List[Dict]:
        """Get check-ins from last N days"""
        data = self._load_data()
        recent = data["check_ins"][-days:] if data["check_ins"] else []
        return recent
    
    def get_today_check_in(self) -> Optional[Dict]:
        """Check if user has checked in today"""
        today_str = date.today().isoformat()
        data = self._load_data()
        
        for check_in in reversed(data["check_ins"]):
            if check_in["date"] == today_str:
                return check_in
        
        return None
    
    def add_session(self, duration_minutes: int):
        """Track a usage session"""
        data = self._load_data()
        
        session = {
            "date": date.today().isoformat(),
            "datetime": datetime.now().isoformat(),
            "duration_minutes": duration_minutes
        }
        
        data["usage_sessions"].append(session)
        self._save_data(data)
    
    def get_wellness_summary(self) -> Dict:
        """Get summary of wellness patterns"""
        data = self._load_data()
        
        if not data["check_ins"]:
            return {"message": "No check-ins yet", "days_active": 0}
            
        total_checkins = len(data["check_ins"])
        unique_dates = len(set(c["date"] for c in data["check_ins"]))
        
        # Calculate average feeling score
        scores = [c["feeling_score"] for c in data["check_ins"]]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_checkins": total_checkins,
            "days_active": unique_dates,
            "average_feeling": round(avg_score, 1),
            "latest_checkin": data["check_ins"][-1]["date"] if data["check_ins"] else None
        }
    
    def _load_data(self) -> Dict:
        """Load wellness data from file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {"check_ins": [], "usage_sessions": []}
    
    def _save_data(self, data: Dict):
        """Save wellness data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
