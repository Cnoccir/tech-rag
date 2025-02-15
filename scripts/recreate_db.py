import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database.database import Base
from app.database.models import User
from app.routers.auth import get_password_hash
from dotenv import load_dotenv
import uuid

def recreate_database():
    load_dotenv()
    
    # Get database URL and create engine
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Extract base URL (without database name) and database name
    base_url = DATABASE_URL.rsplit('/', 1)[0]
    db_name = DATABASE_URL.rsplit('/', 1)[1]
    
    # Create engine to connect to base postgres database
    engine = create_engine(f"{base_url}/postgres")
    
    with engine.connect() as conn:
        # Disconnect all users and drop database if it exists
        conn.execute(text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid();
        """))
        conn.execute(text("COMMIT"))
        
        # Drop and recreate database
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        conn.execute(text("COMMIT"))
        conn.execute(text(f"CREATE DATABASE {db_name}"))
        conn.execute(text("COMMIT"))
    
    # Create new engine with the actual database
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            password=get_password_hash("admin4100"),
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully!")
        
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Recreating database...")
    recreate_database()
    print("Database recreation completed!")
