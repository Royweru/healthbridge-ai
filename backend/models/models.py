# backend/models/models.py

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DEBUG: DATABASE_URL is set to '{DATABASE_URL}'")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy ORM Models ---

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(25), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    language = Column(String(10), default='en')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    appointments = relationship("Appointment", back_populates="patient")
    messages = relationship("Message", back_populates="patient")

    def __repr__(self):
        return f"<Patient(id={self.id}, phone='{self.phone_number}')>"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    appointment_time = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum('scheduled', 'completed', 'canceled', name='appointment_status_enum'), default='scheduled')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, time='{self.appointment_time}')>"

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    role = Column(Text, nullable=False)
    status = Column(Enum('active', 'inactive', 'maintenance', name='agent_status_enum'), default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}')>"

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(100), index=True)
    sender = Column(String(50), nullable=False) # 'patient' or agent's name
    content = Column(Text, nullable=False)
    translated_content = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, sender='{self.sender}', session='{self.session_id}')>"

# --- Pydantic Schemas for API validation ---

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PatientBase(BaseModel):
    phone_number: str
    name: Optional[str] = None
    language: Optional[str] = 'en'

class PatientCreate(PatientBase):
    pass

class PatientSchema(PatientBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class AppointmentBase(BaseModel):
    patient_id: int
    appointment_time: datetime
    reason: Optional[str] = None
    status: Optional[str] = 'scheduled'

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentSchema(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AgentBase(BaseModel):
    name: str
    role: str
    status: Optional[str] = 'active'

class AgentSchema(AgentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        
class MessageBase(BaseModel):
    session_id: str
    sender: str
    content: str

class MessageSchema(MessageBase):
    id: int
    patient_id: Optional[int] = None
    timestamp: datetime

    class Config:
        orm_mode = True

# Helper function to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create all tables
def create_db_and_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")

if __name__ == "__main__":
    print("Creating database and tables...")
    create_db_and_tables()
    print("Done.")
