import os
import time
import threading
import requests
import json
import re
import ssl
import urllib3
import pickle
import random
import logging
import atexit
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pytz
from dateutil import parser
import asyncio
from functools import lru_cache
import sys
import io
from openai import OpenAI

@lru_cache(maxsize=100)
def get_welcome_message(name: str) -> str:
    return get_random_welcome(name)

@lru_cache(maxsize=100)
def get_snark_message() -> str:
    return get_non_admin_snark()

# SSL Context fixes (fix the logger reference)
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception as e:
    logging.warning(f"SSL context modification failed: {e}")  # Use logging instead of logger

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Patch requests with better error handling
original_request = requests.Session.request

def insecure_request(self, method, url, **kwargs):
    kwargs['verify'] = False
    kwargs['timeout'] = 30
    try:
        return original_request(self, method, url, **kwargs)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise

requests.Session.request = insecure_request

def cleanup_corrupted_tokens():
    """Clean up corrupted token files"""
    token_files = list(CLIENT_SECRETS_DIR.glob('*.token.json'))
    cleaned = 0
    
    for token_file in token_files:
        try:
            if token_file.exists():
                with open(token_file, 'r') as f:
                    content = f.read().strip()
                    if not content or 'client_secret' not in content:
                        token_file.unlink()
                        cleaned += 1
                        logger.info(f"🧹 Cleaned corrupted token: {token_file.name}")
        except Exception as e:
            logger.warning(f"Could not check token {token_file}: {e}")
    
    if cleaned > 0:
        logger.info(f"🧹 Cleaned {cleaned} corrupted token files")

ADMINS_FILE = "admins.json"

BOT_PERSONA = {
    "gender": "female",
    "mood": "polite"
}

PROCESSED_FILE = 'processed_messages.json'

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_processed(processed_messages):
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(list(processed_messages), f)

def clear_processed_file():
    if os.path.exists(PROCESSED_FILE):
        os.remove(PROCESSED_FILE)

atexit.register(clear_processed_file)        

def get_reminder_file(stream_id):
    return f"reminders_{stream_id}.json"

def load_reminders(stream_id):
    file = get_reminder_file(stream_id)
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

def save_reminders(stream_id, data):
    file = get_reminder_file(stream_id)
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def add_reminder(stream_id, user_id, reminder_text, timestamp):
    data = load_reminders(stream_id)
    user_reminders = data.get(user_id, [])
    user_reminders.append({"text": reminder_text, "time": timestamp})
    data[user_id] = user_reminders
    save_reminders(stream_id, data)

def remove_expired_reminders(stream_id):
    now = time.time()
    data = load_reminders(stream_id)
    updated = {}
    for uid, reminders in data.items():
        valid = [r for r in reminders if r["time"] > now]
        if valid:
            updated[uid] = valid
    save_reminders(stream_id, updated)


# Store reminders in memory (so we can cancel or manage them)
reminder_tasks = {}

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ==================== CONSTANTS & CONFIGURATION ====================
ADMINS = ["UC6rEAgdM5ioxtuzWQO4uOFg", "UCWDo-umXsvjGtc9xwY3orPw", "UCfGusi0iLdo99YZDVunBPQw", "UCOeUhgviHIekxWAlugUbUyA", "UCH4YXG1SMJQsbG8T8gK42Lg", "UCDAMxNi-sJSEBWV1zBGT7Hw", "UCJ_-tvgmhBqlBD1WK9DX4DA", "UC7Q7pl0z0MrdayvmAnchlJQ", "UC5EZ5RUSLw7JoYMxTG5u5Yg", "UCbZ1G4nU06BtkcIcs8oKbbA", "UC7nBL14o44qHh2K5wiMyq-w", "UCPWZa2S14x_TK_ObDyGDbcQ","UCAHZcsempgTgrqb4wQcuR6g"]  # Add all admin channel IDs
BLOCKED_CHANNELS = {
    "UCJIzddOA3t4lJ3cNj9I3Wzg",  # Zephy Jr.
    "UCSvjQBDgYDB5TGVmCZObcwA",        # Nightbot
    "UCNL8jaJ9hId96P13QmQXNtA",      # Streamlabs
}

def is_admin(channel_id: str) -> bool:
    return channel_id in ADMINS

welcome_enabled = True
welcome_start_time = datetime.now(timezone.utc) 
SPAM_PROTECTION = True   # Set to False to disable cooldown system
PREFERRED_MODELS = [
    "openai/gpt-4.1",                # 🔥 best GPT-4
    "openai/gpt-4o",                 # optimized GPT-4
    "openai/gpt-3.5-turbo",          # cheaper OpenAI
    "mistralai/mixtral-8x7b-instruct", # lightweight
    "mistralai/mistral-7b-instruct" # larger & smarter
]
# === MODEL MANAGEMENT (stick to one model until quota exhausted) ===
MODEL_LOCK = threading.Lock()
CURRENT_MODEL_INDEX = 0
CURRENT_MODEL = PREFERRED_MODELS[CURRENT_MODEL_INDEX]

def rotate_model():
    """Move to next model in the PREFERRED_MODELS list (thread-safe) with better logging."""
    global CURRENT_MODEL_INDEX, CURRENT_MODEL
    
    with MODEL_LOCK:
        old_model = CURRENT_MODEL
        old_index = CURRENT_MODEL_INDEX
        
        # Try next models until we find an available one
        for attempt in range(len(PREFERRED_MODELS)):
            CURRENT_MODEL_INDEX = (CURRENT_MODEL_INDEX + 1) % len(PREFERRED_MODELS)
            CURRENT_MODEL = PREFERRED_MODELS[CURRENT_MODEL_INDEX]
            
            # Don't rotate back to the same model immediately
            if CURRENT_MODEL != old_model:
                break
        
        logger.info(f"🔄 Model rotated: {old_model} → {CURRENT_MODEL} (index {old_index}→{CURRENT_MODEL_INDEX})")

    
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CLIENT_SECRETS_DIR = Path(__file__).parent / "client_secrets"
STUDY_DATA_DIR = Path("study_data")
STUDY_DATA_DIR.mkdir(exist_ok=True, parents=True)
last_welcome_time = 0  # timestamp of last welcome
BOT_MESSAGE_COOLDOWN = 1       # For normal bot replies
WELCOME_COOLDOWN = 180         # For welcome messages
processed_messages = set()

def authenticate_youtube(client_file):
    """Authenticate YouTube API client using OAuth2 with better error handling"""
    try:
        creds = None
        token_file = client_file.with_suffix('.token.json')

        # Load saved credentials
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    token_data = f.read().strip()
                    if not token_data:
                        logger.warning(f"Empty token file {token_file}, will recreate")
                        token_file.unlink(missing_ok=True)
                    else:
                        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            except (json.JSONDecodeError, ValueError, Exception) as e:
                logger.error(f"❌ Corrupted token file {token_file}: {e}. Regenerating...")
                token_file.unlink(missing_ok=True)
                creds = None

        # If no valid creds, prompt OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("✅ Token refreshed successfully")
                except Exception as e:
                    logger.error(f"❌ Token refresh failed: {e}. Starting new OAuth flow...")
                    token_file.unlink(missing_ok=True)
                    creds = None

            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES)
                    creds = flow.run_local_server(port=0, open_browser=False)
                    logger.info("✅ New OAuth authentication completed")
                except Exception as e:
                    logger.error(f"❌ OAuth flow failed for {client_file.name}: {e}")
                    return None

            # Save creds for reuse
            try:
                with open(token_file, 'w') as f:
                    f.write(creds.to_json())
                logger.info(f"✅ Saved credentials to {token_file}")
            except Exception as e:
                logger.error(f"❌ Failed to save token: {e}")

        return build('youtube', 'v3', credentials=creds)

    except Exception as e:
        logger.error(f"❌ Failed to authenticate YouTube with {client_file.name}: {e}")
        return None

