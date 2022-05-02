from environs import Env


env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")  # Забираем значение типа str
ADMINS = env.list("ADMINS")  # Тут у нас будет список из админов
IP = env.str("ip")  # Тоже str, но для айпи адреса хоста
PG_USER = env.str("PGUSER")
PG_PASS = env.str("PGPASS")
DB_NAME = env.str("DBNAME")

CHANNEL_URL = env.str("CHANNEL_URL")
CHANNEL_ID = env.str("CHANNEL_ID")
CHAT_ID = env.str("CHAT_ID")

POSTGRES_URI = f"postgresql://{PG_USER}:{PG_PASS}@{IP}/{DB_NAME}"