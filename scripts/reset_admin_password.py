import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.database.database import SessionLocal
from app.database.models import User
from app.auth.auth import get_password_hash
from dotenv import load_dotenv

def reset_admin_password(username: str, new_password: str):
    db = SessionLocal()
    try:
        # Find admin user
        admin_user = db.query(User).filter(User.username == username).first()
        if not admin_user:
            print(f"User {username} not found!")
            return

        # Update password
        admin_user.password = get_password_hash(new_password)
        db.commit()
        print(f"Password for user {username} updated successfully!")
    except Exception as e:
        print(f"Error updating admin password: {str(e)}")
        db.rollback()
    finally:
        db.close()

def main():
    load_dotenv()
    
    username = "admin"
    new_password = "admin123!"  # More secure password with special character
    
    reset_admin_password(username, new_password)

if __name__ == "__main__":
    main()