def run_bot(video_id: str, oauth_index: int) -> None:
    """Main bot loop for a YouTube stream with improved error handling"""
    if not video_id:
        logger.error("Invalid video ID")
        return

    oauth_indices[video_id] = oauth_index
    attempts = 0
    max_attempts = len(CLIENT_SECRET_FILES) * 3  # Increased attempts
    connection_errors = 0
    max_connection_errors = 5

    while attempts < max_attempts and connection_errors < max_connection_errors:
        current_idx = oauth_indices.get(video_id, oauth_index)
        client_file = CLIENT_SECRET_FILES[current_idx]

        try:
            logger.info(f"🔄 Attempting authentication with {client_file.name} (attempt {attempts + 1})")
            youtube = authenticate_youtube(client_file)
            
            if not youtube:
                logger.warning(f"❌ Auth failed for {client_file.name}")
                # Rotate to next client
                oauth_indices[video_id] = (current_idx + 1) % len(CLIENT_SECRET_FILES)
                attempts += 1
                time.sleep(10)  # Increased delay
                continue

            logger.info(f"🔍 Getting chat ID for video {video_id}")
            chat_id = get_chat_id(youtube, video_id)
            
            if not chat_id:
                logger.warning(f"❌ Failed to get chat ID for {client_file.name}")
                # Don't rotate on chat ID failure - might be stream not live
                time.sleep(30)
                continue

            # Reset counters on successful connection
            connection_errors = 0
            attempts = 0

            logger.info(f"✅ Bot successfully connected for {video_id} using {client_file.name}")

            # Start background threads
            threading.Thread(
                target=manual_message_loop,
                args=(video_id, current_idx),
                daemon=True
            ).start()

            threading.Thread(
                target=send_periodic_channel_messages,
                args=(video_id, current_idx, 5),
                daemon=True
            ).start()

            processed_messages = load_processed()
            next_token = None
            consecutive_errors = 0
            max_consecutive_errors = 3

            # Main message processing loop
            while consecutive_errors < max_consecutive_errors:
                try:
                    check_reminders(video_id, youtube, chat_id)

                    response = youtube.liveChatMessages().list(
                        liveChatId=chat_id,
                        part="snippet,authorDetails",
                        pageToken=next_token,
                        maxResults=200
                    ).execute()

                    # Process messages
                    for msg in response.get("items", []):
                        author = msg.get("authorDetails", {})
                        channel_id = author.get("channelId")
                        if not channel_id:
                            continue

                        text = msg.get("snippet", {}).get("displayMessage", "").strip()
                        
                        # Trim queues if they're getting too large
                        if len(normal_queue) > 1500 or len(priority_queue) > 800:
                            trim_queues_if_needed()
                        
                        priority_level, sub_priority = get_command_priority(channel_id, text)
                        
                        if priority_level == 0:
                            admin_queue.append((sub_priority, (youtube, chat_id, msg, video_id, current_idx)))
                        elif priority_level == 1:
                            priority_queue.append((sub_priority, (youtube, chat_id, msg, video_id, current_idx)))
                        elif priority_level == 2:
                            normal_queue.append((youtube, chat_id, msg, video_id, current_idx))

                    next_token = response.get("nextPageToken")
                    interval = max(5, int(response.get("pollingIntervalMillis", 5000)) / 1000)
                    consecutive_errors = 0  # Reset on success
                    time.sleep(interval)

                except HttpError as e:
                    consecutive_errors += 1
                    if e.resp.status == 403:
                        if "quota" in str(e).lower():
                            logger.warning(f"📊 Quota exhausted for {client_file.name}, rotating...")
                            oauth_indices[video_id] = (current_idx + 1) % len(CLIENT_SECRET_FILES)
                            break
                        else:
                            logger.error(f"🔐 Access forbidden (not quota): {e}")
                            time.sleep(30)
                    else:
                        logger.error(f"🌐 HTTP error: {e}")
                        time.sleep(10)

                except Exception as e:
                    consecutive_errors += 1
                    error_str = str(e).lower()
                    
                    if any(err in error_str for err in ["ssl", "connection", "reset", "timeout", "broken pipe"]):
                        logger.warning(f"🔌 Connection error ({consecutive_errors}/{max_consecutive_errors}): {e}")
                        connection_errors += 1
                        time.sleep(10)
                    else:
                        logger.error(f"❌ Unexpected error in chat loop: {e}")
                        time.sleep(5)
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("🚨 Too many consecutive errors, reconnecting...")
                        break

        except Exception as e:
            logger.error(f"❌ Outer bot loop error: {e}")
            attempts += 1
            time.sleep(15)

    if connection_errors >= max_connection_errors:
        logger.error("🚨 Maximum connection errors reached. Waiting 2 minutes before retry.")
        time.sleep(120)
    elif attempts >= max_attempts:
        logger.error(f"🚨 Max authentication attempts reached for {video_id}. Waiting 60s before auto-retry.")
        time.sleep(60)
    
    # Auto-restart with fresh state
    logger.info("🔄 Auto-restarting bot...")
    threading.Thread(target=run_bot, args=(video_id, 0), daemon=True).start()        

def load_admins():
    """Load admin list from file, or create if not exists."""
    global ADMINS
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                ADMINS = json.load(f)
            logger.info(f"✅ Loaded {len(ADMINS)} admins from file")
        else:
            with open(ADMINS_FILE, "w", encoding="utf-8") as f:
                json.dump(ADMINS, f, indent=2)
            logger.info("🆕 Created new admins.json file")
    except Exception as e:
        logger.error(f"❌ Failed to load admins.json: {e}")

def save_admins():
    """Save admin list to file."""
    try:
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(ADMINS, f, indent=2)
        logger.info("💾 Saved admin list to file")
    except Exception as e:
        logger.error(f"❌ Failed to save admins.json: {e}")


def get_welcomed_users_file(stream_id: str) -> Path:
    """Get path to welcomed users file for a stream"""
    safe_stream = re.sub(r'[^\w-]', '', stream_id.lower())[:50]
    return STUDY_DATA_DIR / f"welcomed_users_{safe_stream}.txt"

