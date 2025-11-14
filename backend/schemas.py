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