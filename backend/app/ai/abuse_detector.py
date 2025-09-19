import os
import groq
from dotenv import load_dotenv
import re
import json

# Load environment variables
load_dotenv()

class AbuseDetector:
    def __init__(self):
        # Initialize Groq client if API key is available
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.groq_api_key:
            self.client = groq.Client(api_key=self.groq_api_key)
        
        # Fallback keyword-based detection
        self.abusive_keywords = [
            "idiot", "stupid", "dumb", "moron", "loser", 
            "bitch", "slut", "whore", "cunt", "pussy",
            "kill yourself", "kys", "die", "hate you",
            "ugly", "fat", "worthless", "pathetic", "useless",
            "retard", "retarded", "fuck you", "fucking", "asshole"
        ]
        
    def analyze_text(self, text):
        """
        Analyze text for abusive content
        Returns: (is_abusive, abuse_score, analysis_details)
        """
        # Try using Groq if available
        if self.client:
            try:
                return self._analyze_with_groq(text)
            except Exception as e:
                print(f"Error with Groq API: {e}")
                # Fall back to keyword-based detection
                return self._analyze_with_keywords(text)
        else:
            # Use keyword-based detection if Groq is not available
            return self._analyze_with_keywords(text)
    
    def _analyze_with_groq(self, text):
        """Analyze text using Groq LLM API"""
        prompt = f"""
        Analyze the following message for abusive or harassing content. 
        Focus on detecting cyberbullying, hate speech, threats, and harassment.
        
        Message: "{text}"
        
        Provide a JSON response with the following fields:
        - is_abusive: boolean (true if the message contains abusive content)
        - abuse_score: integer from 0-100 (0 being not abusive at all, 100 being extremely abusive)
        - categories: list of detected abuse categories (e.g., "harassment", "hate_speech", "threat", "sexual", "bullying")
        - explanation: brief explanation of why the message was flagged or not
        
        JSON response:
        """
        
        # Call Groq API
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",  # Using Llama 3 model
            max_tokens=500
        )
        
        # Extract and parse the response
        response_text = chat_completion.choices[0].message.content
        
        # Extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                analysis = json.loads(json_match.group(0))
                return (
                    analysis.get("is_abusive", False),
                    analysis.get("abuse_score", 0),
                    analysis
                )
            except json.JSONDecodeError:
                # Fall back to keyword detection if JSON parsing fails
                return self._analyze_with_keywords(text)
        else:
            return self._analyze_with_keywords(text)
    
    def _analyze_with_keywords(self, text):
        """Simple keyword-based abuse detection as fallback"""
        text_lower = text.lower()
        
        # Count matches
        matches = [keyword for keyword in self.abusive_keywords if keyword in text_lower]
        match_count = len(matches)
        
        # Calculate abuse score (0-100)
        if match_count == 0:
            abuse_score = 0
        else:
            # More matches = higher score
            abuse_score = min(100, match_count * 25)
        
        # Determine if abusive based on threshold
        is_abusive = abuse_score >= 25
        
        # Create analysis details
        analysis = {
            "is_abusive": is_abusive,
            "abuse_score": abuse_score,
            "categories": ["keyword_detected"] if is_abusive else [],
            "explanation": f"Detected {match_count} abusive keywords" if is_abusive else "No abusive content detected",
            "matched_keywords": matches if is_abusive else []
        }
        
        return (is_abusive, abuse_score, analysis)