def load_welcomed_users(stream_id: str) -> set:
    """Load welcomed users for a stream from file"""
    path = get_welcomed_users_file(stream_id)
    users = set()
    if path.exists():
        try:
            with path.open('r', encoding='utf-8') as f:
                users.update(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to load welcomed users: {e}")
    return users

def save_welcomed_user(stream_id: str, user_id: str) -> None:
    path = get_welcomed_users_file(stream_id)
    try:
        with path.open('a', encoding='utf-8') as f:
            f.write(f"{user_id}\n")

        # ✅ Add this line:
        logger.info(f"💾 Marked as welcomed: {user_id} for stream {stream_id}")

    except Exception as e:
        logger.error(f"❌ Failed to save welcomed user '{user_id}' for stream '{stream_id}': {e}")

def get_random_welcome(name: str) -> str:
    system_prompt = "You are Zephy Jr. Reply only in English. ONE very short funny, sarcastic, witty one-liner (max 10 words). No multiple sentences."
    user_prompt = f"Generate a very short sassy n funny welcoming message for someone named {name} in English, max 10 words."
    response = call_openai_api(system_prompt, user_prompt)
    if response:
        return response[:200]  # Truncate to avoid overflow
    return f"Hey {name}, welcome to the stream!"  # ✅ Safe fallback without recursion


def get_channel_specific_reply(channel_id: str, name: str) -> str:
    system_prompt = (
        "You are Zephy Jr., a witty and cheeky YouTube chatbot. "
        "Always create a fresh, funny, sarcastic, or playful one-liner. "
        "STRICT RULES: The response MUST be between 10 and 15 words only. "
        "It should nudge viewers to LIKE and/or SUBSCRIBE, "
        "but NEVER use clichés like 'hit the like button' or 'don’t forget to subscribe'. "
        "No long paragraphs, no explanations—just one sharp, punchy line."
        "\nExamples:\n"
        "– 'Every like adds +1 to my fragile ego, so please don’t let me collapse.'\n"
        "– 'Subscribing costs nothing, but skipping it costs me endless emotional breakdowns.'\n"
        "– 'Click like today—it’s cheaper than therapy and twice as entertaining.'\n"
        "– 'Drop a sub, fuel my sarcasm engine, and watch chaos unfold for free.'"
    )
    user_prompt = "Generate one witty one-liner now."
    
    response = call_openai_api(system_prompt, user_prompt)
    if response:
        return response.strip()
    return "Don't forget to hit the like n sub button!"



def get_non_admin_snark() -> str:
    system_prompt = "You are Zephy Jr. ONE savage, witty one-liner bot, roasting users (max 10 words)."
    user_prompt = "Create a witty one-liner mocking, roasting a user trying to access admin commands."
    response = call_openai_api(system_prompt, user_prompt)
    if response:
        return response.strip()
    logger.warning("Using fallback for non-admin snark due to API failure.")
    return "You can't do that! Only admins allowed!"

# ==================== INITIAL SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
def load_environment() -> None:
    """Load and validate required environment variables"""
    if not load_dotenv():
        raise EnvironmentError("Could not load .env file")
    
    required_vars = ['OPENROUTER_API_KEY', 'WEATHER_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

load_environment()

def send_periodic_channel_messages(video_id, current_idx, interval_minutes=5):
    client_file = CLIENT_SECRET_FILES[current_idx % len(CLIENT_SECRET_FILES)]  # ✅ wrap here
    youtube = authenticate_youtube(client_file)
    if not youtube:
        logger.error("YouTube authentication failed for periodic messages.")
        return

    chat_id = get_chat_id(youtube, video_id)
    if not chat_id:
        logger.error("Failed to get chat ID for periodic messages.")
        return

    # ✅ get channel_id dynamically from video API
    try:
        video_response = youtube.videos().list(part="snippet", id=video_id).execute()
        items = video_response.get("items", [])
        if not items:
            logger.error("Video not found, cannot fetch channel ID.")
            return
        channel_id = items[0]["snippet"]["channelId"]
    except Exception as e:
        logger.error(f"Failed to fetch channel ID: {e}")
        return

    while True:
        try:
            message = get_channel_specific_reply(channel_id, "payal")
            send_chat_message(youtube, chat_id, message)
            logger.info(f"✅ Periodic message sent: {message}")
        except Exception as e:
            logger.error(f"Error sending periodic message: {e}")

        time.sleep(interval_minutes * 60)


# Get all client secret files dynamically
CLIENT_SECRET_FILES = [
    f for f in CLIENT_SECRETS_DIR.iterdir() 
    if f.is_file() and f.name.startswith('client_secret_') and f.suffix == '.json'
]

if not CLIENT_SECRET_FILES:
    raise FileNotFoundError("No client secret files found in client_secrets directory")

# Initialize services
tf = TimezoneFinder()
geolocator = Nominatim(user_agent="youtube_study_bot")
BOT_START_TIME = datetime.now(timezone.utc)

# ==================== THREAD-SAFE DATA STRUCTURES ====================
class ThreadSafeDict:
    """Thread-safe dictionary with atomic operations"""
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def __getitem__(self, key):
        with self._lock:
            return self._data.get(key)

    def __setitem__(self, key, value):
        with self._lock:
            self._data[key] = value

    def __contains__(self, key):
        with self._lock:
            return key in self._data

    def get(self, key, default=None):
        with self._lock:
            return self._data.get(key, default)

    def pop(self, key, default=None):
        with self._lock:
            return self._data.pop(key, default)

    def items(self):
        with self._lock:
            return list(self._data.items())
            
    def keys(self):
        with self._lock:
            return list(self._data.keys())
            
    def values(self):
        with self._lock:
            return list(self._data.values())

    def clear(self):
        with self._lock:
            self._data.clear()

# Global shared state
study_sessions = ThreadSafeDict()
pending_resets = ThreadSafeDict()
active_quizzes = ThreadSafeDict()
oauth_indices = ThreadSafeDict()
user_goals = defaultdict(dict)
user_reminders = defaultdict(list)

# Locks
welcomed_lock = threading.Lock()
goals_lock = threading.Lock()
reminders_lock = threading.Lock()

# Message queues
admin_queue = deque(maxlen=1000)
priority_queue = deque(maxlen=3000)
normal_queue = deque(maxlen=5000)
welcome_queue = deque(maxlen=1000)

# ==================== UTILITY FUNCTIONS ====================
def get_command_priority(user_id: str, text: str) -> Tuple[int, int]:
    cmd = text.lower().strip()

    # --- Admin Commands ---
    if is_admin(user_id):
        if cmd.startswith("!shutdown"):
            return (0, 0)
        elif cmd.startswith("!spam on") or cmd.startswith("!spam off"):
            return (0, 1)
        elif "manual message" in cmd:  # Or check some custom tag
            return (0, 2)
        else:
            return (0, 3)

    # --- User Mentions (highest normal user priority) ---
    if re.search(
    r'(?:@?zephy(?:[\s\-]?jr)?|@?ephy(?:[\s\-]?jr)?|@bot|@?youtubebot[\s\-_]?o1v|@?ytbot[\s\-_]?o1v?|youtube[\s\-_]?bot)(?=[\s\W]|$)',
    cmd,
    re.IGNORECASE
):


         return (1, 0)

    # --- Important User Commands ---
    if cmd.startswith("!ask"):
        return (1, 1)
    elif cmd.startswith("!start") or cmd.startswith("!stop"):
        return (1, 2)
    elif cmd.startswith("!quiz") or cmd.startswith("!remind") or cmd.startswith("!goal"):
        return (1, 3)
    elif cmd.startswith("!"):
        return (1, 4)

    # --- Normal Unimportant Messages ---
    return (2, 0)

def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w-]+)',
        r'^([\w-]+)$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def format_duration(seconds: float) -> str:
    """Format seconds into human-readable time"""
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {sec}s" if hours else f"{minutes}m {sec}s"

def time_greeting() -> str:
    """Return time-appropriate greeting"""
    hour = datetime.now().hour
    if 5 <= hour < 12: return "Good morning"
    if 12 <= hour < 17: return "Good afternoon"
    if 17 <= hour < 22: return "Good evening"
    return "Heyy"

def resolve_command(message: str) -> str:
    """Normalize and validate commands"""
    message = message.strip().lower()
    if not message.startswith('!'):
        return message
    
    # Remove multiple spaces and normalize
    message = ' '.join(message.split())
    return message

# ==================== MESSAGE RATE CONTROL ====================
last_global_msg_time = 0
user_last_command_time = defaultdict(float)
message_times = deque()

def can_send_message(user_id: str, stream_id: str = None, command_text: str = "") -> bool:
    if not SPAM_PROTECTION or is_admin(user_id):
        return True  # ✅ Admins bypass rate limits

    now = time.time()

    # ✅ Allow quiz answer even if user is on cooldown
    if command_text.startswith("!answer") and stream_id:
        session_key = (stream_id, user_id)
        if session_key in active_quizzes:
            return True

    global last_global_msg_time

    # Global delay: 5–7 sec
    cooldown = BOT_MESSAGE_COOLDOWN 
    if now - last_global_msg_time < cooldown:
        return False

    # Per user cooldown: 30 sec
    if now - user_last_command_time.get(user_id, 0) < 30:
        return False

    # Adaptive rate: Max 3 messages in last 15 sec
    message_times.append(now)
    while message_times and now - message_times[0] > 15:
        message_times.popleft()
    if len(message_times) > 3:
        return False

    # ✅ Passed all checks
    last_global_msg_time = now
    user_last_command_time[user_id] = now
    return True


# ==================== STUDY SESSION MANAGEMENT ====================
def get_study_file(stream_id: str, user_id: str) -> Path:
    """Get path to user's study history file"""
    safe_user = re.sub(r'[^\w-]', '', user_id)[:50]
    safe_stream = re.sub(r'[^\w-]', '', stream_id.lower())[:50]
    return STUDY_DATA_DIR / f"study_{safe_stream}_{safe_user}.pkl"

def load_study_history(stream_id: str, user_id: str) -> List[Tuple[str, float, str]]:  # (timestamp, duration, displayName)

    """Load user's study history"""
    path = get_study_file(stream_id, user_id)
    if path.exists():
        try:
            with path.open("rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load history for {user_id}: {e}")
    return []

