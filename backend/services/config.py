import os
from dotenv import load_dotenv

# Load environment variables from the workspace root folder
# Since we are starting the backend inside AI_AD_CREATIVE_STUDIO/backend or root, load_dotenv will search upwards.
load_dotenv(override=True)

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    @classmethod
    def validate(self):
        if not self.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured.")
        if not self.GEMINI_MODEL:
            raise ValueError("Gemini Model configuration missing.")
 

config = Config()
