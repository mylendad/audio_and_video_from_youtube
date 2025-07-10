# redis_lock.py

import redis
import time

# подключение (настрой при необходимости)
r = redis.Redis(host='localhost', port=6379, db=0)

def acquire_user_lock(user_id: int, ttl: int = 600) -> bool:
    """
    Устанавливает флаг занятости пользователя.
    Возвращает True, если флаг установлен (нет активной загрузки).
    False — если уже выполняется загрузка.
    """
    key = f"user_lock:{user_id}"
    result = r.setnx(key, int(time.time()))
    if result:
        r.expire(key, ttl)
    return result

def release_user_lock(user_id: int):
    """Снимает блокировку"""
    r.delete(f"user_lock:{user_id}")
