from envparse import Env

env = Env()
env.read_envfile()

TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")
ADMIN_USER_ID = env.int("ADMIN_USER_ID")
DB_DSN = env.str("DB_DSN")
REQUIRED_CHANNELS = [ch for ch in env.list("REQUIRED_CHANNELS", default=[]) if ch]

REDIS_HOST = env.str("REDIS_HOST", default="localhost")
REDIS_PORT = env.int("REDIS_PORT", default=6379)
HTTP_PORT = env.int("HTTP_PORT", 8080)

COOKIE_FILE = "www.youtube.com_cookies.txt"
