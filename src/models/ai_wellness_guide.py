"""
AI Wellness Guide - Core empathetic conversation engine
Leveraging your Ollama infrastructure for local AI processing
"""

import requests
import json
import logging
from typing import List, Dict, Optional
from config.settings import settings
from prompts.wellness_prompts import WellnessPrompts
from models.risk_classifier import RiskClassifier


logger = logging.getLogger(__name__)

class WellnessGuide:
    """Empathetic AI guide for healthy AI relationships"""
    
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_HOST}/api/generate"
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.OLLAMA_TEMPERATURE
        self.prompts = WellnessPrompts()
        self.risk_classifier = RiskClassifier()

    
    def generate_response(
        self, 
        user_input: str, 
        wellness_mode: str = "Balanced",
        conversation_history: List[Dict] = None
    ) -> str:
        """Generate empathetic response to user input, with risk awareness."""
        
        if conversation_history is None:
            conversation_history = []

        try:
            # 1) Risk assessment (Phase 1: awareness only)
            risk_assessment = self.risk_classifier.classify(
                user_input=user_input,
                conversation_history=conversation_history
            )

            logger.info(
                "Risk assessment | domain=%s | intensity=%.2f | dependency=%.2f | weight=%.2f",
                risk_assessment["domain"],
                risk_assessment["emotional_intensity"],
                risk_assessment["dependency_risk"],
                risk_assessment["risk_weight"],
            )

            # (Optional) store last assessment if you want to surface later in UI
            self.last_risk_assessment = risk_assessment

            # 2) Build context-aware prompt (same as before)
            system_prompt = self.prompts.get_system_prompt(wellness_mode)
            conversation_context = self._build_context(conversation_history)

            full_prompt = (
                f"{system_prompt}\n\n"
                f"{conversation_context}\n\n"
                f"User: {user_input}\n\n"
                f"Assistant:"
            )

            # 3) Call Ollama API
            response = self._call_ollama(full_prompt)

            # 4) Process and validate response
            processed_response = self._process_response(response, user_input)

            return processed_response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._get_fallback_response()

    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with error handling"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        try:
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise Exception(f"Unable to connect to Ollama. Please ensure it's running at {settings.OLLAMA_HOST}")
    
    def _build_context(self, conversation_history: List[Dict]) -> str:
        """Build conversation context from history"""
        
        if not conversation_history:
            return "This is the start of a new conversation."
        
        # Keep last 5 exchanges for context
        recent_history = conversation_history[-10:]
        
        context = "Previous conversation:\n"
        for msg in recent_history:
            role = msg.get("role", "").capitalize()
            content = msg.get("content", "")[:200]  # Limit length
            context += f"{role}: {content}\n"
        
        return context
    
    def _process_response(self, response: str, user_input: str) -> str:
        """Process and validate AI response for safety and empathy"""
        
        if not response:
            return self._get_fallback_response()
        
        # Basic safety checks
        if self._contains_harmful_content(response):
            logger.warning("Potentially harmful content detected in response")
            return self._get_safe_alternative_response()
        
        # Ensure response is empathetic and helpful
        if len(response.strip()) < 10:
            return self._get_fallback_response()
        
        return response
    
    def _contains_harmful_content(self, text: str) -> bool:
        """Basic safety check for harmful content"""
        
        harmful_indicators = [
            "you should feel bad",
            "you're addicted",
            "something is wrong with you",
            "you need professional help immediately"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in harmful_indicators)
    
    def _get_fallback_response(self) -> str:
        """Safe fallback response when AI is unavailable"""
        return ("I want to help you develop a healthier relationship with AI, "
                "but I'm having trouble generating a response right now. "
                "How are you feeling about your technology use today?")
    
    def _get_safe_alternative_response(self) -> str:
        """Safe alternative when potentially harmful content is detected"""
        return ("I care about your wellbeing and want to help you reflect on your "
                "relationship with AI in a supportive way. What specific aspects of "
                "AI usage would you like to explore together?")
    
    def check_health(self) -> bool:
        """Check if Ollama connection is healthy"""
        try:
            test_response = self._call_ollama("Hello")
            return bool(test_response)
        except:
            return False
