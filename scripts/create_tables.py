import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.database.database import engine
from app.database.models import Base, User, Document, Chat, Message
from dotenv import load_dotenv

def main():
    load_dotenv()
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    main()
