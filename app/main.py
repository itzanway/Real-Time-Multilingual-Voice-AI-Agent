from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import logging

from app.memory.redis_manager import get_session_state, save_session_state
from app.audio.stt import stream_audio_to_text
from app.audio.tts import stream_text_to_audio
from app.agent.llm import process_user_transcript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice AI Agent")

@app.websocket("/ws/voice/{phone_number}")
async def voice_websocket_endpoint(websocket: WebSocket, phone_number: str):
    await websocket.accept()
    
    # 1. Fetch State
    session_state = await get_session_state(phone_number)
    # In a real app, you'd query PostgreSQL here to get `preferred_language`
    preferred_language = "en-IN" 

    # 2. Setup Async Queues to pipe data between components
    audio_in_queue = asyncio.Queue()
    transcript_queue = asyncio.Queue()
    text_out_queue = asyncio.Queue()
    audio_out_queue = asyncio.Queue()

    # 3. Define the LLM Worker Task
    async def llm_worker():
        while True:
            transcript = await transcript_queue.get()
            session_state["messages"].append({"role": "user", "content": transcript})
            
            # This is where we capture and log reasoning traces 
            logger.info(f"--- REASONING TRACE START ({phone_number}) ---")
            logger.info(f"Current State: {session_state.get('intent', 'UNKNOWN')}")
            
            agent_reply = ""
            async for text_chunk in process_user_transcript(transcript, session_state["messages"]):
                agent_reply += text_chunk
                await text_out_queue.put(text_chunk)
            
            logger.info(f"Agent decided to say: {agent_reply}")
            logger.info(f"--- REASONING TRACE END ---")
            
            session_state["messages"].append({"role": "assistant", "content": agent_reply})
            await save_session_state(phone_number, session_state)

    # 4. Define the WebSocket I/O Tasks
    async def receive_from_client():
        try:
            while True:
                data = await websocket.receive_bytes()
                await audio_in_queue.put(data)
        except WebSocketDisconnect:
            await audio_in_queue.put(None) # Signal to stop

    async def send_to_client():
        while True:
            audio_bytes = await audio_out_queue.get()
            await websocket.send_bytes(audio_bytes)

    # 5. Run everything concurrently
    try:
        await asyncio.gather(
            receive_from_client(),
            send_to_client(),
            stream_audio_to_text(audio_in_queue, transcript_queue, preferred_language),
            llm_worker(),
            stream_text_to_audio(text_out_queue, audio_out_queue)
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}")