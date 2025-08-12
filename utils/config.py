"""
Configuration settings for the AI Video Interview Bot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class"""
    
    # API Configuration
    HF_API_TOKEN = os.getenv('HF_API_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    HF_MODEL_NAME = os.getenv('HF_MODEL_NAME', 'microsoft/DialoGPT-medium')
    
    # Application Settings
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    MAX_QUESTION_COUNT = int(os.getenv('MAX_QUESTION_COUNT', 7))
    MIN_QUESTION_COUNT = int(os.getenv('MIN_QUESTION_COUNT', 5))
    AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', 16000))
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    REPORTS_DIR = DATA_DIR / 'reports'
    SESSIONS_DIR = DATA_DIR / 'interview_sessions'
    ASSETS_DIR = BASE_DIR / 'assets'
    
    # Ensure directories exist
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Hugging Face API Configuration
    HF_API_URL = "https://api-inference.huggingface.co/models"
    HF_HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}
    
    # Interview Configuration
    GREETING_TEMPLATE = """
    Hello and welcome to your {role_title} interview! 
    
    I'm an AI interviewer designed to help evaluate your skills and experience for this position. 
    This interview will consist of {question_count} questions tailored specifically to the {role_title} role.
    
    Please take your time with each response, speak clearly, and feel free to provide detailed examples 
    from your experience. Each question will be presented one at a time, and you'll have the opportunity 
    to record your video response.
    
    Let's begin when you're ready!
    """
    
    # Evaluation Criteria
    EVALUATION_CRITERIA = [
        "Technical Skills",
        "Communication",
        "Problem Solving",
        "Experience Relevance",
        "Cultural Fit",
        "Leadership Potential"
    ]
