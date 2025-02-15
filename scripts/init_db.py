import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.database.database import init_db
from app.database.models import Base
from dotenv import load_dotenv

def main():
    load_dotenv()
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    main()
