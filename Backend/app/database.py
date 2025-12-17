# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("MYSQL_URL")

if not DATABASE_URL:
    raise ValueError("MYSQL_URL no está definida")

# 🔑 fuerza uso de PyMySQL
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "mysql://", "mysql+pymysql://", 1
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
