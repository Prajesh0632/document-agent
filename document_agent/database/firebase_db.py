import firebase_admin
from firebase_admin import credentials, firestore
import json
from config import get_settings

settings = get_settings()
db = None 

def init_firebase():
    global db
    
    if settings.ENV.lower() == "production":
        # Production: Load from FIREBASE_KEY_JSON environment variable
        if not settings.FIREBASE_KEY_JSON:
            raise ValueError("FIREBASE_KEY_JSON environment variable is required in production mode")
        try:
            firebase_key_dict = json.loads(settings.FIREBASE_KEY_JSON)
            cred = credentials.Certificate(firebase_key_dict)
        except json.JSONDecodeError:
            raise ValueError("FIREBASE_KEY_JSON is not valid JSON")
    else:
        # Development: Load from file path
        cred = credentials.Certificate(settings.FIREBASE_KEY_PATH)
    
    firebase_admin.initialize_app(cred)
    db = firestore.client()

def get_db():
    return db