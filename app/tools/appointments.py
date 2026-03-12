import logging

logger = logging.getLogger(__name__)

# Mock database mapping doctor IDs to available ISO 8601 time slots
MOCK_SCHEDULE = {
    "dr_smith": ["2026-03-15T10:00:00", "2026-03-15T11:00:00"],
    "dr_patel": ["2026-03-15T14:00:00"]
}

async def check_availability(doctor_id: str, requested_time: str) -> str:
    """Checks if a doctor is available at a specific time."""
    available_slots = MOCK_SCHEDULE.get(doctor_id, [])
    
    if requested_time in available_slots:
        return f"Slot {requested_time} is available for {doctor_id}."
    else:
        # Crucial: Offer alternatives for graceful conflict resolution
        return f"Slot unavailable. Available alternatives for {doctor_id} are: {', '.join(available_slots)}."

async def book_appointment(patient_phone: str, doctor_id: str, time_slot: str) -> str:
    """Genuinely books the appointment and prevents double-booking."""
    available_slots = MOCK_SCHEDULE.get(doctor_id, [])
    
    if time_slot not in available_slots:
        return "Booking failed: Time slot is no longer available."
    
    # Remove from availability (prevent double booking)
    MOCK_SCHEDULE[doctor_id].remove(time_slot)
    logger.info(f"Booked {doctor_id} at {time_slot} for {patient_phone}")
    
    return f"Successfully booked appointment with {doctor_id} at {time_slot}."