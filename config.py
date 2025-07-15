from envparse import Env

env = Env()
env.read_envfile()

TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")
ADMIN_USER_ID = env.int("ADMIN_USER_ID")

REQUIRED_CHANNELS = [ch for ch in env.list("REQUIRED_CHANNELS", default=[]) if ch]

DB_DSN = env.str("DB_DSN")
