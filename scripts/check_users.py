import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine, Base
from app.database.models import *
from app.routers.auth import get_password_hash

def main():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check existing users
        users = db.query(User).all()
        print("\nExisting users:")
        if users:
            for user in users:
                print(f"Username: {user.username}")
        else:
            print("No users found")
            
        # Create admin user if it doesn't exist
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("\nCreating admin user...")
            admin_user = User(
                username="admin",
                password=get_password_hash("admin4100")
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
        else:
            print("\nAdmin user already exists")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
