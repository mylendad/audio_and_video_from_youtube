from envparse import Env # type: ignore[import-untyped]

env = Env()
env.read_envfile()

TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")
ADMIN_USER_ID = env.int("ADMIN_USER_ID")
DB_DSN = env.str("DB_DSN")
REQUIRED_CHANNELS = [ch for ch in env.list("REQUIRED_CHANNELS", default=[]) if ch]
SUBSCRIPTION_CHECK_TIMEOUT = env.int("SUBSCRIPTION_CHECK_TIMEOUT", default=10)

REDIS_HOST = env.str("REDIS_HOST", default="localhost")
REDIS_PORT = env.int("REDIS_PORT", default=6379)
HTTP_PORT = env.int("HTTP_PORT", default=8080)

STORAGE_HOST = env.str("STORAGE_HOST", default=None)
STORAGE_PORT = env.int("STORAGE_PORT", default=22)
STORAGE_USER = env.str("STORAGE_USER", default=None)
STORAGE_PASSWORD = env.str("STORAGE_PASSWORD", default=None)
STORAGE_PRIVATE_KEY_PATH = env.str("STORAGE_PRIVATE_KEY_PATH", default=None)
STORAGE_PATH = env.str("STORAGE_PATH", default="/")
STORAGE_PUBLIC_URL_PREFIX = env.str("STORAGE_PUBLIC_URL_PREFIX", default=None)
STORAGE_UPLOAD_ENABLED = env.bool("STORAGE_UPLOAD_ENABLED", default=True)

COOKIE_FILE = "www.youtube.com_cookies.txt"
