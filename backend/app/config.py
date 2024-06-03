import os

class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    SERPER_API_KEY = os.environ.get('SERPER_API_KEY')