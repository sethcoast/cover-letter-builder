import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("Connected to Redis!")
except redis.ConnectionError:
    print("Failed to connect to Redis.")
