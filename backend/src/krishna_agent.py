import asyncio
import logging

from livekit.agents import Agent, RunContext, function_tool

try:
    from prompt import GOVERNMENT_SCHEME_SPECIALIST_PROMPT
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.prompt import GOVERNMENT_SCHEME_SPECIALIST_PROMPT

try:
    from db_dashboard import record_handoff
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.db_dashboard import record_handoff  # type: ignore

try:
    from agent import Assistant, get_voice_for_agent
except ImportError:
    # pyrefly: ignore [missing-import]
    from src.agent import Assistant, get_voice_for_agent

logger = logging.getLogger("agent.krishna")


class GovernmentSchemeSpecialist(Assistant):
    def __init__(self, room=None, session=None, call_id=None) -> None:
        super().__init__(room=room, session=session)
        self._instructions = GOVERNMENT_SCHEME_SPECIALIST_PROMPT
        self.call_id = call_id
        self.escalation_prefix = "KRI"
        self.voice = "en-IN-rohan"
        # Filter out self-handoff tool so Krishna cannot trigger a handoff to himself
        self._tools = [
            t
            for t in self._tools
            if t.info.name != "handoff_to_government_scheme_specialist"
        ]

    async def on_enter(self) -> None:
        logger.info("GovernmentSchemeSpecialist (Krishna) entered session.")
        if self.session:
            self.current_language = self.session.userdata.get(
                "current_language", "English"
            )
            self.call_id = self.session.userdata.get("call_id", self.call_id)

            voice_id = get_voice_for_agent(self.__class__.__name__, self.current_language)
            try:
                self.session.tts.update_options(voice=voice_id)
                logger.info(f"Krishna: voice updated to {voice_id}.")
            except Exception as e:
                logger.error(f"Krishna: failed to update TTS voice to {voice_id}: {e}")

            if self.room and self.room.local_participant:
                try:
                    await self.room.local_participant.set_metadata("Krishna")
                    await self.room.local_participant.set_name("Krishna")
                    logger.info("Krishna: set name and metadata to Krishna")
                except Exception as e:
                    logger.error(f"Krishna: failed to set name/metadata: {e}")

            # Log the handoff event in DB
            try:
                if self.call_id:
                    record_handoff(
                        self.call_id, "Krishna", "Government Scheme Specialist"
                    )
                    logger.info(f"Handoff logged to database for call {self.call_id}")
            except Exception as e:
                logger.error(f"Krishna: failed to log handoff in DB: {e}")

    @function_tool
    async def handoff_to_dia(self, context: RunContext) -> Agent:
        """Use this tool to hand the conversation back to Dia, the main financial assistant.
        Use this when the user changes the topic from government schemes to general financial questions (e.g. loans, credit cards, stock markets, general insurance, tax planning, budgeting, compound interest on private savings, etc.).
        """
        logger.info(f"Krishna: Initiating back-handoff to Dia. Call ID: {self.call_id}")

        if self.room and self.room.local_participant:
            try:
                await self.room.local_participant.set_metadata("connecting_to_dia")
                logger.info("Krishna: set transition metadata to connecting_to_dia")
                await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"Krishna: failed to set transition metadata: {e}")

        # Initialize userdata if not already set
        try:
            _ = context.session.userdata
        except ValueError:
            context.session.userdata = {}

        # Save current language to session userdata
        context.session.userdata["current_language"] = self.current_language
        context.session.userdata["call_id"] = self.call_id

        # Create Dia agent
        from agent import Assistant as MainAssistant

        dia = MainAssistant(room=self.room, session=context.session)
        dia.call_id = self.call_id
        dia.current_language = self.current_language
        dia._chat_ctx = self.chat_ctx.copy(exclude_instructions=True)

        # Set active agent to Dia
        context.session.update_agent(dia)

        # Update database with transition back to Dia
        try:
            if self.call_id:
                record_handoff(self.call_id, "Dia")
                logger.info(f"Back-handoff logged to database for call {self.call_id}")
        except Exception as e:
            logger.error(f"Krishna: failed to log back-handoff: {e}")

        return dia
