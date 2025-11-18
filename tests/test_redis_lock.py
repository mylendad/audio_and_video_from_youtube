import time
from unittest.mock import MagicMock

import pytest

from redis_lock import (
    acquire_user_lock,
    get_all_locks,
    is_locked,
    release_user_lock,
)


@pytest.fixture
def mock_redis(mocker):
    """Фикстура для мокирования клиента Redis."""
    mock = MagicMock()
    mocker.patch("redis_lock.r", mock)
    return mock


def test_acquire_user_lock_success(mock_redis):
    """Тест успешного получения блокировки."""
    user_id = 123
    mock_redis.setnx.return_value = True

    result = acquire_user_lock(user_id, ttl=300)

    assert result is True
    mock_redis.setnx.assert_called_once_with(f"user_lock:{user_id}", int(time.time()))
    mock_redis.expire.assert_called_once_with(f"user_lock:{user_id}", 300)


def test_acquire_user_lock_fail(mock_redis):
    """Тест неудачного получения блокировки."""
    user_id = 123
    mock_redis.setnx.return_value = False

    result = acquire_user_lock(user_id)

    assert result is False
    mock_redis.expire.assert_not_called()


def test_release_user_lock(mock_redis):
    """Тест снятия блокировки."""
    user_id = 123
    release_user_lock(user_id)
    mock_redis.delete.assert_called_once_with(f"user_lock:{user_id}")


def test_get_all_locks(mock_redis):
    """Тест получения всех блокировок."""
    mock_redis.scan_iter.return_value = [b"user_lock:1", b"user_lock:2"]
    
    locks = get_all_locks()
    
    assert locks == ["user_lock:1", "user_lock:2"]
    mock_redis.scan_iter.assert_called_once_with(match="user_lock:*")


def test_is_locked_true(mock_redis):
    """Тест проверки наличия блокировки (когда она есть)."""
    user_id = 123
    mock_redis.exists.return_value = 1

    assert is_locked(user_id) is True
    mock_redis.exists.assert_called_once_with(f"user_lock:{user_id}")


def test_is_locked_false(mock_redis):
    """Тест проверки наличия блокировки (когда ее нет)."""
    user_id = 123
    mock_redis.exists.return_value = 0

    assert is_locked(user_id) is False
    mock_redis.exists.assert_called_once_with(f"user_lock:{user_id}")
