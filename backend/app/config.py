import os

class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    SERPER_API_KEY = os.environ.get('SERPER_API_KEY')
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    SOCKET_IO_MESSAGE_QUEUE = 'redis://localhost:6379/0'