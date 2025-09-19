#!/usr/bin/env python3
"""
Setup script for DocSense AI
Creates initial admin user and sets up database
"""

import os
import sys
sys.path.append('.')

from src.storage import Storage
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def main():
    storage = Storage(".")
    
    print("Creating initial admin user...")
    try:
        admin_password = "admin123"  # Change this
        hashed = get_password_hash(admin_password)
        storage.create_user("admin", "admin@docsense.com", hashed, "admin")
        print(f"Admin user created with password: {admin_password}")
        print("Username: admin")
    except Exception as e:
        print(f"Admin user might already exist: {e}")
    
    print("Setup complete!")

if __name__ == "__main__":
    main()