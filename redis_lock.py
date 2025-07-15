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
    
def get_all_locks(pattern: str = "user_lock:*") -> list[str]:
    """Вернёт все активные ключи блокировок пользователей."""
    return [key.decode("utf-8") for key in r.scan_iter(match=pattern)]

def is_locked(user_id: int) -> bool:
    """Проверяет, есть ли блокировка для конкретного пользователя."""
    return r.exists(f"user_lock:{user_id}") == 1

