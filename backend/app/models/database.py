from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import os

# Create SQLite database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./cybershield.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Relationships
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    reports = relationship("Report", foreign_keys="Report.user_id", back_populates="user")
    reported_reports = relationship("Report", foreign_keys="Report.reported_user_id", back_populates="reported_user")
    blocked_users = relationship("BlockedUser", foreign_keys="BlockedUser.user_id", back_populates="user")
    friend_requests_sent = relationship("FriendRequest", foreign_keys="FriendRequest.sender_id", back_populates="sender")
    friend_requests_received = relationship("FriendRequest", foreign_keys="FriendRequest.receiver_id", back_populates="receiver")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_abusive = Column(Boolean, default=False)
    abuse_score = Column(Float, default=0.0)  # 0-10 score for abuse severity
    abuse_type = Column(String, nullable=True)  # Type of abuse detected
    
    # Relationships
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # User who created the report
    reported_user_id = Column(Integer, ForeignKey("users.id"))  # User being reported
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)  # Optional: specific message being reported
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="pending")  # pending, reviewed, closed
    evidence_file_path = Column(String, nullable=True)
    description = Column(Text, nullable=True)  # Description of the report
    
    # Relationships
    user = relationship("User", back_populates="reports", foreign_keys=[user_id])
    reported_user = relationship("User", back_populates="reported_reports", foreign_keys=[reported_user_id])
    message = relationship("Message", foreign_keys=[message_id])

class BlockedUser(Base):
    __tablename__ = "blocked_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blocked_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="blocked_users", foreign_keys=[user_id])
    blocked_user = relationship("User", foreign_keys=[blocked_user_id])

class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    sender = relationship("User", back_populates="friend_requests_sent", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="friend_requests_received", foreign_keys=[receiver_id])

class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    
    # Ensure unique friendship pairs
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='unique_friendship'),
    )

# Create all tables in the database
def create_tables():
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()