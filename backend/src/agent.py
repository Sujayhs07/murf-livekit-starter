import asyncio
import io
import logging
import sys

# Force UTF-8 encoding on Windows to prevent UnicodeEncodeError with Devanagari (Hindi) text
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

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
from livekit.plugins import deepgram, google, murf, silero

logger = logging.getLogger("agent")

load_dotenv(".env.local")

try:
    from prompt import GOVERNMENT_SCHEME_SPECIALIST_PROMPT, SYSTEM_PROMPT
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.prompt import SYSTEM_PROMPT

try:
    from db import get_caller_by_id_or_name, upsert_caller
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.db import get_caller_by_id_or_name, upsert_caller

try:
    import schemes_data
except ImportError:
    # pyrefly: ignore [missing-import]
    from src import schemes_data

try:
    from db_dashboard import add_call_start, record_handoff, update_call_end
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.db_dashboard import (  # type: ignore
        add_call_start,
        update_call_end,
    )


try:
    from tools import AssistantTools
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.tools import AssistantTools


class Assistant(Agent, AssistantTools):
    def __init__(
        self, room: rtc.Room | None = None, session: AgentSession | None = None
    ) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.room = room
        self.agent_session = session
        self.current_language = "English"  # Default to Hindi
        self.call_id = None
        self.call_success = False
        self.success_reason = None
        self.failure_reason = "USER_HANGUP"
        self.escalation_prefix = "FIN"
        self.voice = "Anisha"

    async def on_enter(self) -> None:
        logger.info("Assistant (Dia) entered/resumed session.")
        if self.session:
            # Restore Dia's voice to Anisha
            try:
                self.session.tts.update_options(voice="Anisha")
                logger.info("Dia: voice restored to Anisha.")
            except Exception as e:
                logger.error(f"Dia: failed to update TTS voice to Anisha: {e}")
            if self.room and self.room.local_participant:
                try:
                    await self.room.local_participant.set_metadata("Dia")
                    await self.room.local_participant.set_name("Dia")
                    logger.info("Dia: set name and metadata to Dia")
                except Exception as e:
                    logger.error(f"Dia: failed to set name/metadata: {e}")

    @function_tool
    async def handoff_to_government_scheme_specialist(
        self, context: RunContext
    ) -> Agent:
        """Use this tool to hand off the conversation to Krishna, the Government Scheme Specialist.
        Use this ONLY when the user explicitly gives verbal permission to connect to Krishna, the government scheme specialist.
        Do NOT use this for ordinary financial questions or compound interest/EMI calculations.
        """
        logger.info(f"Dia: Initiating handoff to Krishna. Call ID: {self.call_id}")

        if self.room and self.room.local_participant:
            try:
                await self.room.local_participant.set_metadata("connecting_to_krishna")
                logger.info("Dia: set transition metadata to connecting_to_krishna")
                await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"Dia: failed to set transition metadata: {e}")

        # Initialize userdata if not already set
        try:
            _ = context.session.userdata
        except ValueError:
            context.session.userdata = {}

        # Save current language to session userdata
        context.session.userdata["current_language"] = self.current_language
        context.session.userdata["call_id"] = self.call_id

        # Create Krishna agent dynamically to avoid circular imports at module level
        try:
            from krishna_agent import GovernmentSchemeSpecialist
        except ImportError:
            # pyrefly: ignore [missing-import]
            from src.krishna_agent import GovernmentSchemeSpecialist  # type: ignore

        # Create Krishna agent, passing the chat context copy excluding instructions
        specialist = GovernmentSchemeSpecialist(
            room=self.room, session=context.session, call_id=self.call_id
        )
        specialist._chat_ctx = self.chat_ctx.copy(exclude_instructions=True)

        # Set active agent to Krishna
        context.session.update_agent(specialist)

        return specialist


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    import json

    is_outbound = False
    recipient_name = "User"
    call_type = "scheme_deadline"
    custom_message = ""
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
            is_outbound = metadata.get("is_outbound", False)
            recipient_name = metadata.get("recipient_name", "User")
            call_type = metadata.get("call_type", "scheme_deadline")
            custom_message = metadata.get("custom_message", "")
            logger.info(
                f"Loaded job metadata: is_outbound={is_outbound}, recipient_name={recipient_name}, call_type={call_type}, custom_message={custom_message}"
            )
        except Exception as e:
            logger.error(f"Failed to parse job metadata: {e}")
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
            voice="Anisha",
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
        userdata={},
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.transcript.strip().lower()
        if not transcript:
            return

        # Check for stop request
        stop_keywords = [
            "stop the call",
            "stop calling",
            "opt out",
            "stop",
            "cancel",
            "stop this call",
        ]
        if any(keyword in transcript for keyword in stop_keywords):
            logger.info("User requested to stop/opt-out. Say goodbye and disconnect.")

            async def end_call():
                try:
                    await session.say(
                        "Understood. I will end the call now and update your preferences. Goodbye."
                    )
                    await asyncio.sleep(4.0)
                except Exception as e:
                    logger.error(f"Error during shutdown message: {e}")
                await ctx.room.disconnect()

            asyncio.create_task(end_call())
            return

        # Helper to safely update TTS voice
        def _set_tts_voice(voice_id: str) -> None:
            try:
                session.tts.update_options(voice=voice_id)
                logger.info(f"TTS voice switched to {voice_id}")
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"Failed to set TTS voice to {voice_id}: {e}")

        # Check user language settings from participant metadata
        user_lang = None
        participants = list(ctx.room.remote_participants.values())
        if participants:
            p = participants[0]
            if p.metadata:
                try:
                    import json

                    meta = json.loads(p.metadata)
                    user_lang = meta.get("language")
                except Exception:
                    pass

        active_agent = session.current_agent
        voice_to_set = getattr(active_agent, "voice", "Anisha")

        if user_lang == "hi":
            logger.info("Using language from settings: Hindi.")
            active_agent.current_language = "Hindi"
            _set_tts_voice(voice_to_set)
        elif user_lang == "en":
            logger.info("Using language from settings: English.")
            active_agent.current_language = "English"
            _set_tts_voice(voice_to_set)
        else:
            # Fallback to automatic language detection
            # Check for Devanagari script characters (native Hindi)
            has_devanagari = any(
                ord(c) >= 0x0900 and ord(c) <= 0x097F for c in transcript
            )

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

            if has_devanagari or has_hindi_words:
                logger.info(
                    f"Detected Hindi/Hinglish speech: '{ev.transcript}'. Setting language to Hindi."
                )
                active_agent.current_language = "Hindi"
                _set_tts_voice(voice_to_set)
            else:
                logger.info(
                    f"Detected English speech: '{ev.transcript}'. Setting language to English."
                )
                active_agent.current_language = "English"
                _set_tts_voice(voice_to_set)

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
    assistant = Assistant(room=ctx.room, session=session)

    # Generate unique call ID
    import random
    from datetime import datetime

    year = datetime.now().year
    call_id = f"CALL-{year}-{random.randint(1000, 9999)}"
    assistant.call_id = call_id

    try:
        add_call_start(call_id=call_id, language="English", channel="browser")
    except Exception as e:
        logger.error(f"Failed to record call start in db: {e}")

    start_time = datetime.now()
    disconnect_event = asyncio.Event()

    @ctx.room.on("disconnected")
    def on_room_disconnected():
        logger.info("Room disconnected event received")
        disconnect_event.set()

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant disconnected: {participant.identity}")
        disconnect_event.set()

    try:
        await session.start(
            agent=assistant,
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(),
            ),
        )
        logger.info("AgentSession started successfully")

        # Join the room and connect to the user
        await ctx.connect()

        # Automatically speak initial greeting
        async def greet_user_on_entry():
            try:
                if is_outbound:
                    # Wait for any remote participant to connect/join the room
                    logger.info("Outbound call: waiting for participant to join...")

                    connected_event = asyncio.Event()

                    @ctx.room.on("participant_connected")
                    def on_participant_connected(participant: rtc.RemoteParticipant):
                        logger.info(
                            f"Participant connected event received for: {participant.identity}"
                        )
                        connected_event.set()

                    # Check if participant is already present
                    if len(ctx.room.remote_participants) > 0:
                        logger.info("Participant already present in room.")
                        connected_event.set()

                    try:
                        await asyncio.wait_for(connected_event.wait(), timeout=45.0)
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for participant to join.")
                        return

                    logger.info("Participant joined, speaking greeting.")
                    await asyncio.sleep(
                        2.0
                    )  # Brief delay to let the user put the phone to their ear

                    session.tts.update_options(voice="Anisha")
                    if custom_message:
                        session.say(custom_message)
                    elif call_type == "payment_reminder":
                        session.say(
                            "Namaste! This is Dia calling from Bharat Finance Services. We are calling to remind you that your monthly loan EMI payment is due in three days. "
                            "You can say 'stop the call' or hang up at any time if you'd like to end this call or opt out."
                        )
                    elif call_type == "itr_deadline":
                        session.say(
                            "Namaste! This is Dia calling from the National Financial Literacy Council of India. We are calling to remind you that the deadline for filing your Income Tax Return is approaching on July thirty-first. "
                            "You can say 'stop the call' or hang up at any time if you'd like to end this call or opt out."
                        )
                    else:  # default scheme_deadline
                        session.say(
                            "Namaste! This is Dia calling from the National Financial Literacy Council of India regarding the approaching deadline for the PM-Kisan scheme. "
                            "You can say 'stop the call' or hang up at any time if you'd like to end this call or opt out."
                        )
                    logger.info(
                        f"Spoke outbound welcome greeting for {call_type} on entry"
                    )
                else:
                    await asyncio.sleep(1.0)
                    session.tts.update_options(voice="Anisha")

                    active_tab = "voice"
                    user_lang = "en"
                    participants = list(ctx.room.remote_participants.values())
                    if participants:
                        p = participants[0]
                        if p.metadata:
                            try:
                                import json

                                meta = json.loads(p.metadata)
                                active_tab = meta.get("activeTab", "voice")
                                user_lang = meta.get("language", "en")
                            except Exception:
                                pass

                    if user_lang == "hi":
                        assistant.current_language = "Hindi"
                    elif user_lang == "kn":
                        assistant.current_language = "Kannada"
                    else:
                        assistant.current_language = "English"

                    logger.info(
                        f"Customized greeting based on active tab: {active_tab}, language: {user_lang}"
                    )

                    if assistant.current_language == "Hindi":
                        if active_tab == "finance":
                            session.say(
                                "नमस्ते! मैं दीया हूँ। मैं देख रही हूँ कि आप फाइनेंस डैशबोर्ड पर हैं। यहाँ आप अपना बैलेंस देख सकते हैं और ट्रांजैक्शन कर सकते हैं। क्या आप किसी ट्रांजैक्शन या स्कीम के बारे में जानकारी चाहते हैं?"
                            )
                        elif active_tab == "analytics":
                            session.say(
                                "नमस्ते! मैं दीया हूँ। मैं देख रही हूँ कि आप कॉल एनालिटिक्स पेज पर हैं। यहाँ आप हमारी बातचीत की परफॉर्मेंस और कॉल रिकॉर्ड्स देख सकते हैं। क्या आप इसके बारे में कुछ जानना चाहते हैं?"
                            )
                        elif active_tab == "help":
                            session.say(
                                "नमस्ते! मैं दीया हूँ। मैं देख रही हूँ कि आप हेल्प पेज पर हैं। यहाँ आप मेरे फीचर्स और सपोर्ट गाइड देख सकते हैं। बताइए, आज मैं आपके कौन से सवाल का जवाब दूँ?"
                            )
                        else:
                            session.say(
                                "नमस्ते! मैं दीया हूँ। मुझे अपनी फाइनेंशियल दोस्त समझिए। मैं सरकारी फाइनेंशियल स्कीम्स और सेफ बैंकिंग से जुड़े सवालों में आपकी मदद करने के लिए यहाँ हूँ। बताइए, आज मैं आपकी कैसे मदद कर सकती हूँ? क्या मैं आपका शुभ नाम जान सकती हूँ?"
                            )
                    elif assistant.current_language == "Kannada":
                        if active_tab == "finance":
                            session.say(
                                "ನಮಸ್ತೆ! ನಾನು ದಿಯಾ. ನೀವು ಫೈನಾನ್ಸ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿದ್ದೀರಿ ಎಂದು ನಾನು ನೋಡುತ್ತಿದ್ದೇನೆ. ಇಲ್ಲಿ ನೀವು ನಿಮ್ಮ ಬ್ಯಾಲೆನ್ಸ್ ಅನ್ನು ನೋಡಬಹುದು ಮತ್ತು ವಹಿವಾಟುಗಳನ್ನು ಮಾಡಬಹುದು. ನೀವು ಯಾವುದೇ ವಹಿವಾಟು ಅಥವಾ ಯೋಜನೆಯ ಬಗ್ಗೆ ಮಾಹಿತಿ ಬಯಸುವಿರಾ?"
                            )
                        elif active_tab == "analytics":
                            session.say(
                                "ನಮಸ್ತೆ! ನಾನು ದಿಯಾ. ನೀವು ಕಾಲ್ ಅನಾಲಿಟಿಕ್ಸ್ ಪುಟದಲ್ಲಿದ್ದೀರಿ ಎಂದು ನಾನು ನೋಡುತ್ತಿದ್ದೇನೆ. ಇಲ್ಲಿ ನೀವು ನಮ್ಮ ಸಂಭಾಷಣೆಗಳ ಕಾರ್ಯಕ್ಷಮತೆ ಮತ್ತು ಕಾಲ್ ರೆಕಾರ್ಡ್‌ಗಳನ್ನು ಮೇಲ್ವಿಚಾರಣೆ ಮಾಡಬಹುದು. ನೀವು ಇದರ ಬಗ್ಗೆ ಇನ್ನಷ್ಟು ತಿಳಿಯಲು ಬಯಸುವಿರಾ?"
                            )
                        elif active_tab == "help":
                            session.say(
                                "ನಮಸ್ತೆ! ನಾನು ದಿಯಾ. ನೀವು ಸಹಾಯ ಪುಟದಲ್ಲಿದ್ದೀರಿ ಎಂದು ನಾನು ನೋಡುತ್ತಿದ್ದೇನೆ. ಇಲ್ಲಿ ನೀವು ನನ್ನ ವೈಶಿಷ್ಟ್ಯಗಳು ಮತ್ತು ಬೆಂಬಲ ಮಾರ್ಗದರ್ಶಿಯನ್ನು ಪರಿಶೀಲಿಸಬಹುದು. ದಯವಿಟ್ಟು ಹೇಳಿ, ಇಂದು ನಾನು ನಿಮ್ಮ ಯಾವ ಪ್ರಶ್ನೆಗೆ ಉತ್ತರಿಸಬೇಕು?"
                            )
                        else:
                            session.say(
                                "ನಮಸ್ತೆ! ನಾನು ದಿಯಾ, ನಿಮ್ಮ ಹಣಕಾಸು ಸಹಾಯಕರು. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು, ಲೆಕ್ಕಾಚಾರಗಳು ಮತ್ತು ಸುರಕ್ಷಿತ ಬ್ಯಾಂಕಿಂಗ್ ಮಾರ್ಗಸೂಚಿಗಳೊಂದಿಗೆ ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ನಾನು ಇಲ್ಲಿದ್ದೇನೆ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು? ನಿಮ್ಮ ಹೆಸರನ್ನು ನಾನು ತಿಳಿಯಬಹುದೇ?"
                            )
                    else:
                        if active_tab == "finance":
                            session.say(
                                "Hello! I am Dia. I see that you are on the Finance Dashboard. Here you can view your balance and perform transactions. Would you like some information on a transaction or scheme?"
                            )
                        elif active_tab == "analytics":
                            session.say(
                                "Hello! I am Dia. I see that you are on the Call Analytics page. Here you can monitor the performance of our conversations and call records. Would you like to know more about this?"
                            )
                        elif active_tab == "help":
                            session.say(
                                "Hello! I am Dia. I see that you are on the Help page. Here you can check my features and support guide. Please tell me, which of your questions should I answer today?"
                            )
                        else:
                            session.say(
                                "Hello! I am Dia, your financial assistant. I am here to help you with government schemes, calculations, and safe banking guidelines. How can I help you today? May I know your name?"
                            )
                    logger.info("Spoke inbound welcome greeting to user on entry")
            except Exception as err:
                logger.error(f"Failed to speak welcome greeting: {err}")

        asyncio.create_task(greet_user_on_entry())

        # Wait for the room disconnect event
        await disconnect_event.wait()

    finally:
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        outcome = "SUCCESS" if assistant.call_success else "FAILED"
        lang = assistant.current_language
        failure_reason = (
            assistant.failure_reason if not assistant.call_success else None
        )
        success_reason = assistant.success_reason if assistant.call_success else None

        logger.info(
            f"Recording call end: {call_id}, duration={duration}s, outcome={outcome}, lang={lang}"
        )
        try:
            update_call_end(
                call_id=call_id,
                duration_seconds=duration,
                outcome=outcome,
                language=lang,
                failure_reason=failure_reason,
                success_reason=success_reason,
            )
        except Exception as e:
            logger.error(f"Failed to update call end in db: {e}")


if __name__ == "__main__":
    cli.run_app(server)
