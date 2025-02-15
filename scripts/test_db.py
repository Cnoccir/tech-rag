import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import inspect
from app.database.database import engine, init_db
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # Try to connect to the database
    print("Testing database connection...")
    inspector = inspect(engine)
    
    # Print existing tables
    print("\nExisting tables:")
    print(inspector.get_table_names())
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    
    # Print tables after initialization
    print("\nTables after initialization:")
    print(inspector.get_table_names())

if __name__ == "__main__":
    main()
