#!/usr/bin/env python3
"""
Script to create an initial admin user for the Smart City IoT Platform
"""

import asyncio
import sys
import uuid
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, '/app')

from backend.core.database import AsyncSessionLocal
from backend.core.security import get_password_hash
from backend.models.user import User, UserRole


async def create_admin_user():
    """Create an admin user interactively"""

    print("=" * 60)
    print("Smart City IoT Platform - Create Admin User")
    print("=" * 60)
    print()

    # Get user input
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email (default: admin@smartcity.local): ").strip() or "admin@smartcity.local"
    full_name = input("Enter full name (default: System Administrator): ").strip() or "System Administrator"

    # Get password
    while True:
        password = getpass("Enter password (min 8 characters): ")
        if len(password) < 8:
            print("Error: Password must be at least 8 characters long")
            continue

        password_confirm = getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match")
            continue

        break

    print()
    print("Creating admin user...")

    # Create user in database
    async with AsyncSessionLocal() as db:
        try:
            # Check if user already exists
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.username == username))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"Error: User '{username}' already exists")
                return False

            # Create admin user
            admin_user = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                department="Administration",
                job_title="System Administrator"
            )

            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)

            print()
            print("✓ Admin user created successfully!")
            print()
            print("User Details:")
            print(f"  ID:       {admin_user.id}")
            print(f"  Username: {admin_user.username}")
            print(f"  Email:    {admin_user.email}")
            print(f"  Role:     {admin_user.role.value}")
            print()
            print("You can now log in with these credentials.")
            print()

            return True

        except Exception as e:
            await db.rollback()
            print(f"Error creating user: {e}")
            return False


async def create_default_admin():
    """Create a default admin user (non-interactive)"""
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select

            # Check if any admin exists
            result = await db.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print("Admin user already exists")
                return

            # Create default admin
            admin_user = User(
                id=str(uuid.uuid4()),
                username="admin",
                email="admin@smartcity.local",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),  # Change this!
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )

            db.add(admin_user)
            await db.commit()

            print("Default admin user created:")
            print("  Username: admin")
            print("  Password: admin123")
            print("  ⚠️  IMPORTANT: Change this password immediately!")

        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--non-interactive":
        asyncio.run(create_default_admin())
    else:
        asyncio.run(create_admin_user())
