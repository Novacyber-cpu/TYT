from app import db
from datetime import datetime

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Quote {self.id}: {self.text[:30]}...>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "author": self.author or "",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Link {self.id}: {self.name} ({self.category})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "icon": self.icon,
            "category": self.category,
            "position": self.position
        }

class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False)
    background = db.Column(db.String(50), default="default")
    custom_background_url = db.Column(db.String(255), nullable=True)
    accent_color = db.Column(db.String(20), default="#ff4d4d")
    default_city = db.Column(db.String(100), default="Tokyo")
    character = db.Column(db.String(50), default="kurumi")
    custom_greeting = db.Column(db.String(255), default="Ara ara~ Ada yang bisa kubantu?")
    custom_phrases = db.Column(db.Text, nullable=True) # JSON string of custom phrases
    background_music = db.Column(db.String(255), nullable=True)
    character_voice = db.Column(db.String(50), default="default")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserPreference {self.id}: {self.username}>"
    
    def to_dict(self):
        return {
            "username": self.username,
            "background": self.background,
            "customBackgroundUrl": self.custom_background_url,
            "accentColor": self.accent_color,
            "city": self.default_city,
            "character": self.character,
            "customGreeting": self.custom_greeting,
            "customPhrases": self.custom_phrases,
            "backgroundMusic": self.background_music,
            "characterVoice": self.character_voice
        }