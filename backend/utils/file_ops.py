"""
File operations utilities
"""

import os
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def ensure_directory(path: str) -> Path:
    """Ensure directory exists, create if it doesn't"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def load_json_file(file_path: str, default: Any = None) -> Any:
    """Load JSON file with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        return default

def save_json_file(file_path: str, data: Any) -> bool:
    """Save data to JSON file with error handling"""
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False

def load_pickle_file(file_path: str, default: Any = None) -> Any:
    """Load pickle file with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        return default
    except Exception as e:
        logger.error(f"Failed to load pickle file {file_path}: {e}")
        return default

def save_pickle_file(file_path: str, data: Any) -> bool:
    """Save data to pickle file with error handling"""
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"Failed to save pickle file {file_path}: {e}")
        return False

def clean_old_files(directory: str, pattern: str, max_age_days: int = 7) -> int:
    """Clean old files matching pattern in directory"""
    cleaned = 0
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return cleaned
            
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                # Check file age
                file_age = (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days
                if file_age > max_age_days:
                    file_path.unlink()
                    cleaned += 1
                    logger.info(f"Cleaned old file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to clean old files in {directory}: {e}")
    
    return cleaned