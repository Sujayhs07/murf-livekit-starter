import os
import asyncio
from dotenv import load_dotenv
from livekit.plugins import deepgram
from livekit.agents import stt

load_dotenv(".env.local")

async def test_stt():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    print(f"DEEPGRAM_API_KEY starts with: {api_key[:10] if api_key else 'None'}")
    
    try:
        # Initialize Deepgram STT
        dg = deepgram.STT(model="nova-3", language="en")
        print("Deepgram STT initialized successfully.")
    except Exception as e:
        print("Error during Deepgram initialization:", e)

if __name__ == "__main__":
    asyncio.run(test_stt())
