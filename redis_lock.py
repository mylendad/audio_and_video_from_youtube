import redis
import time

r = redis.Redis(host='localhost', port=6379, db=0)

def acquire_user_lock(user_id: int, ttl: int = 600) -> bool:
    
    key = f"user_lock:{user_id}"
    result = r.setnx(key, int(time.time()))
    if result:
        r.expire(key, ttl)
    return result

def release_user_lock(user_id: int):
    r.delete(f"user_lock:{user_id}")
