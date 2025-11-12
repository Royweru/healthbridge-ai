# backend/routes/appointments.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.models import models
from backend.models.models import AppointmentSchema, AppointmentCreate, get_db

router = APIRouter(
    prefix="/api/appointments",
    tags=["Appointments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", 
             response_model=AppointmentSchema, 
             status_code=201,
             summary="Schedule a New Appointment")
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    """
    Creates a new appointment for a patient.
    
    - **patient_id**: The ID of the patient for whom the appointment is being booked.
    - **appointment_time**: The scheduled time for the appointment (in ISO 8601 format).
    - **reason**: The reason for the visit.
    """
    # Check if patient exists
    db_patient = db.query(models.Patient).filter(models.Patient.id == appointment.patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail=f"Patient with ID {appointment.patient_id} not found.")
        
    db_appointment = models.Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@router.get("/", 
            response_model=List[AppointmentSchema],
            summary="List All Appointments")
def read_appointments(
    patient_id: Optional[int] = Query(None, description="Filter appointments by patient ID"),
    start_date: Optional[datetime] = Query(None, description="Filter appointments from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter appointments up to this date"),
    status: Optional[str] = Query(None, description="Filter by appointment status (scheduled, completed, canceled)"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of appointments with optional filtering and pagination.
    """
    query = db.query(models.Appointment)
    
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if start_date:
        query = query.filter(models.Appointment.appointment_time >= start_date)
    if end_date:
        query = query.filter(models.Appointment.appointment_time <= end_date)
    if status:
        query = query.filter(models.Appointment.status == status)
        
    appointments = query.offset(skip).limit(limit).all()
    return appointments

@router.get("/{appointment_id}", 
            response_model=AppointmentSchema,
            summary="Get a Specific Appointment")
def read_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """
    Retrieves details of a single appointment by its ID.
    """
    db_appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appointment

@router.put("/{appointment_id}", 
            response_model=AppointmentSchema,
            summary="Update an Appointment")
def update_appointment(appointment_id: int, appointment: AppointmentCreate, db: Session = Depends(get_db)):
    """
    Updates the details of an existing appointment (e.g., reschedule or change reason).
    """
    db_appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    update_data = appointment.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
        
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@router.delete("/{appointment_id}", 
               status_code=204,
               summary="Cancel an Appointment")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """
    Deletes an appointment (or marks it as canceled).
    
    For this implementation, we will change the status to 'canceled' instead of deleting the record.
    """
    db_appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if db_appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if db_appointment.status == 'canceled':
        raise HTTPException(status_code=400, detail="Appointment is already canceled.")

    db_appointment.status = 'canceled'
    db.add(db_appointment)
    db.commit()
    # No content is returned for a 204 response
    return 
