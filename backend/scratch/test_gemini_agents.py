import os
import asyncio
from dotenv import load_dotenv
from livekit.plugins import google
from livekit.agents import llm

load_dotenv(".env.local")

async def test_llm():
    agent_llm = google.LLM(model="gemini-3.5-flash-lite")
    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(role="user", content="Hello")
    
    try:
        chat = agent_llm.chat(chat_ctx=chat_ctx)
        async for chunk in chat:
            print("Chunk:", chunk)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_llm())
