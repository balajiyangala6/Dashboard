#!/usr/bin/env python
"""
Setup admin user in MongoDB Atlas for production
"""
import os
from datetime import datetime, timezone
from pymongo import MongoClient
from django.contrib.auth.hashers import make_password

# MongoDB Atlas connection
MONGODB_URI = "mongodb+srv://balajiyangala6_db_user:BL1efo4diGYd3YVf@cluster0.x80auwp.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DATABASE = "balaji_os"

def create_admin_user():
    """Create admin user in MongoDB Atlas"""
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    
    # Check if admin already exists
    existing = db.accounts.find_one({'username': 'admin'})
    if existing:
        print("✓ Admin user already exists")
        return
    
    # Create admin user
    admin_data = {
        'username': 'admin',
        'email': 'admin@balaji.os',
        'display_name': 'Admin User',
        'role': 'admin',
        'password_hash': make_password('admin123'),  # Change this password!
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
    }
    
    result = db.accounts.insert_one(admin_data)
    print(f"✓ Admin user created with ID: {result.inserted_id}")
    print("\nLogin credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\n⚠️  IMPORTANT: Change this password after first login!")
    
    client.close()

if __name__ == '__main__':
    print("Creating admin user in MongoDB Atlas...")
    create_admin_user()
