#!/usr/bin/env python
"""
Test script to verify PostgreSQL connection.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from secret.env
load_dotenv("secret.env")

# Get database credentials (with fallbacks to Docker default values)
DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "telegram_bot_db")
DB_USER = os.environ.get("DB_USER", "botuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "botpassword")

def test_connection():
    """Test connection to PostgreSQL database."""
    # Construct database URL
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    logger.info(f"Attempting to connect to PostgreSQL at {DB_HOST}:{DB_PORT}")
    logger.info(f"Database: {DB_NAME}, User: {DB_USER}")
    
    try:
        # Create engine and connect
        engine = create_engine(DATABASE_URL)
        conn = engine.connect()
        
        # Execute a simple query
        result = conn.execute(text("SELECT version();"))
        version = result.scalar()
        
        logger.info("✅ Connection successful!")
        logger.info(f"PostgreSQL version: {version}")
        
        # Test schema access
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """))
        
        tables = [row[0] for row in result]
        if tables:
            logger.info(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
        else:
            logger.warning("⚠️ No tables found in the database")
            
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 