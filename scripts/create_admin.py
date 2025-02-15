import sys
import os
import uuid
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.database.database import SessionLocal
from app.database.models import User
from app.auth.auth import get_password_hash
from dotenv import load_dotenv

def create_admin_user(username: str, password: str):
    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"User {username} already exists!")
            return

        # Create new admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            username=username,
            password=get_password_hash(password),
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user {username} created successfully!")
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
    finally:
        db.close()

def main():
    load_dotenv()
    
    username = "admin"
    password = "admin123"  # You should change this in production
    
    create_admin_user(username, password)

if __name__ == "__main__":
    main()
