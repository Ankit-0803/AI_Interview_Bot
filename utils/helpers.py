"""
Utility helper functions for the AI Video Interview Bot
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import streamlit as st

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

def save_json(data: Dict[str, Any], filepath: Path) -> bool:
    """Save data to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        st.error(f"Error saving JSON file: {e}")
        return False

def load_json(filepath: Path) -> Dict[str, Any]:
    """Load data from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return {}

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {remaining_seconds:.1f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"

def validate_audio_input(audio_data) -> bool:
    """Validate audio input data"""
    if audio_data is None:
        return False
    
    if hasattr(audio_data, '__len__') and len(audio_data) == 0:
        return False
    
    return True

def create_progress_bar(current: int, total: int) -> str:
    """Create a visual progress bar"""
    progress = current / total
    bar_length = 20
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    percentage = progress * 100
    return f"Progress: [{bar}] {percentage:.1f}% ({current}/{total})"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def get_file_size_mb(filepath: Path) -> float:
    """Get file size in MB"""
    try:
        return filepath.stat().st_size / (1024 * 1024)
    except:
        return 0.0
