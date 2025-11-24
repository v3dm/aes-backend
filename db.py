# # db.py
# import os
# from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Text
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# # Default to local SQLite for development
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

# # For sqlite allow same thread
# connect_args = {}
# if DATABASE_URL.startswith("sqlite"):
#     connect_args = {"check_same_thread": False}

# engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# class EncryptedBlob(Base):
#     __tablename__ = "encrypted_blobs"
#     id = Column(Integer, primary_key=True, index=True)
#     ciphertext_b64 = Column(Text, nullable=False)    # base64 string of salt||iv||tag||ct
#     filename = Column(String(255), nullable=True)
#     note = Column(String(512), nullable=True)
#     algorithm = Column(String(100), nullable=False, default="AES-256-GCM")
#     kdf = Column(String(100), nullable=False, default="PBKDF2:100000")
#     owner = Column(String(255), nullable=True)       # optional user identifier
#     created_at = Column(DateTime(timezone=True), server_default=func.now())

# db.py  (MySQL-only, no sqlite fallback)


import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Text
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. CORRECT usage: Look for the variable named "DATABASE_URL"
DATABASE_URL = os.getenv("DATABASE_URL")

# If it's missing, we allow it to fail, but the 503 error in app.py handles the user experience.
if not DATABASE_URL:
    # Just a warning print, the app.py handles the actual 503
    print("WARNING: DATABASE_URL not set. Database features will fail.")
else:
    # 2. Fix for Supabase (they sometimes use postgres:// which SQLAlchemy hates)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Create engine conditionally
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
else:
    engine = None
    SessionLocal = None

# Base model
Base = declarative_base()

class EncryptedBlob(Base):
    __tablename__ = "encrypted_blobs"
    id = Column(Integer, primary_key=True, index=True)
    ciphertext_b64 = Column(Text, nullable=False)
    filename = Column(String(255), nullable=True)
    note = Column(String(512), nullable=True)
    algorithm = Column(String(100), nullable=False, default="AES-256-GCM")
    kdf = Column(String(100), nullable=False, default="PBKDF2:100000")
    owner = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def init_db():
    if engine:
        Base.metadata.create_all(bind=engine)

# Try to init immediately if we have a connection
init_db()
