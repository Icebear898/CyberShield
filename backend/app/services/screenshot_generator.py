from PIL import Image, ImageDraw, ImageFont
import os
import datetime
from typing import List, Dict

class ScreenshotGenerator:
    """Generate screenshots of chat messages for evidence reports"""
    
    def __init__(self):
        self.width = 800
        self.message_height = 80
        self.padding = 20
        self.avatar_size = 40
        
        # Try to load a font, fall back to default if not available
        try:
            self.font_regular = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
            self.font_bold = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", 16)
            self.font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        except:
            # Fallback to default font
            self.font_regular = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
    
    def generate_chat_screenshot(self, messages: List[Dict], sender_name: str, receiver_name: str) -> str:
        """Generate a screenshot of chat messages"""
        
        # Calculate image height
        header_height = 60
        total_height = header_height + (len(messages) * (self.message_height + 10)) + self.padding * 2
        
        # Create image
        img = Image.new('RGB', (self.width, total_height), color='#f5f5f5')
        draw = ImageDraw.Draw(img)
        
        # Draw header
        self._draw_header(draw, sender_name, receiver_name)
        
        # Draw messages
        y_offset = header_height + self.padding
        for message in messages:
            y_offset = self._draw_message(draw, message, y_offset, sender_name)
        
        # Save screenshot
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_screenshot_{timestamp}.png"
        screenshots_dir = os.path.join(os.getcwd(), "reports", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        filepath = os.path.join(screenshots_dir, filename)
        img.save(filepath)
        
        return filepath
    
    def _draw_header(self, draw: ImageDraw, sender_name: str, receiver_name: str):
        """Draw chat header"""
        # Background
        draw.rectangle([0, 0, self.width, 60], fill='#1976d2')
        
        # Title
        title = f"Chat: {sender_name} ↔ {receiver_name}"
        draw.text((self.padding, 20), title, fill='white', font=self.font_bold)
        
        # Timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((self.width - 200, 35), f"Generated: {timestamp}", fill='white', font=self.font_small)
    
    def _draw_message(self, draw: ImageDraw, message: Dict, y_offset: int, current_sender: str) -> int:
        """Draw a single message bubble"""
        
        is_sender = message['sender_name'] == current_sender
        is_abusive = message.get('is_abusive', False)
        
        # Message bubble dimensions
        bubble_width = 500
        bubble_height = self.message_height
        
        if is_sender:
            # Sender message (right side)
            bubble_x = self.width - bubble_width - self.padding
            bubble_color = '#e3f2fd' if not is_abusive else '#ffebee'
            text_color = '#1976d2' if not is_abusive else '#d32f2f'
        else:
            # Receiver message (left side)
            bubble_x = self.padding
            bubble_color = '#f5f5f5' if not is_abusive else '#ffebee'
            text_color = '#424242' if not is_abusive else '#d32f2f'
        
        # Draw message bubble
        draw.rounded_rectangle(
            [bubble_x, y_offset, bubble_x + bubble_width, y_offset + bubble_height],
            radius=15,
            fill=bubble_color,
            outline='#d32f2f' if is_abusive else '#e0e0e0',
            width=2 if is_abusive else 1
        )
        
        # Draw abuse warning if abusive
        if is_abusive:
            warning_y = y_offset + 5
            draw.text((bubble_x + 10, warning_y), "⚠️ ABUSIVE CONTENT DETECTED", 
                     fill='#d32f2f', font=self.font_small)
            
            # Draw abuse type and score
            abuse_info = f"Type: {message.get('abuse_type', 'UNKNOWN')} | Score: {message.get('abuse_score', 0)}/10"
            draw.text((bubble_x + 10, warning_y + 15), abuse_info, 
                     fill='#d32f2f', font=self.font_small)
            
            content_y = warning_y + 35
        else:
            content_y = y_offset + 10
        
        # Draw message content
        content = message['content']
        if len(content) > 60:
            content = content[:60] + "..."
        
        draw.text((bubble_x + 10, content_y), content, fill=text_color, font=self.font_regular)
        
        # Draw timestamp
        timestamp = datetime.datetime.fromisoformat(message['created_at'].replace('Z', '+00:00'))
        time_str = timestamp.strftime("%H:%M")
        draw.text((bubble_x + bubble_width - 50, y_offset + bubble_height - 20), 
                 time_str, fill='#757575', font=self.font_small)
        
        return y_offset + bubble_height + 10
    
    def generate_evidence_screenshot(self, abusive_messages: List[Dict], sender_name: str, receiver_name: str) -> str:
        """Generate a focused screenshot showing only abusive messages"""
        
        if not abusive_messages:
            return None
        
        # Filter and prepare messages for screenshot
        screenshot_messages = []
        for msg in abusive_messages:
            screenshot_messages.append({
                'sender_name': sender_name,
                'content': msg['content'],
                'created_at': msg['created_at'],
                'is_abusive': True,
                'abuse_type': msg.get('abuse_type', 'CYBERBULLYING'),
                'abuse_score': msg.get('abuse_score', 0)
            })
        
        return self.generate_chat_screenshot(screenshot_messages, sender_name, receiver_name)
