from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Mock database for the sake of the tools logic
# In reality, these would query your PostgreSQL DB asynchronously
MOCK_SCHEDULE = {
    "doc_1": ["2026-03-15T10:00:00", "2026-03-15T11:00:00"],
    "doc_2": ["2026-03-15T14:00:00"]
}

async def check_availability(doctor_id: str, requested_time: str) -> str:
    """Checks if a doctor is available at a specific time."""
    available_slots = MOCK_SCHEDULE.get(doctor_id, [])
    
    if requested_time in available_slots:
        return f"Slot {requested_time} is available for {doctor_id}."
    else:
        # Crucial for the prompt: Offer alternatives [cite: 30]
        return f"Slot unavailable. Available alternatives for {doctor_id} are: {', '.join(available_slots)}."

async def book_appointment(patient_phone: str, doctor_id: str, time_slot: str) -> str:
    """Genuinely books the appointment and prevents double-booking."""
    available_slots = MOCK_SCHEDULE.get(doctor_id, [])
    
    if time_slot not in available_slots:
        return "Booking failed: Time slot is no longer available or invalid."
    
    # Logic to remove the slot from availability and save to DB goes here
    MOCK_SCHEDULE[doctor_id].remove(time_slot)
    logger.info(f"Booked {doctor_id} at {time_slot} for {patient_phone}")
    
    return f"Successfully booked appointment with {doctor_id} at {time_slot}."