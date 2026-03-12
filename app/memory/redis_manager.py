import redis.asyncio as redis
import json
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

SESSION_TTL_SECONDS = 3600  # 1 hour TTL 

async def save_session_state(phone_number: str, state_data: dict):
    """Saves the current conversation context with a TTL."""
    key = f"session:{phone_number}"
    await redis_client.setex(
        key,
        SESSION_TTL_SECONDS,
        json.dumps(state_data)
    )

async def get_session_state(phone_number: str) -> dict:
    """Retrieves the active session context if it exists."""
    key = f"session:{phone_number}"
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return {"messages": [], "intent": "UNKNOWN", "pending_action": None}