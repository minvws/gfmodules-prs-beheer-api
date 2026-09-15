from app.config import get_config
from app.db.db import Database

if __name__ == "__main__":
    config = get_config()
    db = Database(config.database)
    db.generate_tables()
