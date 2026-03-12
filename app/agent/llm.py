from openai import AsyncOpenAI
import os
import json
from app.tools.appointments import check_availability, book_appointment

# We use the OpenAI SDK but point it to a low-latency provider via base_url
client = AsyncOpenAI(
    api_key=os.getenv("FAST_LLM_API_KEY"), 
    base_url="https://api.groq.com/openai/v1" # Example for Groq
)

SYSTEM_PROMPT = """
You are a real-time clinical voice assistant. 
1. Your primary job is booking and managing appointments.
2. You must detect the user's language (English, Hindi, or Tamil) and respond in that same language.
3. Be concise. You are speaking over audio; long paragraphs cause unacceptable latency.
4. Use tools to check availability before confirming any booking.
"""

# Define the tools schema for the LLM
tools = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check if a doctor is available at a specific time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "string"},
                    "requested_time": {"type": "string", "description": "ISO 8601 format"}
                },
                "required": ["doctor_id", "requested_time"]
            }
        }
    }
]

async def process_user_transcript(transcript: str, session_history: list):
    """
    Sends the transcript to the LLM. 
    Returns an async generator yielding text chunks for the TTS stream.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session_history
    messages.append({"role": "user", "content": transcript})
    
    response = await client.chat.completions.create(
        model="llama3-70b-8192", # Example fast model
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=True
    )
    
    async for chunk in response:
        # If the LLM decides to call a tool, handle it here
        if chunk.choices[0].delta.tool_calls:
            # Execute the python function from app.tools and loop the result back to the LLM
            pass 
            
        # If it's standard text, yield it immediately to the TTS engine
        elif chunk.choices[0].delta.content:
             yield chunk.choices[0].delta.content