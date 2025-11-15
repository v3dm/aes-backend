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

# Expect DATABASE_URL to be set, e.g.:
# mysql+pymysql://fastapi_user:strong_password_here@127.0.0.1:3306/aes_db?charset=utf8mb4
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable not set. Example:\n"
        "mysql+pymysql://fastapi_user:strong_password_here@127.0.0.1:3306/aes_db?charset=utf8mb4"
    )

# create engine for MySQL (pymysql)
engine = create_engine(DATABASE_URL, echo=False, future=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Base model
Base = declarative_base()

class EncryptedBlob(Base):
    __tablename__ = "encrypted_blobs"
    id = Column(Integer, primary_key=True, index=True)
    ciphertext_b64 = Column(Text, nullable=False)    # base64: salt||iv||tag||ct
    filename = Column(String(255), nullable=True)
    note = Column(String(512), nullable=True)
    algorithm = Column(String(100), nullable=False, default="AES-256-GCM")
    kdf = Column(String(100), nullable=False, default="PBKDF2:100000")
    owner = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Create tables (safe; will create if missing)
def init_db():
    Base.metadata.create_all(bind=engine)

# initialize automatically
init_db()
