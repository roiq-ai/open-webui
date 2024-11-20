from open_webui.config import run_migrations
from open_webui.env import DATABASE_URL

print(DATABASE_URL)
run_migrations()