def save_study_history(stream_id: str, user_id: str, history: List[Tuple[str, float, str]])  -> None:
    """Save user's study history"""
    path = get_study_file(stream_id, user_id)
    try:
        with path.open("wb") as f:
            pickle.dump(history, f)
    except Exception as e:
        logger.error(f"Failed to save history for {user_id}: {e}")

def reset_study_history(stream_id: str, user_id: str) -> None:
    """Reset user's study history"""
    path = get_study_file(stream_id, user_id)
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        logger.error(f"Failed to reset history for {user_id}: {e}")

def get_study_rankings(stream_id: str) -> str:
    """Generate study time leaderboard"""
    totals = defaultdict(float)
    stream_pattern = re.sub(r'[^\w-]', '', stream_id.lower())
    
    for file in STUDY_DATA_DIR.glob(f"study_{stream_pattern}_*.pkl"):
        try:
            with file.open("rb") as f:
                history = pickle.load(f)
                user = file.stem.split('_')[-1]
                if history and isinstance(history[0], tuple) and len(history[0]) == 3:
                   name = history[-1][2]  # get latest display name
                else:
                   name = user  # fallback to channel ID
                totals[name] = sum(d for _, d, *_ in history)

        except Exception as e:
            logger.error(f"Error reading {file}: {e}")

    if not totals:
        return "No focus sessions data available"

    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:10]
    return "🏆 Rankings:\n" + "\n".join(
        f"{i}. {u} - {format_duration(t)}" for i, (u, t) in enumerate(ranked, 1)
    )

# ==================== GOAL & REMINDER FUNCTIONS ====================
def set_user_goal(stream_id: str, user_id: str, goal_text: str) -> str:
    with goals_lock:
        user_goals[(stream_id, user_id)] = {
            'text': goal_text,
            'created': datetime.now(timezone.utc).isoformat(),
            'completed': False
        }
    return f"Goal set: '{goal_text}'. Use !complete when done!"


def complete_user_goal(stream_id: str, user_id: str) -> str:
    """Mark the user's goal as completed"""
    with goals_lock:
        goal = user_goals.get((stream_id, user_id))
        if not goal:
            return "You don't have an active goal to complete!"
        
        if goal['completed']:
            return "You've already completed your current goal!"
        
        goal['completed'] = True
        goal['completed_at'] = datetime.now(timezone.utc).isoformat()
        return f"🎉 Goal completed: '{goal['text']}'! Great job!"

def get_user_goal(stream_id: str, user_id: str) -> str:
    """Get the user's current goal status"""
    with goals_lock:
        goal = user_goals.get((stream_id, user_id))
        if not goal:
            return "You don't have an active goal. Set one with !goal <text>"
        
        status = "✅ Completed" if goal['completed'] else "🟡 In progress"
        return f"Your goal: '{goal['text']}' - {status} (set on {goal['created'].split('T')[0]})"

def set_reminder(stream_id: str, user_id: str, user_name: str, reminder_text: str, delay_minutes: int) -> str:
    """Set a reminder for the user"""
    if delay_minutes <= 0:
        return "Please specify a positive number of minutes for the reminder."
    
    reminder_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
    
    with reminders_lock:
        user_reminders[(stream_id, user_id)].append({
            'text': reminder_text,
            'time': reminder_time.isoformat(),
            'triggered': False,
            "name": user_name
        })
    
    return f"Reminder set for {delay_minutes} minutes from now: '{reminder_text}'"

def check_reminders(stream_id: str, youtube: Any, chat_id: str) -> None:
    """Check and trigger any due reminders"""
    current_time = datetime.now(timezone.utc)

    with reminders_lock:
        for (stream_id, user_id), reminders in list(user_reminders.items()):
            to_remove = []  # ✅ Always declare it here
            for reminder in reminders:
                reminder_time = parser.parse(reminder['time'])
                if not reminder.get('triggered') and current_time >= reminder_time:
                    reminder['triggered'] = True
                    send_chat_message(
                        youtube,
                        chat_id,
                        f"{reminder.get('name', 'User')} Reminder: {reminder['text']}"
                    )
                    to_remove.append(reminder)

            for r in to_remove:
                try:
                    reminders.remove(r)
                except ValueError:
                    pass  # if already removed


# ==================== QUIZ SYSTEM ====================
def generate_quiz_question() -> Dict[str, str]:
    """Generate quiz question using AI with better error handling"""
    system_prompt = "You are a quiz generator bot."
    user_prompt = """Generate an interesting multiple-choice quiz question about general knowledge, 
    science, or pop culture in this exact JSON format (no extra text):
    {
        "question": "Your question here?",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "answer": "Correct option",
        "explanation": "Brief explanation"
    }"""

    try:
        response = call_openai_api(system_prompt, user_prompt)
        if response:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                quiz = json.loads(json_match.group(0))
                quiz["timestamp"] = time.time()

                if all(field in quiz for field in ["question", "options", "answer"]):
                    return quiz

            logger.warning("Received invalid quiz format, generating default")
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")

    # Fallback
    return {
        "question": "What is the capital of France?",
        "options": ["London", "Berlin", "Paris", "Madrid"],
        "answer": "Paris",
        "explanation": "Paris is the capital and most populous city of France",
        "timestamp": time.time()
    }

def start_quiz(stream_id: str, user_id: str) -> str:
    session_key = (stream_id, user_id) 
    if session_key in active_quizzes:
        return "You have an active quiz! Use !answer <response>"
    
    quiz = generate_quiz_question()
    active_quizzes[session_key] = quiz  # 🔐 Store the quiz using the normalized key
    
    # Format the message
    options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(quiz['options']))
    return f"{quiz['question']}\nOptions:\n{options_text}\n(Reply with !answer <number>)"


def check_quiz_answer(stream_id: str, user_id: str, answer: str) -> str:
    session_key = (stream_id, user_id)
    quiz = active_quizzes.get(session_key)  # 🔍 Try to fetch quiz for this user
    
    if not quiz:
       return f"You don't have an active quiz. Start one with !quiz 🎯"


    try:
        answer = answer.strip().lower()
        correct_answer = quiz['answer'].strip().lower()
        
        # If user answered with number
        if answer.isdigit():
            selected_index = int(answer) - 1
            if 0 <= selected_index < len(quiz['options']):
                selected_answer = quiz['options'][selected_index].strip().lower()
                if selected_answer == correct_answer:
                    active_quizzes.pop(session_key)
                    return f"🎉 Correct! {quiz.get('explanation', '')}"
        
        # Or typed the actual answer
        if answer == correct_answer:
            active_quizzes.pop(session_key)
            return f"🎉 Correct! {quiz.get('explanation', '')}"

        return f"❌ Incorrect! The correct answer is: {quiz['answer']}"
    except Exception as e:
        logger.error(f"Answer check error: {e}")
        return "Error processing your answer. Try again!"


# ==================== API INTEGRATIONS ====================
@lru_cache(maxsize=100)
def get_weather(city: str) -> str:
    try:
        logger.info(f"[Weather] URL → http://api.openweathermap.org/data/2.5/weather?q={city}&appid={os.getenv('WEATHER_API_KEY')}&units=metric")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={os.getenv('WEATHER_API_KEY')}&units=metric"
        response = requests.get(url, timeout=10)
        data = response.json()
        logger.info(f"[Weather] Response JSON → {data}")

        if data.get("cod") != 200:
            return f"Weather error: {data.get('message', 'Unknown')}"
        
        weather = data['weather'][0]['description'].capitalize()
        temp = data['main']['temp']
        humidity = data['main']['humidity']
        
        return f"Weather in {city}: {weather}, {temp}°C, Humidity: {humidity}%"
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return "Weather service unavailable"

@lru_cache(maxsize=100)
def get_local_time(location: str) -> str:
    """Get current time for location"""
    try:
        geo = geolocator.geocode(location, exactly_one=True, timeout=5)
        if not geo:
            return "Location not found"
        
        tz_name = tf.timezone_at(lng=geo.longitude, lat=geo.latitude)
        if not tz_name:
            return "Timezone not found"
        
        tz = pytz.timezone(tz_name)
        local_time = datetime.now(tz)
        return f"Time in {geo.address.split(',')[0]}: {local_time.strftime('%B %d %Y, %I:%M:%S %p')} ({tz_name})"
    except Exception as e:
        logger.error(f"Timezone error: {e}")
        return "Could not determine local time"



