import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client.clinic_db

patients_collection = db.patients
appointments_collection = db.appointments

class AppointmentSchema(BaseModel):
    patient_phone: str
    doctor_id: str
    start_time: datetime
    status: str = "Booked"

async def get_patient_language(phone_number: str) -> str:
    """Retrieves the preferred language across sessions."""
    patient = await patients_collection.find_one({"phone_number": phone_number})
    if patient and "preferred_language" in patient:
        return patient["preferred_language"]
    return "en-IN"

async def upsert_patient_language(phone_number: str, language: str):
    """Updates or creates the patient's language preference."""
    await patients_collection.update_one(
        {"phone_number": phone_number},
        {"$set": {"preferred_language": language}},
        upsert=True
    )
    
async def save_appointment_to_db(patient_phone: str, doctor_id: str, time_slot: str):
    """Persists a confirmed appointment."""
    appointment = AppointmentSchema(
        patient_phone=patient_phone,
        doctor_id=doctor_id,
        start_time=datetime.fromisoformat(time_slot)
    )
    await appointments_collection.insert_one(appointment.model_dump())
    logger.info(f"Saved appointment to MongoDB for {patient_phone}")