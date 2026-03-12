from openai import AsyncOpenAI
import os
import json
from app.tools.appointments import check_availability, book_appointment

# Pointing to Groq for sub-450ms latency
client = AsyncOpenAI(
    api_key=os.getenv("FAST_LLM_API_KEY"), 
    base_url="https://api.groq.com/openai/v1" 
)

SYSTEM_PROMPT = """
You are a real-time clinical voice assistant. 
1. Your primary job is booking and managing appointments.
2. You must detect the user's language (English, Hindi, or Tamil) and respond in that same language.
3. Be concise. Long paragraphs cause unacceptable audio latency.
4. Use tools to check availability before confirming any booking. Do not hallucinate times.
"""

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
    Sends transcript to LLM. Evaluates tool calls. Yields text chunks for TTS.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session_history
    messages.append({"role": "user", "content": transcript})
    
    response = await client.chat.completions.create(
        model="llama3-70b-8192", 
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=False # Simplified to handle tool-calling logic cleanly in this skeleton
    )
    
    message = response.choices[0].message
    
    # Check if the LLM wants to call a tool
    if message.tool_calls:
        for tool_call in message.tool_calls:
            if tool_call.function.name == "check_availability":
                args = json.loads(tool_call.function.arguments)
                # Execute the actual Python tool
                result = await check_availability(args["doctor_id"], args["requested_time"])
                
                # In a full implementation, you would append this result to messages 
                # and call the LLM again to generate the audio response.
                yield f"I checked the schedule. {result}"
    else:
        # Standard conversational text
        yield message.content