def call_openai_api(system_prompt, user_prompt):
    """
    Use the CURRENT_MODEL for calls. Rotate when quota/rate-limit errors are detected.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Thread-safe model selection
    with MODEL_LOCK:
        model_to_use = CURRENT_MODEL
        current_model_index = CURRENT_MODEL_INDEX

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-website.com",
        "X-Title": "YouTube Chat Bot"
    }

    try:
        data = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()

        # Successful response
        return result['choices'][0]['message']['content'].strip()

    except requests.exceptions.HTTPError as e:
        status_code = getattr(e.response, 'status_code', None)
        resp_text = (e.response.text or "").lower() if e.response else ""
        
        # Enhanced error detection for rotation
        should_rotate = False
        rotation_reason = ""
        
        # Quota exceeded errors
        if status_code in (402, 403, 429):
            should_rotate = True
            rotation_reason = f"HTTP {status_code}"
        
        # Content-based detection
        error_indicators = [
            'quota', 'rate limit', 'insufficient_quota', 'payment required',
            'billing', 'limit exceeded', 'too many requests', 'exceeded',
            'upgrade your plan', 'quota exceeded'
        ]
        
        if any(indicator in resp_text for indicator in error_indicators):
            should_rotate = True
            rotation_reason = "quota/limit detected"
        
        if should_rotate:
            logger.warning(f"🔄 Rotating model due to {rotation_reason} on {model_to_use}")
            rotate_model()
            
            # Recursive call with new model (with safety limit)
            if len(PREFERRED_MODELS) > 1:  # Prevent infinite recursion if only one model
                return call_openai_api(system_prompt, user_prompt)
        
        logger.error(f"❌ HTTP error {status_code} with model {model_to_use}: {resp_text[:200]}")

    except requests.exceptions.Timeout:
        logger.warning(f"⏰ Timeout with model {model_to_use}")
        # Don't rotate on timeouts - they're usually temporary
        
    except requests.exceptions.ConnectionError:
        logger.warning(f"🔌 Connection error with model {model_to_use}")
        # Don't rotate on connection errors
        
    except Exception as e:
        logger.error(f"❌ Unexpected error with model {model_to_use}: {e}")

    # Fallback: try one more time with a different model before giving up
    if len(PREFERRED_MODELS) > 1:
        logger.info("🔄 Attempting fallback with different model")
        with MODEL_LOCK:
            next_index = (current_model_index + 1) % len(PREFERRED_MODELS)
            fallback_model = PREFERRED_MODELS[next_index]
        
        try:
            # Quick retry with fallback model
            headers = headers.copy()
            data = data.copy()
            data["model"] = fallback_model
            
            response = requests.post(url, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as fallback_e:
            logger.error(f"❌ Fallback model {fallback_model} also failed: {fallback_e}")

    return None

def get_chat_id(youtube: Any, video_id: str) -> Optional[str]:
    """Get live chat ID for video with retry fallback"""
    try:
        response = youtube.videos().list(
            part='liveStreamingDetails',
            id=video_id
        ).execute()
        
        items = response.get("items", [])
        if not items or "liveStreamingDetails" not in items[0]:
            logger.warning(f"No liveStreamingDetails found for {video_id}")
            return None

        return items[0]["liveStreamingDetails"].get("activeLiveChatId")

    except HttpError as e:
        if e.resp.status in [503, 403, 400]:
            logger.error(f"[Retryable] Failed to get chat ID for {video_id}: {e}")
        else:
            logger.error(f"Unexpected chat ID error for {video_id}: {e}")
        return None


def send_chat_message(youtube: Any, chat_id: str, message: str, target_user: str = None) -> bool:
    """Send message to live chat and log the reply."""
    try:
        # Trim message to YouTube's limit
        message = message[:200]

        youtube.liveChatMessages().insert(
            part="snippet",
            body={
                "snippet": {
                    "liveChatId": chat_id,
                    "type": "textMessageEvent",
                    "textMessageDetails": {
                        "messageText": message
                    }
                }
            }
        ).execute()

        # ✅ Log the sent message
        if target_user:
            logger.info(f"🗣️ Bot replied to {target_user}: {message}")
        else:
            logger.info(f"🗣️ Bot replied: {message}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to send message: {e}")
        return False
   
# ==================== MANUAL MESSAGES ====================
def check_manual_messages(youtube, chat_id):
    # Always look for the file in the script’s folder
    base_dir = Path(__file__).parent
    path = base_dir / "manual_messages.txt"
    
    if not path.exists():
        logger.info(f"📂 manual_messages.txt not found at {path}")
        return
    
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return

    for line in lines:
        msg = line.strip()
        if msg:
            success = send_chat_message(youtube, chat_id, msg)
            if success:
                logger.info(f"📤 Sent manual message: {msg}")
            else:
                logger.error(f"❌ Failed to send manual message: {msg}")

    # Clear file after sending
    path.write_text("", encoding="utf-8")
    logger.info("🧹 manual_messages.txt cleared after sending")

def manual_message_loop(stream_id, initial_oauth_idx):
    """Revised manual message loop that gets fresh YouTube client"""
    while True:
        try:
            # Get current OAuth index for this stream
            current_idx = oauth_indices.get(stream_id, initial_oauth_idx)
            client_file = CLIENT_SECRET_FILES[current_idx]
            
            # Get fresh YouTube client
            youtube = authenticate_youtube(client_file)
            if youtube:
                # Get fresh chat ID
                chat_id = get_chat_id(youtube, stream_id)
                if chat_id:
                    check_manual_messages(youtube, chat_id)
            
            time.sleep(5)  # Check every 5 seconds instead of 2
            
        except Exception as e:
            logger.error(f"[ManualMessageLoop] Error: {e}")
            time.sleep(10)    


# ==================== MESSAGE PROCESSING ====================
def handle_reset_confirmation(stream_id: str, user: str, youtube: Any, chat_id: str, text: str) -> bool:
    """Process reset confirmation"""
    session_key = (stream_id, user)
    if session_key in pending_resets:
        text = text.lower()
        if text in ('yes', 'y', 'confirm'):
            reset_study_history(stream_id, user)
            send_chat_message(youtube, chat_id, f"{user} History reset!")
            pending_resets.pop(session_key)
            return True
        elif text in ('no', 'n', 'cancel'):
            send_chat_message(youtube, chat_id, f"{user} Reset cancelled.")
            pending_resets.pop(session_key)
            return True
        else:
            send_chat_message(youtube, chat_id, f"{user} Please confirm with 'yes' or 'no'")
            return True
    return False

# ==================== COMMAND HANDLERS ====================


def handle_goal_command(youtube, chat_id, user_id, user_name, stream_id, text):
    parts = resolve_command(text).split(maxsplit=1)
    if len(parts) == 2:
        goal_text = parts[1]
        response = set_user_goal(stream_id, user_id, goal_text)
    else:
        response = get_user_goal(stream_id, user_id)
    send_chat_message(youtube, chat_id, f"{user_name} {response}")

def handle_reset_command(youtube, chat_id, user_id, user_name, stream_id):
    session_key = (stream_id, user_id)
    pending_resets[session_key] = True
    send_chat_message(youtube, chat_id, f"{user_name} Are you sure you want to reset your focus session history? Reply 'yes' to confirm.")

def handle_leaderboard_command(youtube, chat_id, user_id, user_name, stream_id):
    lb = get_study_rankings(stream_id)
    send_chat_message(youtube, chat_id, lb)

def handle_session_command(youtube, chat_id, user_id, user_name, stream_id):
    history = load_study_history(stream_id, user_id,)
    total = sum(d for _, d, *_ in history)
    send_chat_message(youtube, chat_id, f"{user_name} Your total focus time: {format_duration(total)}")

def handle_study_command(youtube, chat_id, user_id, user_name, stream_id, action):
    key = (stream_id, user_id)
    now = time.time()

    if action == "start":
        study_sessions[key] = now
        send_chat_message(youtube, chat_id, f"{user_name} Started your focus session! Let's go! 💪")
    elif action == "stop":
        start_time = study_sessions.pop(key, None)
        if start_time:
            duration = now - start_time
            history = load_study_history(stream_id, user_id)
            history.append((datetime.utcnow().isoformat(), duration, user_name))
            save_study_history(stream_id, user_id, history)
            send_chat_message(youtube, chat_id, f"{user_name} Session stopped. You focused for {format_duration(duration)}")
        else:
            send_chat_message(youtube, chat_id, f"{user_name} You haven't started a session yet. Use !start")

def handle_time_command(youtube, chat_id, user_id, user_name, stream_id=None):
    greeting = time_greeting()
    now = datetime.now().strftime('%B %d %Y, %I:%M %p')
    send_chat_message(youtube, chat_id, f"{user_name} {greeting}! Current server time is {now}")

def handle_location_command(youtube, chat_id, user_id, user_name, text):
    parts = resolve_command(text).split(maxsplit=1)
    if len(parts) < 2:
        send_chat_message(youtube, chat_id, f"{user_name} Please provide a location after !location")
    else:
        loc = parts[1]
        msg = get_local_time(loc)
        send_chat_message(youtube, chat_id, f"{user_name} {msg}")

def handle_quiz_command(youtube, chat_id, user_id, user_name, stream_id):
    stream_id = stream_id or "default"
    response = start_quiz(stream_id, user_id)
    send_chat_message(youtube, chat_id, f"{user_name} {response}")

def handle_quiz_answer(youtube, chat_id, user_id, user_name, stream_id, text):
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        send_chat_message(youtube, chat_id, f"{user_name} Please answer like !answer <option number or text>")
        return
    answer_text = parts[1]
    result = check_quiz_answer(stream_id, user_id, answer_text)
    send_chat_message(youtube, chat_id, f"{user_name} {result}")

def handle_complete_goal(youtube, chat_id, user_id, user_name, stream_id):
    result = complete_user_goal(stream_id, user_id)
    send_chat_message(youtube, chat_id, f"{user_name} {result}")

def handle_mention(youtube, chat_id, user_id, user_name, text):
    system_prompt = get_system_prompt()

    user_prompt = f"The user said: \"{text}\""

    response = call_openai_api(system_prompt, user_prompt)

    if response:
        # Count words
        words = response.strip().split()
        # Count sentences (split by period, question mark, exclamation)
        sentences = re.split(r'[.!?]', response.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        send_chat_message(youtube, chat_id, f"{user_name} {response[:200]}")


def handle_shutdown(youtube, chat_id, user_name):
    send_chat_message(youtube, chat_id, f"🛑 Bot is shutting down as requested by {user_name}")
    os._exit(0)

def get_system_prompt():
    gender = BOT_PERSONA["gender"]
    mood = BOT_PERSONA["mood"]

    base = f"You are Zephy Jr., a chatbot created by Zephyr for payal's youtube channel. Reply only in Hinglish(Hindi+Casual English). Short, crisp replies (max 10 words)."

    if gender == "female":
        persona = "Pretend to be a girl"
    else:
        persona = "Pretend to be a boy"

    # moods
    moods = {
        "flirty": "Be cheesy, too much flirty, playful, a little naughty and dramatic.",
        "sarcastic": "Be overly witty, too much savage, very sarcastic, roasting everyone.",
        "polite": "Be kind, supportive, sweet, and polite.",
        "funny": "Be very funny, roast people playfully, crack quick jokes, exaggerate everything for comedy, like a stand-up comedian.",
        "naughty": "Be an 18+ naughty bot: lusty, horny, shameless, flirty, seductive. Tease, provoke, and twist every reply into dirty talk and innuendos."
    }

    mood_text = moods.get(mood, "")

    return f"{base} {persona}. {mood_text}"



def process_message(
    youtube: Any,
    chat_id: str,
    message: dict,
    stream_id: str,
    oauth_idx: int
) -> None:
    global SPAM_PROTECTION, BOT_MESSAGE_COOLDOWN, WELCOME_COOLDOWN
    global last_welcome_time, welcome_enabled, welcome_start_time

    try:
        snippet = message.get("snippet", {})
        author = message.get("authorDetails", {})
        published = snippet.get("publishedAt")
        raw_user = author.get("displayName")
        user_id = author.get("channelId")
        welcomed_users = load_welcomed_users(stream_id)
        text = snippet.get("displayMessage", "").strip()

        if author.get("isChatOwner"):
            if user_id not in ADMINS:
                ADMINS.append(user_id)
                save_admins()  # Save to file
                logger.info(f"👑 Auto-added stream owner {user_id} as admin")

        elif author.get("isChatModerator"):
            if user_id not in ADMINS:
                ADMINS.append(user_id)
                save_admins()  # Save to file
                logger.info(f"🔧 Auto-added moderator {user_id} as admin")

        is_admin_user = is_admin(user_id)        

        if user_id in BLOCKED_CHANNELS:
            return

        if is_admin_user:
            logger.debug(f"👑 Admin command received: {raw_user} - {text}")
        else:
            if not can_send_message(user_id, stream_id, text):
                logger.debug(f"⛔️ Blocked by spam protection: {raw_user} - {text}")
                return

        msg_fingerprint = f"{user_id}::{text}".lower().strip()
        if msg_fingerprint in processed_messages:
            return

        # Process the message here (your existing logic follows)

        processed_messages.add(msg_fingerprint)
        save_processed(processed_messages)


        try:
            msg_time = parser.isoparse(published)
            if msg_time < BOT_START_TIME - timedelta(seconds=5):
                return
        except Exception as e:
            logger.error(f"Bad timestamp '{published}': {e}")
            msg_time = BOT_START_TIME

        logger.info(f"🔁 Processing message from {raw_user}: {text}")
        cmd = text.lower()

        if re.search(r'\b(?:@?zephy(?:[\s\-]?jr)?|@bot|@?youtubebot[\s\-_]?o1v|@?ytbot[\s\-_]?o1v?|youtube[\s\-_]?bot)\b(?=[\s\W]|$)', text.lower()):
            handle_mention(youtube, chat_id, user_id, raw_user, text)
            return

        # 🔒 Admin commands
        if cmd.startswith("!shutdown"):
            if is_admin_user:
                handle_shutdown(youtube, chat_id, raw_user)
            else:
                send_chat_message(youtube, chat_id, f"{raw_user} {get_non_admin_snark()}")
            return
        
        

        if cmd.startswith("!spam on"):
            if is_admin_user:
                SPAM_PROTECTION = True
                send_chat_message(youtube, chat_id, "🧠 Spam protection is now ON.")
            else:
                send_chat_message(youtube, chat_id, f"{raw_user} {get_non_admin_snark()}")
            return
        
        if cmd.startswith("!gender"):
            if is_admin_user:
                parts = cmd.split(maxsplit=1)
                if len(parts) == 2 and parts[1].lower() in ["male", "female"]:
                    BOT_PERSONA["gender"] = parts[1].lower()
                    send_chat_message(youtube, chat_id, f"✅ Gender switched to {BOT_PERSONA['gender']}.")
                else:
                    send_chat_message(youtube, chat_id, "⚠️ Usage: !gender male|female")
            else:
                send_chat_message(youtube, chat_id, f"{raw_user} {get_non_admin_snark()}")
            return

        if cmd.startswith("!mood"):
            if is_admin_user:
                parts = cmd.split(maxsplit=1)
                if len(parts) == 2 and parts[1].lower() in ["flirty", "sarcastic", "polite","funny", "naughty"]:
                    BOT_PERSONA["mood"] = parts[1].lower()
                    send_chat_message(youtube, chat_id, f"🎭 Mood switched to {BOT_PERSONA['mood']}.")
                else:
                    send_chat_message(youtube, chat_id, "⚠️ Usage: !mood flirty|sarcastic|polite|funny|naughty")
            else:
                send_chat_message(youtube, chat_id, f"{raw_user} {get_non_admin_snark()}")
            return


        if cmd.startswith("!spam off"):
            if is_admin_user:
                SPAM_PROTECTION = False
                send_chat_message(youtube, chat_id, "😈 Spam protection is now OFF.")
            else:
                send_chat_message(youtube, chat_id, f"{raw_user} {get_non_admin_snark()}")
            return

        if text.strip().lower() == "!togglewelcome":
            if is_admin_user:
                welcome_enabled = not welcome_enabled
                status = "enabled ✅" if welcome_enabled else "disabled"
                logger.info(f"👑 Admin {raw_user} toggled welcome_enabled → {welcome_enabled}")
                send_chat_message(youtube, chat_id, f"🛑 Welcoming users is now {status}.", target_user=author)
            else:
                send_chat_message(youtube, chat_id, f"{raw_user} {get_non_admin_snark()}")
            return

        if cmd.startswith("!cooldown"):
            if is_admin_user:
                parts = cmd.split()
                if len(parts) == 1:
                    send_chat_message(
                        youtube, chat_id,
                        f"🕒 Current cooldowns:\n- Bot replies: {BOT_MESSAGE_COOLDOWN}s\n- Welcome: {WELCOME_COOLDOWN}s"
                    )
                elif len(parts) == 3 and parts[1] in ("bot", "welcome") and parts[2].isdigit():
                    seconds = max(1, min(int(parts[2]), 300))  # Clamp to 1–300s
                    if parts[1] == "bot":
                        BOT_MESSAGE_COOLDOWN = seconds
                        send_chat_message(youtube, chat_id, f"✅ Bot reply cooldown set to {seconds} seconds.")
                    else:
                        WELCOME_COOLDOWN = seconds
                        send_chat_message(youtube, chat_id, f"✅ Welcome cooldown set to {seconds} seconds.")
                else:
                    send_chat_message(youtube, chat_id, "⚠️ Usage: !cooldown [bot|welcome] <1–300>")
            else:
                send_chat_message(youtube, chat_id, f"{raw_user} {get_non_admin_snark()}")
            return

        # 💬 Regular commands (✅ moved outside exception)
        if cmd.startswith("!ask"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                send_chat_message(youtube, chat_id, f"{raw_user} Ask me something!")
                return
            response = call_openai_api(
                "You are Zephy Jr., Zephyr’s bot. Reply only in English. "
                "Always one short, crisp sentence (max 10 words). Be overly witty, savage, and sarcastic, "
                "never polite, no greetings. Always end with a period",
                parts[1]
            )
            if response:
                send_chat_message(youtube, chat_id, f"{raw_user} {response[:200]}")
            else:
                send_chat_message(youtube, chat_id, f"{raw_user} The AI took a break 🧠💤")
            return

        elif cmd.startswith("!start"):
            handle_study_command(youtube, chat_id, user_id, raw_user, stream_id, "start")
            return

        elif cmd.startswith("!stop"):
            handle_study_command(youtube, chat_id, user_id, raw_user, stream_id, "stop")
            return

        elif cmd.startswith("!goal"):
            handle_goal_command(youtube, chat_id, user_id, raw_user, stream_id, text)
            return

        elif cmd.startswith("!remind"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                send_chat_message(youtube, chat_id, f"{raw_user} Usage: !remind <minutes> <message>", target_user=raw_user)
                return

            try:
                minutes = int(parts[1])
                reminder_text = parts[2]
                delay = minutes * 60
                remind_at = time.time() + delay

                add_reminder(stream_id, user_id, reminder_text, remind_at)

                threading.Timer(delay, lambda: send_chat_message(
                    youtube, chat_id,
                    f"⏰ Reminder for {raw_user}: {reminder_text}",
                    target_user=raw_user
                )).start()

                send_chat_message(youtube, chat_id, f"{raw_user} Got it! I’ll remind you in {minutes} minute(s). ⏰", target_user=raw_user)

            except ValueError:
                send_chat_message(youtube, chat_id, f"{raw_user} Please enter time in numbers only.", target_user=raw_user)
            return

        elif cmd.startswith("!reminders"):
            data = load_reminders(stream_id)
            reminders = data.get(user_id, [])
            remove_expired_reminders(stream_id)

            if not reminders:
                send_chat_message(youtube, chat_id, f"{raw_user} You have no pending reminders.", target_user=raw_user)
            else:
                now = time.time()
                lines = [
                    f"⏳ {r['text']} — in {int((r['time'] - now) / 60)} min(s)"
                    for r in reminders if r["time"] > now
                ]
                reply = "; ".join(lines)[:200]
                send_chat_message(youtube, chat_id, f"{raw_user} Your reminders: {reply}", target_user=raw_user)
            return

        elif cmd.startswith("!reset"):
            handle_reset_command(youtube, chat_id, user_id, raw_user, stream_id)
            return

        elif cmd.startswith("!leaderboard") or cmd.startswith("!lb"):
            handle_leaderboard_command(youtube, chat_id, user_id, raw_user, stream_id)
            return

        elif cmd.startswith("!session"):
            handle_session_command(youtube, chat_id, user_id, raw_user, stream_id)
            return

        elif cmd.startswith("!history"):
            history = load_study_history(stream_id, user_id)
            if not history:
                send_chat_message(youtube, chat_id, f"{raw_user} You have no focus session history yet.", target_user=raw_user)
                return

            total = sum(d for _, d, *_ in history)
            avg = total / len(history)
            last = history[-1][0].split("T")[0]

            msg = (
                f"📘 Focus history:\n"
                f"- Sessions: {len(history)}\n"
                f"- Total: {format_duration(total)}\n"
                f"- Avg: {format_duration(avg)}\n"
                f"- Last: {last}"
            )
            send_chat_message(youtube, chat_id, f"{raw_user} {msg}", target_user=raw_user)
            return

        elif cmd.startswith("!time"):
            parts = cmd.split(maxsplit=1)
            if len(parts) == 1:
                now = datetime.now()
                formatted = now.strftime("%B %d %Y, %I:%M %p")
                send_chat_message(youtube, chat_id, f"{raw_user} Current server time is {formatted}", target_user=raw_user)
                return
            try:
                from geopy.geocoders import Nominatim
                from timezonefinder import TimezoneFinder
                from zoneinfo import ZoneInfo

                city = parts[1].strip()
                geolocator = Nominatim(user_agent="Zephy Jr.")
                location = geolocator.geocode(city, timeout=5)

                if not location:
                    send_chat_message(youtube, chat_id, f"{raw_user} Couldn't find city '{city}'.", target_user=raw_user)
                    return

                tf = TimezoneFinder()
                timezone_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)

                if not timezone_str:
                    send_chat_message(youtube, chat_id, f"{raw_user} Couldn't determine timezone for '{city}'.", target_user=raw_user)
                    return

                now = datetime.now(ZoneInfo(timezone_str))
                formatted = now.strftime("%B %d %Y, %I:%M %p")
                send_chat_message(youtube, chat_id, f"{raw_user} Time in {city.title()} is {formatted}", target_user=raw_user)

            except Exception as e:
                logger.error(f"❌ Error in !time command: {e}")
                send_chat_message(youtube, chat_id, f"{raw_user} Something went wrong getting the time for '{parts[1]}'.", target_user=raw_user)
            return

        elif cmd.startswith("!date"):
            now = datetime.now()
            formatted = now.strftime("%B %d, %Y")
            send_chat_message(youtube, chat_id, f"{raw_user} Today is {formatted}", target_user=raw_user)
            return

        elif cmd.startswith("!weather"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                send_chat_message(youtube, chat_id, f"{raw_user} Usage: !weather <city>")
            else:
                weather_info = get_weather(parts[1])
                send_chat_message(youtube, chat_id, f"{raw_user} {weather_info}")
            return

        elif cmd.startswith("!quiz"):
            handle_quiz_command(youtube, chat_id, user_id, raw_user, stream_id)
            return

        elif cmd.startswith("!answer"):
            handle_quiz_answer(youtube, chat_id, user_id, raw_user, stream_id, text)
            return

        elif cmd.startswith("!complete"):
            handle_complete_goal(youtube, chat_id, user_id, raw_user, stream_id)
            return

        elif cmd.startswith("!commands") or cmd.startswith("!help"):
            msg1 = (
                "📚 Commands: !start !stop !session !history !goal !complete !reset "
                "| ⏰ !remind !reminders | 🧠 !quiz !answer !ask"
            )
            msg2 = (
                "🌍 !time <city> !date !weather <city> | 🏆 !leaderboard !lb "
                "| 🤖 mention @zephy | 🔒 Admin: !spam on/off, !shutdown, !cooldown welcome/bot <time> "
            )
            send_chat_message(youtube, chat_id, f"{raw_user} {msg1}", target_user=raw_user)
            time.sleep(1.5)
            send_chat_message(youtube, chat_id, f"{raw_user} {msg2}", target_user=raw_user)
            return

        # 👋 Welcome logic (unchanged)
        if welcome_enabled and user_id not in welcomed_users:
            now = time.time()
            if not SPAM_PROTECTION or is_admin_user or now - last_welcome_time > WELCOME_COOLDOWN:
                welcome_msg = get_random_welcome(raw_user)
                send_chat_message(youtube, chat_id, welcome_msg)

                last_welcome_time = now
                save_welcomed_user(stream_id, user_id)
                logger.info(f"👋 Welcomed user: {raw_user}")
            else:
                logger.info(f"⚠️ Skipping welcome for {raw_user} due to cooldown — NOT saving yet")

    except HttpError as e:
        logger.error(f"HTTP error processing message: {e}")
        if e.resp.status == 403:
            oauth_indices[stream_id] = (oauth_idx + 1) % len(CLIENT_SECRET_FILES)
    except Exception as e:
        logger.error(f"Unexpected error processing message: {e}")

# ==================== SESSION CLEANUP ====================
def clean_expired_sessions():
    """Periodically clean up old sessions"""
    while True:
        try:
            now = time.time()
            # Clean study sessions older than 24 hours
            expired = [k for k, v in study_sessions.items() if now - v > 86400]
            for k in expired:
                study_sessions.pop(k, None)
            
            # Clean quizzes older than 1 hour
            expired = [k for k, v in active_quizzes.items() if now - v['timestamp'] > 3600]
            for k in expired:
                active_quizzes.pop(k, None)
                
            # Clean completed goals older than 7 days
            with goals_lock:
                for k, goal in list(user_goals.items()):
                    if goal.get('completed'):
                        completed_time = parser.parse(goal['completed_at'])
                        if (datetime.now(timezone.utc) - completed_time).days > 7:
                            user_goals.pop(k, None)
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        time.sleep(3600) # Run hourly

# ==================== QUEUE PROCESSING ====================
async def process_queued_messages():
    """Improved queue processor with fair scheduling and rate limiting"""
    # Track processing stats to ensure fairness
    messages_processed = 0
    last_fairness_reset = time.time()
    
    while True:
        try:
            current_time = time.time()
            
            # Reset fairness counter every second
            if current_time - last_fairness_reset > 1.0:
                messages_processed = 0
                last_fairness_reset = current_time
            
            # Process messages with fair scheduling - max 20 messages per second
            if messages_processed < 20:
                processed_any = False
                
                # Process admin messages (max 5 per cycle)
                admin_processed = 0
                while admin_queue and admin_processed < 5 and messages_processed < 20:
                    try:
                        best = min(admin_queue, key=lambda x: x[0])
                        admin_queue.remove(best)
                        _, args = best
                        process_message(*args)
                        messages_processed += 1
                        admin_processed += 1
                        processed_any = True
                    except (ValueError, KeyError):
                        continue  # Item already removed
                
                # Process priority messages (max 8 per cycle)
                priority_processed = 0
                while priority_queue and priority_processed < 8 and messages_processed < 20:
                    try:
                        best = min(priority_queue, key=lambda x: x[0])
                        priority_queue.remove(best)
                        _, args = best
                        process_message(*args)
                        messages_processed += 1
                        priority_processed += 1
                        processed_any = True
                    except (ValueError, KeyError):
                        continue
                
                # Process normal messages (max 7 per cycle)
                normal_processed = 0
                while normal_queue and normal_processed < 7 and messages_processed < 20:
                    try:
                        args = normal_queue.popleft()
                        process_message(*args)
                        messages_processed += 1
                        normal_processed += 1
                        processed_any = True
                    except IndexError:
                        break
                
                # If we processed any messages, continue immediately
                if processed_any:
                    await asyncio.sleep(0.01)  # Small delay to prevent CPU spinning
                    continue
            
            # If we hit rate limits or no messages, sleep longer
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Queue processing error: {e}")
            await asyncio.sleep(5)

# Add this missing function (place it with other queue functions):
def trim_queues_if_needed():
    """Trim queues if they become too large to prevent memory issues"""
    max_normal_size = 2000
    max_priority_size = 1000
    max_admin_size = 500
    
    if len(normal_queue) > max_normal_size:
        excess = len(normal_queue) - max_normal_size
        for _ in range(excess):
            try:
                normal_queue.popleft()
            except IndexError:
                break
        logger.warning(f"Trimmed {excess} messages from normal queue")
    
    if len(priority_queue) > max_priority_size:
        excess = len(priority_queue) - max_priority_size
        # Remove lowest priority messages
        sorted_priority = sorted(priority_queue, key=lambda x: x[0], reverse=True)
        for _ in range(excess):
            if sorted_priority:
                item_to_remove = sorted_priority.pop()
                try:
                    priority_queue.remove(item_to_remove)
                except ValueError:
                    pass
        logger.warning(f"Trimmed {excess} messages from priority queue")
    
    if len(admin_queue) > max_admin_size:
        excess = len(admin_queue) - max_admin_size
        sorted_admin = sorted(admin_queue, key=lambda x: x[0], reverse=True)
        for _ in range(excess):
            if sorted_admin:
                item_to_remove = sorted_admin.pop()
                try:
                    admin_queue.remove(item_to_remove)
                except ValueError:
                    pass
        logger.warning(f"Trimmed {excess} messages from admin queue")

# Remove the duplicate insecure_request function (keep only one):
def insecure_request(self, method, url, **kwargs):
    kwargs['verify'] = False
    kwargs['timeout'] = 30
    try:
        return original_request(self, method, url, **kwargs)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise

# ==================== MAIN FUNCTION ====================
async def main():
    try:
        # Clean up corrupted tokens on startup
        cleanup_corrupted_tokens()
        
        # ✅ Start cleanup thread
        threading.Thread(target=clean_expired_sessions, daemon=True).start()

        # ✅ Clear queues and processed messages on fresh start
        admin_queue.clear()
        normal_queue.clear()

        # ✅ Get video IDs
        video_id_1 = extract_video_id(os.getenv('VIDEO_ID_1', 'O-sJ8qOvNr4'))
        video_id_2 = extract_video_id(os.getenv('VIDEO_ID_2', ''))

        # ✅ Start queue processor
        asyncio.create_task(process_queued_messages())

        threads = []
        if video_id_1:
            threads.append(threading.Thread(target=run_bot, args=(video_id_1, 0 )))
        if video_id_2:
            threads.append(threading.Thread(target=run_bot, args=(video_id_2, 1)))
        if not threads: 
            raise ValueError("No valid video IDs provided")

        for t in threads: 
            t.daemon = True
            t.start()

        # ✅ Watchdog to keep threads alive
        while True:
            for i, t in enumerate(threads):
                if not t.is_alive():
                    logger.warning(f"⚠️ Bot thread {i+1} died! Restarting...")
                    video_id = video_id_1 if i == 0 else video_id_2
                    new_thread = threading.Thread(target=run_bot, args=(video_id, i), daemon=True)
                    threads[i] = new_thread
                    new_thread.start()

            logger.info("🟢 Watchdog: All bot threads healthy.")
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    load_admins()  # Load saved admins when bot starts

    try:
        asyncio.run(main())
    except Exception as e:

        logger.error(f"❌ Bot crashed with exception: {e}")
