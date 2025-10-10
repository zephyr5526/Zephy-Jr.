"""
Bot runner service for managing Zephy Jr. bot instances
"""

import asyncio
import threading
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add parent directory to path to import the original bot
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class BotRunner:
    """Manages Zephy Jr. bot instances and their lifecycle"""
    
    def __init__(self):
        self.bot_threads: Dict[str, threading.Thread] = {}
        self.bot_status: Dict[str, Dict] = {}
        self.running = False
        self._lock = threading.Lock()
        
    async def start_bot(self, stream_id: str, video_url: Optional[str] = None) -> bool:
        """Start a bot instance for a stream"""
        try:
            with self._lock:
                if stream_id in self.bot_threads and self.bot_threads[stream_id].is_alive():
                    logger.warning(f"Bot for stream {stream_id} is already running")
                    return False
                
                # Import the original bot functions
                from Chatbot_old import run_bot, extract_video_id
                
                # Extract video ID from URL if provided
                if video_url:
                    video_id = extract_video_id(video_url)
                    if not video_id:
                        logger.error(f"Invalid video URL: {video_url}")
                        return False
                else:
                    video_id = stream_id
                
                # Start bot in a separate thread
                bot_thread = threading.Thread(
                    target=run_bot,
                    args=(video_id, 0),  # Use first OAuth index
                    daemon=True,
                    name=f"Bot-{stream_id}"
                )
                
                bot_thread.start()
                self.bot_threads[stream_id] = bot_thread
                
                # Update status
                self.bot_status[stream_id] = {
                    "is_running": True,
                    "start_time": datetime.now(timezone.utc),
                    "last_activity": datetime.now(timezone.utc),
                    "message_count": 0,
                    "error_count": 0,
                    "video_id": video_id,
                    "video_url": video_url
                }
                
                logger.info(f"✅ Started bot for stream {stream_id} (video: {video_id})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to start bot for stream {stream_id}: {e}")
            return False
    
    async def stop_bot(self, stream_id: str) -> bool:
        """Stop a bot instance for a stream"""
        try:
            with self._lock:
                if stream_id not in self.bot_threads:
                    logger.warning(f"No bot running for stream {stream_id}")
                    return False
                
                # Update status
                if stream_id in self.bot_status:
                    self.bot_status[stream_id]["is_running"] = False
                    self.bot_status[stream_id]["last_activity"] = datetime.now(timezone.utc)
                
                # Note: We can't forcefully stop the thread, but we can mark it for cleanup
                logger.info(f"🛑 Stopped bot for stream {stream_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to stop bot for stream {stream_id}: {e}")
            return False
    
    async def stop_all_bots(self) -> bool:
        """Stop all running bot instances"""
        try:
            with self._lock:
                for stream_id in list(self.bot_threads.keys()):
                    await self.stop_bot(stream_id)
                
                self.bot_threads.clear()
                logger.info("🛑 Stopped all bot instances")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to stop all bots: {e}")
            return False
    
    def get_bot_status(self, stream_id: Optional[str] = None) -> Dict:
        """Get status of bot(s)"""
        with self._lock:
            if stream_id:
                return self.bot_status.get(stream_id, {
                    "is_running": False,
                    "error": "Bot not found"
                })
            else:
                return {
                    "bots": self.bot_status,
                    "total_running": sum(1 for status in self.bot_status.values() if status.get("is_running", False))
                }
    
    def update_bot_activity(self, stream_id: str, message_count: int = 0, error_count: int = 0):
        """Update bot activity metrics"""
        with self._lock:
            if stream_id in self.bot_status:
                self.bot_status[stream_id]["last_activity"] = datetime.now(timezone.utc)
                self.bot_status[stream_id]["message_count"] += message_count
                self.bot_status[stream_id]["error_count"] += error_count
    
    def cleanup_dead_threads(self):
        """Clean up dead bot threads"""
        with self._lock:
            dead_threads = []
            for stream_id, thread in self.bot_threads.items():
                if not thread.is_alive():
                    dead_threads.append(stream_id)
            
            for stream_id in dead_threads:
                del self.bot_threads[stream_id]
                if stream_id in self.bot_status:
                    self.bot_status[stream_id]["is_running"] = False
                    self.bot_status[stream_id]["last_activity"] = datetime.now(timezone.utc)
                
                logger.info(f"🧹 Cleaned up dead thread for stream {stream_id}")
    
    async def restart_bot(self, stream_id: str, video_url: Optional[str] = None) -> bool:
        """Restart a bot instance"""
        await self.stop_bot(stream_id)
        await asyncio.sleep(2)  # Wait a bit before restarting
        return await self.start_bot(stream_id, video_url)