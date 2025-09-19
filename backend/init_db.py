#!/usr/bin/env python3
"""
Initialize database with sample data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.database import create_tables, SessionLocal, User
from app.auth import get_password_hash

def init_database():
    # Create all tables
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@cybershield.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            is_admin=True,
            is_active=True
        )
        db.add(admin_user)
        
        # Create test users
        alice = User(
            username="alice",
            email="alice@test.com",
            hashed_password=get_password_hash("alice123"),
            full_name="Alice Johnson",
            is_admin=False,
            is_active=True
        )
        db.add(alice)
        
        bob = User(
            username="bob",
            email="bob@test.com",
            hashed_password=get_password_hash("bob123"),
            full_name="Bob Smith",
            is_admin=False,
            is_active=True
        )
        db.add(bob)
        
        charlie = User(
            username="charlie",
            email="charlie@test.com",
            hashed_password=get_password_hash("charlie123"),
            full_name="Charlie Brown",
            is_admin=False,
            is_active=True
        )
        db.add(charlie)
        
        db.commit()
        print("Database initialized successfully!")
        print("Users created:")
        print("- admin / admin123 (Admin)")
        print("- alice / alice123")
        print("- bob / bob123")
        print("- charlie / charlie123")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
