import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    UserInputTranscribedEvent,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero

logger = logging.getLogger("agent")

load_dotenv(".env.local")

try:
    from prompt import SYSTEM_PROMPT
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.prompt import SYSTEM_PROMPT

try:
    from db import get_caller_by_id_or_name, upsert_caller
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.db import get_caller_by_id_or_name, upsert_caller


class Assistant(Agent):
    def __init__(self, room: rtc.Room) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.room = room

    @function_tool
    async def lookup_caller(self, context: RunContext, name: str | None = None) -> str:
        """Use this tool to look up a caller in the database.
        It returns information about the caller, such as their name, language preference,
        facts about past interactions, and when they last interacted.

        Args:
            name: The caller's name to search for (optional). If not specified, looks up by participant identity.
        """
        user_id = None
        participants = list(self.room.remote_participants.values())
        if participants:
            user_id = participants[0].identity

        logger.info(f"Looking up caller. user_id={user_id}, name={name}")
        caller = get_caller_by_id_or_name(user_id=user_id, name=name)
        if caller:
            logger.info(f"Found caller: {caller}")
            return f"Caller found: {caller}"

        logger.info("Caller not found")
        return "Caller not found."

    @function_tool
    async def save_caller_info(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        schemes_checked: str,
        eligibility_answers: str,
    ) -> str:
        """Use this tool to save or update the caller's profile and facts.
        Only call this tool if the user gave explicit verbal consent to remember/save their data.

        Args:
            name: The caller's name.
            language_preference: The language they prefer (e.g. Hindi, English, Hinglish).
            schemes_checked: The schemes checked/discussed (e.g. PMJDY, PMSBY).
            eligibility_answers: Details about eligibility criteria met or discussed.
        """
        user_id = f"voice_assistant_user_{name.lower()}"
        participants = list(self.room.remote_participants.values())
        if participants:
            user_id = participants[0].identity

        facts = {
            "schemes_checked": schemes_checked,
            "eligibility_answers": eligibility_answers,
        }

        logger.info(
            f"Saving caller info. user_id={user_id}, name={name}, language={language_preference}, facts={facts}"
        )
        upsert_caller(user_id, name, language_preference, facts)
        return "Caller information saved successfully."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-2", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="en-IN-anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
        min_endpointing_delay=0.3,
        max_endpointing_delay=1.0,
        min_interruption_duration=0.2,
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        # Check for Devanagari script characters (native Hindi)
        has_devanagari = any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in transcript)

        # Check for common Hinglish/Hindi romanized keywords
        hindi_keywords = {
            "kya",
            "hai",
            "aur",
            "main",
            "haan",
            "nahin",
            "aap",
            "namaste",
            "shukriya",
            "yojana",
            "batao",
            "bataiye",
            "samjhao",
            "dhan",
            "suraksha",
            "bima",
            "pension",
            "mein",
            "ke",
            "ki",
            "se",
            "ko",
            "ka",
            "jo",
            "toh",
            "bhi",
            "ho",
            "kar",
            "raha",
            "rahi",
            "rha",
            "rhi",
            "mujhe",
            "mera",
            "meri",
            "hum",
            "tum",
            "apna",
            "apni",
            "karke",
            "karo",
            "karna",
            "tha",
            "thi",
            "the",
            "ab",
            "kab",
            "tab",
            "sab",
        }
        words = set(transcript.split())
        has_hindi_words = not words.isdisjoint(hindi_keywords)

        # Helper to safely update TTS voice
        def _set_tts_voice(voice_id: str) -> None:
            try:
                session.tts.update_options(voice=voice_id)
                logger.info(f"TTS voice switched to {voice_id}")
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"Failed to set TTS voice to {voice_id}: {e}")

        if has_devanagari or has_hindi_words:
            logger.info(
                f"Detected Hindi/Hinglish speech: '{ev.transcript}'. Switching TTS to Hindi voice."
            )
            _set_tts_voice("hi-IN-anisha")
        else:
            logger.info(
                f"Detected English speech: '{ev.transcript}'. Switching TTS to English voice."
            )
            _set_tts_voice("en-IN-anisha")

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    logger.info("Initializing AgentSession with voice pipeline")
    try:
        await session.start(
            agent=Assistant(room=ctx.room),
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: (
                        noise_cancellation.BVCTelephony()
                        if params.participant.kind
                        == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                        else noise_cancellation.BVC()
                    ),
                ),
            ),
        )
        logger.info("AgentSession started successfully")
    except Exception as e:
        logger.error(f"Failed to start AgentSession: {e}")
        raise

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
