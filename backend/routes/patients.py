# backend/routes/patients.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.models import models
from backend.models.models import PatientSchema, PatientCreate, get_db

router = APIRouter(
    prefix="/api/patients",
    tags=["Patients"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", 
             response_model=PatientSchema, 
             status_code=201,
             summary="Register a New Patient")
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """
    Creates a new patient record in the database.
    
    - **phone_number**: The patient's unique phone number (must include country code).
    - **name**: The patient's full name.
    - **language**: The patient's preferred language (e.g., 'en', 'sw').
    """
    db_patient = db.query(models.Patient).filter(models.Patient.phone_number == patient.phone_number).first()
    if db_patient:
        raise HTTPException(status_code=400, detail="Patient with this phone number already registered.")
    
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.get("/", 
            response_model=List[PatientSchema],
            summary="List All Patients")
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieves a list of all patient records with pagination.
    """
    patients = db.query(models.Patient).offset(skip).limit(limit).all()
    return patients

@router.get("/{patient_id}", 
            response_model=PatientSchema,
            summary="Get a Specific Patient")
def read_patient(patient_id: int, db: Session = Depends(get_db)):
    """
    Retrieves details of a single patient by their unique ID.
    """
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@router.put("/{patient_id}", 
            response_model=PatientSchema,
            summary="Update Patient Details")
def update_patient(patient_id: int, patient: PatientCreate, db: Session = Depends(get_db)):
    """
    Updates the information of an existing patient.
    """
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    update_data = patient.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_patient, key, value)
        
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.delete("/{patient_id}", 
               response_model=PatientSchema,
               summary="Delete a Patient")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """
    Deletes a patient record from the database.
    
    Note: In a real-world scenario, you might prefer to soft-delete (mark as inactive) 
    instead of hard-deleting records to preserve data integrity.
    """
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    db.delete(db_patient)
    db.commit()
    return db_patient
