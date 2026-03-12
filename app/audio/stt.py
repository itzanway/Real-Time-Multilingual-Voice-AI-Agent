import os
import json
import websockets
import asyncio
import logging

logger = logging.getLogger(__name__)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

async def stream_audio_to_text(audio_queue: asyncio.Queue, transcript_queue: asyncio.Queue, preferred_language: str = "en-IN"):
    dg_url = f"wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000&language={preferred_language}&interim_results=false"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}
    
    try:
        async with websockets.connect(dg_url, extra_headers=headers) as ws:
            async def sender():
                while True:
                    chunk = await audio_queue.get()
                    if chunk is None: break
                    await ws.send(chunk)
            
            async def receiver():
                async for msg in ws:
                    res = json.loads(msg)
                    if res.get("is_final"):
                        transcript = res["channel"]["alternatives"][0]["transcript"]
                        if transcript.strip():
                            logger.info(f"User: {transcript}")
                            await transcript_queue.put(transcript)

            await asyncio.gather(sender(), receiver())
    except Exception as e:
        logger.error(f"STT Error: {e}")