"""
Database utilities for storage.
"""

import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

# Get database configuration from environment variables or use SQLite by default
DB_TYPE = os.environ.get("DB_TYPE", "sqlite")

if DB_TYPE == "postgres":
    # PostgreSQL configuration
    DB_HOST = os.environ.get("DB_HOST", "postgres")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "telegram_bot_db")
    DB_USER = os.environ.get("DB_USER", "botuser")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "botpassword")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # SQLite configuration (default)
    DB_PATH = os.environ.get("DB_PATH", "telegram_bot.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    logger.info(f"Using SQLite database at {DB_PATH}")

# Create the engine
engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()


class User(Base):
    """User model for Telegram users."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    
    # Relationship with messages
    messages = relationship("Message", back_populates="user")

    def __repr__(self):
        return f"<User {self.display_name}>"


class Thread(Base):
    """Thread model for Telegram message threads."""
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    
    # Relationship with messages
    messages = relationship("Message", back_populates="thread")

    def __repr__(self):
        return f"<Thread {self.title}>"


class Message(Base):
    """Message model for Telegram messages."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="messages")
    thread = relationship("Thread", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.id}: {self.text[:20]}...>"


def init_db():
    """Initialize the database schema."""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        logger.error(f"Error getting database session: {e}")
        raise


def add_user(telegram_id, display_name):
    """Add a user to the database or get existing user."""
    db = get_db()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, display_name=display_name)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Added new user: {display_name} ({telegram_id})")
        elif user.display_name != display_name:
            # Update display name if changed
            user.display_name = display_name
            db.commit()
            logger.info(f"Updated user display name: {display_name} ({telegram_id})")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding/updating user: {e}")
        raise
    finally:
        db.close()


def add_thread(thread_id, title):
    """Add a thread to the database or get existing thread."""
    db = get_db()
    try:
        thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
        if not thread:
            thread = Thread(thread_id=thread_id, title=title)
            db.add(thread)
            db.commit()
            db.refresh(thread)
            logger.info(f"Added new thread: {title} ({thread_id})")
        elif thread.title != title and title != "Main Group Chat":
            # Update title if changed and not default
            thread.title = title
            db.commit()
            logger.info(f"Updated thread title: {title} ({thread_id})")
        return thread
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding/updating thread: {e}")
        raise
    finally:
        db.close()


def add_message(telegram_user_id, display_name, thread_telegram_id, thread_title, text, timestamp):
    """Add a message to the database."""
    db = get_db()
    try:
        # Get or create user
        user = add_user(telegram_user_id, display_name)
        
        # Get or create thread
        thread = add_thread(thread_telegram_id, thread_title)
        
        # Create message
        message = Message(
            user_id=user.id,
            thread_id=thread.id,
            text=text,
            timestamp=timestamp
        )
        db.add(message)
        db.commit()
        logger.info(f"Added new message from {display_name} in thread {thread_title}")
        return message
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding message: {e}")
        raise
    finally:
        db.close()


def get_messages_in_range(start_time, end_time):
    """Get messages within a specified time range."""
    db = get_db()
    try:
        # Query messages in time range
        messages = (
            db.query(Message, User, Thread)
            .join(User, Message.user_id == User.id)
            .join(Thread, Message.thread_id == Thread.id)
            .filter(Message.timestamp >= start_time, Message.timestamp <= end_time)
            .order_by(Message.timestamp)
            .all()
        )
        
        # Format results as dict of thread_id -> messages
        threaded_messages = {}
        for message, user, thread in messages:
            if thread.thread_id not in threaded_messages:
                threaded_messages[thread.thread_id] = []
            
            threaded_messages[thread.thread_id].append({
                "time": message.timestamp,
                "user_id": user.telegram_id,
                "display_name": user.display_name,
                "text": message.text
            })
        
        logger.info(f"Retrieved {len(messages)} messages between {start_time} and {end_time}")
        return threaded_messages
    except Exception as e:
        logger.error(f"Error getting messages in range: {e}")
        return {}
    finally:
        db.close()


def get_thread_titles():
    """Get all thread titles."""
    db = get_db()
    try:
        threads = db.query(Thread).all()
        thread_titles = {thread.thread_id: thread.title for thread in threads}
        return thread_titles
    except Exception as e:
        logger.error(f"Error getting thread titles: {e}")
        return {}
    finally:
        db.close()


def migrate_from_json(json_data):
    """Migrate data from JSON to database."""
    try:
        db = get_db()
        thread_logs = json_data.get("thread_logs", {})
        thread_titles = json_data.get("thread_titles", {})
        
        # Count for logging
        total_messages = 0
        
        # Process each thread
        for thread_id_str, messages in thread_logs.items():
            thread_id = int(thread_id_str)
            thread_title = thread_titles.get(thread_id_str, "Main Group Chat")
            
            # Add thread
            thread = add_thread(thread_id, thread_title)
            
            # Process messages in thread
            for msg in messages:
                # Get data
                user_id = msg.get("user_id")
                display_name = msg.get("display_name")
                text = msg.get("text")
                timestamp = datetime.fromisoformat(msg.get("time"))
                
                # Add message
                add_message(user_id, display_name, thread_id, thread_title, text, timestamp)
                total_messages += 1
        
        logger.info(f"Migrated {total_messages} messages from JSON to database")
    except Exception as e:
        db.rollback()
        logger.error(f"Error migrating data: {e}")
    finally:
        db.close() 