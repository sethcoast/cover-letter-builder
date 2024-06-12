import os

class Config:
    OPENAI_API_KEY          = os.environ.get('OPENAI_API_KEY')
    SERPER_API_KEY          = os.environ.get('SERPER_API_KEY')
    SECRET_KEY              = os.environ.get('SECRET_KEY')
    CELERY_BROKER_URL       = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND   = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_URL               = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')