#!/usr/bin/env python3
"""
Script to create an admin user for CyberShield application.
Run this script to create the default admin account.
"""

import sys
import os
from sqlalchemy.orm import Session

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.database import SessionLocal, User, create_tables
from app.routers.auth import get_password_hash

def create_admin_user():
    """Create the default admin user."""
    
    # Create tables if they don't exist
    create_tables()
    
    # Create database session
    db: Session = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("❌ Admin user already exists!")
            print(f"Username: {existing_admin.username}")
            print(f"Email: {existing_admin.email}")
            print(f"Is Admin: {existing_admin.is_admin}")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@cybershield.com",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print("=" * 50)
        print("🔐 ADMIN CREDENTIALS:")
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@cybershield.com")
        print("=" * 50)
        print("⚠️  IMPORTANT: Change the default password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def create_test_users():
    """Create some test users for demonstration."""
    
    db: Session = SessionLocal()
    
    try:
        test_users = [
            {
                "username": "alice",
                "email": "alice@example.com",
                "full_name": "Alice Johnson",
                "password": "alice123"
            },
            {
                "username": "bob", 
                "email": "bob@example.com",
                "full_name": "Bob Smith",
                "password": "bob123"
            },
            {
                "username": "charlie",
                "email": "charlie@example.com", 
                "full_name": "Charlie Brown",
                "password": "charlie123"
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            
            if not existing_user:
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    hashed_password=get_password_hash(user_data["password"]),
                    is_active=True,
                    is_admin=False
                )
                
                db.add(new_user)
                created_users.append(user_data)
        
        if created_users:
            db.commit()
            print("\n✅ Test users created successfully!")
            print("=" * 50)
            print("👥 TEST USER CREDENTIALS:")
            for user in created_users:
                print(f"Username: {user['username']} | Password: {user['password']}")
            print("=" * 50)
        else:
            print("\n⚠️  Test users already exist.")
            
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 CyberShield Admin Setup")
    print("=" * 50)
    
    create_admin_user()
    
    # Ask if user wants to create test users
    create_test = input("\n🤔 Do you want to create test users for demo? (y/n): ").lower().strip()
    
    if create_test in ['y', 'yes']:
        create_test_users()
    
    print("\n🎉 Setup complete! You can now start the application.")
    print("💡 Run: uvicorn app.main:app --reload")
