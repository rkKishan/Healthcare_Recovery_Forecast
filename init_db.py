"""
Initialize database with test data
Run this once to set up the database
"""

from database import SessionLocal, User, create_tables
from auth import hash_password
import sys

def init_database():
    """Create tables and add test user"""
    print("🔧 Creating database tables...")
    create_tables()
    print("✅ Tables created!")
    
    print("\n👤 Adding test user...")
    db = SessionLocal()
    
    # Check if test user already exists
    existing = db.query(User).filter(User.hospital_id == "DEMO001").first()
    if existing:
        print("⚠️  Test user already exists!")
        db.close()
        return
    
    # Create test user
    test_user = User(
        hospital_id="DEMO001",
        email="demo@hospital.com",
        full_name="Dr. Demo User",
        hospital_name="Demo Hospital",
        hashed_password=hash_password("password123"),
        role="admin",
        is_active=True
    )
    
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    print(f"✅ Test user created!")
    print(f"\n📝 Test Credentials:")
    print(f"   Hospital ID: DEMO001")
    print(f"   Password: password123")
    print(f"   Email: demo@hospital.com")
    
    db.close()


if __name__ == "__main__":
    try:
        init_database()
        print("\n✨ Database initialization complete!")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
