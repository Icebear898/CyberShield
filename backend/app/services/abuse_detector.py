import re
from typing import Tuple, Dict, Any

class AbuseDetector:
    """Simple abuse detection system using keyword matching and pattern analysis"""
    
    def __init__(self):
        # Define abusive keywords and their severity scores
        self.abusive_keywords = {
            # High severity (8-10)
            'hate': 9.0,
            'kill': 10.0,
            'die': 9.0,
            'death': 8.5,
            'murder': 10.0,
            'suicide': 9.5,
            
            # Medium-high severity (6-8)
            'bitch': 7.0,
            'fuck': 6.5,
            'shit': 6.0,
            'damn': 5.5,
            'hell': 5.0,
            'bastard': 7.5,
            'asshole': 7.0,
            
            # Medium severity (4-6)
            'stupid': 4.5,
            'idiot': 5.0,
            'loser': 4.0,
            'ugly': 3.5,
            'fat': 3.0,
            'worthless': 6.0,
            
            # Harassment patterns
            'nobody likes you': 8.0,
            'everyone hates you': 8.5,
            'you should': 7.0,  # Often followed by harmful suggestions
            'go away': 4.0,
            'shut up': 5.0,
        }
        
        # Patterns that indicate abuse
        self.abusive_patterns = [
            r'\b(you\s+are\s+so\s+\w+)\b',  # "you are so [negative word]"
            r'\b(i\s+hate\s+you)\b',        # "i hate you"
            r'\b(go\s+\w+\s+yourself)\b',   # "go [verb] yourself"
            r'\b(nobody\s+\w+\s+you)\b',    # "nobody [verb] you"
            r'\b(you\s+should\s+\w+)\b',    # "you should [harmful action]"
        ]
    
    def analyze_text(self, text: str) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Analyze text for abusive content
        
        Returns:
            Tuple of (is_abusive, abuse_score, analysis_details)
        """
        if not text or not text.strip():
            return False, 0.0, {"reason": "Empty text"}
        
        text_lower = text.lower().strip()
        abuse_score = 0.0
        detected_keywords = []
        detected_patterns = []
        
        # Check for abusive keywords
        for keyword, score in self.abusive_keywords.items():
            if keyword in text_lower:
                abuse_score = max(abuse_score, score)
                detected_keywords.append(keyword)
        
        # Check for phrase-based detection for specific abuse types
        phrases_to_check = [
            'send me your nude', 'show me your body', 'give me your money', 'pay me $',
            'expose your secrets', 'share your photos', 'unless you', 'or else',
            'kill yourself', 'hurt yourself', 'nobody cares', 'i will kill you',
            'i will hurt you', 'i will find you', 'send pics baby'
        ]
        
        for phrase in phrases_to_check:
            if phrase in text_lower:
                abuse_score = max(abuse_score, 7.0)  # High score for specific phrases
                detected_keywords.append(phrase)
        
        # Check for abusive patterns
        for pattern in self.abusive_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                abuse_score = max(abuse_score, 7.0)  # Pattern matches get high score
                detected_patterns.extend(matches)
        
        # Additional scoring based on text characteristics
        if len(text_lower) > 0:
            # Check for excessive caps (shouting)
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.7 and len(text) > 10:
                abuse_score += 1.0
            
            # Check for excessive punctuation (aggressive tone)
            punct_ratio = sum(1 for c in text if c in '!?') / len(text)
            if punct_ratio > 0.2:
                abuse_score += 0.5
        
        # Normalize score to 0-10 range
        abuse_score = min(abuse_score, 10.0)
        
        # Determine if text is abusive (threshold: 4.0)
        is_abusive = abuse_score >= 4.0
        
        analysis = {
            "detected_keywords": detected_keywords,
            "detected_patterns": detected_patterns,
            "caps_ratio": caps_ratio if 'caps_ratio' in locals() else 0.0,
            "punct_ratio": punct_ratio if 'punct_ratio' in locals() else 0.0,
            "threshold_used": 4.0,
            "classification": self._classify_abuse_type(detected_keywords, detected_patterns)
        }
        
        return is_abusive, abuse_score, analysis
    
    def _classify_abuse_type(self, keywords: list, patterns: list) -> str:
        """Classify the type of abuse detected"""
        
        # Cyberbullying keywords
        cyberbullying_words = ['loser', 'stupid', 'idiot', 'worthless', 'nobody likes you', 'everyone hates you', 'ugly', 'fat']
        
        # Sexual harassment keywords
        sexual_harassment_words = ['sexy', 'hot', 'nude', 'naked', 'send pics', 'show me', 'sexual', 'body', 'breast', 'private', 'pics baby', 'send me your']
        
        # Exploitation keywords
        exploitation_words = ['money', 'pay me', 'give me', 'steal', 'scam', 'fraud', 'trick', 'use you', 'give me your money', 'pay me $']
        
        # Blackmail keywords
        blackmail_words = ['expose', 'tell everyone', 'share photos', 'blackmail', 'secret', 'unless you', 'or else', 'expose your secrets', 'share your photos']
        
        # Mental harassment keywords
        mental_harassment_words = ['kill yourself', 'suicide', 'die', 'worthless', 'nobody cares', 'alone', 'depressed', 'hurt yourself']
        
        # Threat keywords
        threat_words = ['kill', 'hurt', 'beat', 'destroy', 'revenge', 'get you', 'find you', 'come for you', 'murder', 'violence']
        
        # Convert keywords to string for phrase checking
        keywords_text = ' '.join(keywords).lower()
        
        # Check for each category (order matters - most specific first)
        if any(word in keywords_text for word in threat_words) or any('kill' in pattern or 'hurt' in pattern for pattern in patterns):
            return "THREAT"
        elif any(word in keywords_text for word in mental_harassment_words):
            return "MENTAL_HARASSMENT"
        elif any(word in keywords_text for word in blackmail_words):
            return "BLACKMAIL"
        elif any(word in keywords_text for word in exploitation_words):
            return "EXPLOITATION"
        elif any(word in keywords_text for word in sexual_harassment_words):
            return "SEXUAL_HARASSMENT"
        elif any(word in keywords_text for word in cyberbullying_words):
            return "CYBERBULLYING"
        else:
            return "CYBERBULLYING"  # Default to cyberbullying for general abuse
    
    def get_abuse_severity(self, score: float) -> str:
        """Get human-readable severity level"""
        if score >= 8.0:
            return "SEVERE"
        elif score >= 6.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def is_safe_content(self, text: str) -> bool:
        """Quick check if content is safe (not abusive)"""
        is_abusive, _, _ = self.analyze_text(text)
        return not is_abusive
