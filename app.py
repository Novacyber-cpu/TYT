import os
import json
import requests
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "kurumi_secret_key")

# Configure database
db_url = os.environ.get("DATABASE_URL")
if db_url is None:
    app.logger.error("DATABASE_URL environment variable is not set!")
    # Provide a default SQLite URI for development if DATABASE_URL is not available
    db_url = "sqlite:///kurumi.db"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Import models and create database tables
with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/quotes')
def get_quotes():
    try:
        from models import Quote
        
        # Check if we have quotes in the database
        db_quotes = Quote.query.all()
        
        # If no quotes in DB, load from file and populate DB
        if not db_quotes:
            app.logger.info("No quotes found in database, loading from JSON file")
            try:
                with open('static/data/quotes.json', 'r', encoding='utf-8') as f:
                    quotes_data = json.load(f)
                
                # Import quotes into database
                for quote_text in quotes_data:
                    # Extract author if present (format: "Quote text - Author")
                    if " – " in quote_text:
                        text, author = quote_text.split(" – ", 1)
                    else:
                        text, author = quote_text, None
                    
                    new_quote = Quote(text=text, author=author)
                    db.session.add(new_quote)
                
                db.session.commit()
                db_quotes = Quote.query.all()
            except Exception as e:
                app.logger.error(f"Error loading quotes from JSON: {e}")
        
        # Format quotes for JSON response
        quotes = []
        for quote in db_quotes:
            if quote.author:
                quotes.append(f"{quote.text} – {quote.author}")
            else:
                quotes.append(quote.text)
        
        return jsonify(quotes)
    except Exception as e:
        app.logger.error(f"Error retrieving quotes: {e}")
        return jsonify({"error": "Failed to load quotes"}), 500

@app.route('/api/links')
def get_links():
    try:
        from models import Link
        
        # Check if we have links in the database
        db_links = Link.query.all()
        
        # If no links in DB, load from file and populate DB
        if not db_links:
            app.logger.info("No links found in database, loading from JSON file")
            try:
                with open('static/data/links.json', 'r', encoding='utf-8') as f:
                    links_data = json.load(f)
                
                # Import links into database
                position = 0
                for category, category_links in links_data.items():
                    for link_data in category_links:
                        new_link = Link(
                            name=link_data["name"],
                            url=link_data["url"],
                            icon=link_data.get("icon", "fa-solid fa-link"),
                            category=category,
                            position=position
                        )
                        position += 1
                        db.session.add(new_link)
                
                db.session.commit()
                db_links = Link.query.all()
            except Exception as e:
                app.logger.error(f"Error loading links from JSON: {e}")
        
        # Format links for JSON response
        links_by_category = {}
        for link in db_links:
            if link.category not in links_by_category:
                links_by_category[link.category] = []
            
            links_by_category[link.category].append({
                "name": link.name,
                "url": link.url,
                "icon": link.icon
            })
        
        return jsonify(links_by_category)
    except Exception as e:
        app.logger.error(f"Error retrieving links: {e}")
        return jsonify({"error": "Failed to load links"}), 500

@app.route('/api/weather')
def get_weather():
    try:
        city = request.args.get('city', 'Tokyo')
        api_key = os.environ.get("WEATHER_API_KEY", "606feec03db68a693c464be01dec8bd8")
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        
        response = requests.get(url)
        weather_data = response.json()
        
        return jsonify(weather_data)
    except Exception as e:
        app.logger.error(f"Error fetching weather: {e}")
        return jsonify({"error": "Failed to fetch weather data"}), 500

@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    try:
        from models import UserPreference
        
        # Use browser fingerprint or IP as user_id (simplified for demo)
        user_id = request.headers.get('X-Forwarded-For') or request.remote_addr or "default_user"
        
        # Find or create user preferences
        user_prefs = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not user_prefs:
            # Create default preferences
            user_prefs = UserPreference(
                user_id=user_id,
                username="Tri-kun",
                background="default",
                custom_background_url=None,
                accent_color="#ff4d4d",
                default_city="Tokyo",
                character="kurumi",
                custom_greeting="Ara ara~ Ada yang bisa kubantu?",
                custom_phrases=json.dumps([
                    "Ufufu~ Apa yang sedang kamu cari?",
                    "Butuh bantuan? Kurumi di sini untukmu",
                    "Ara~ Sepertinya kamu sedang sibuk ya?"
                ]),
                background_music=None,
                character_voice="default"
            )
            db.session.add(user_prefs)
            db.session.commit()
        
        return jsonify(user_prefs.to_dict())
    except Exception as e:
        app.logger.error(f"Error retrieving preferences: {e}")
        return jsonify({"error": "Failed to load preferences"}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        file_type = request.args.get('type', 'background')
        allowed_types = {
            'background': ['jpg', 'jpeg', 'png', 'gif'],
            'audio': ['mp3', 'wav', 'ogg'],
            'character': ['png', 'gif']
        }
        
        # Check file extension
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_types.get(file_type, []):
            return jsonify({"error": f"File type not allowed. Allowed types: {', '.join(allowed_types.get(file_type, []))}"}), 400
        
        # Save file to appropriate folder
        folder = {
            'background': 'backgrounds',
            'audio': 'sounds',
            'character': 'characters'
        }.get(file_type, 'uploads')
        
        save_path = os.path.join('static', folder)
        os.makedirs(save_path, exist_ok=True)
        
        # Create a unique filename
        from datetime import datetime
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = os.path.join(save_path, unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Return the file URL
        file_url = f"/static/{folder}/{unique_filename}"
        return jsonify({"success": True, "fileUrl": file_url})
    except Exception as e:
        app.logger.error(f"Error uploading file: {e}")
        return jsonify({"error": "Failed to upload file"}), 500

@app.route('/api/preferences', methods=['POST'])
def save_preferences():
    try:
        from models import UserPreference
        
        # Get request data
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Use browser fingerprint or IP as user_id (simplified for demo)
        user_id = request.headers.get('X-Forwarded-For') or request.remote_addr or "default_user"
        
        # Find or create user preferences
        user_prefs = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not user_prefs:
            user_prefs = UserPreference(user_id=user_id)
            db.session.add(user_prefs)
        
        # Update fields from request data
        if 'username' in data:
            user_prefs.username = data['username']
        if 'background' in data:
            user_prefs.background = data['background']
        if 'customBackgroundUrl' in data:
            user_prefs.custom_background_url = data['customBackgroundUrl']
        if 'accentColor' in data:
            user_prefs.accent_color = data['accentColor']
        if 'city' in data:
            user_prefs.default_city = data['city']
        if 'character' in data:
            user_prefs.character = data['character']
        if 'customGreeting' in data:
            user_prefs.custom_greeting = data['customGreeting']
        if 'customPhrases' in data:
            user_prefs.custom_phrases = data['customPhrases']
        if 'backgroundMusic' in data:
            user_prefs.background_music = data['backgroundMusic']
        if 'characterVoice' in data:
            user_prefs.character_voice = data['characterVoice']
        
        db.session.commit()
        
        return jsonify({"success": True, "preferences": user_prefs.to_dict()})
    except Exception as e:
        app.logger.error(f"Error saving preferences: {e}")
        return jsonify({"error": "Failed to save preferences"}), 500
