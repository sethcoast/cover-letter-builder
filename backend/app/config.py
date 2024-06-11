import os

class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    SERPER_API_KEY = os.environ.get('SERPER_API_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
    REDIS_URL = os.environ.get('REDIS_URL')