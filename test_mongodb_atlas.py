#!/usr/bin/env python
"""
Test MongoDB Atlas connection
"""
import os
import certifi
from pymongo import MongoClient

# MongoDB Atlas connection
MONGODB_URI = "mongodb+srv://balajiyangala6_db_user:BL1efo4diGYd3YVf@cluster0.x80auwp.mongodb.net/?retryWrites=true&w=majority"

def test_connection():
    """Test MongoDB Atlas connection"""
    try:
        print("Connecting to MongoDB Atlas...")
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where(),
        )
        
        # Test connection
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB Atlas!")
        
        # List databases
        dbs = client.list_database_names()
        print(f"✓ Available databases: {dbs}")
        
        # Check balaji_os database
        db = client['balaji_os']
        collections = db.list_collection_names()
        print(f"✓ Collections in balaji_os: {collections}")
        
        # Check accounts collection
        if 'accounts' in collections:
            count = db.accounts.count_documents({})
            print(f"✓ Number of accounts: {count}")
        
        client.close()
        print("\n✅ MongoDB Atlas connection is working perfectly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    test_connection()
