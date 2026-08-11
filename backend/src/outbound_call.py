import asyncio
import os
import random
import json
from dotenv import load_dotenv
from livekit import api

# Load env variables from .env.local
load_dotenv(".env.local")

async def main():
    # LiveKit Credentials
    lk_url = os.getenv("LIVEKIT_URL")
    lk_key = os.getenv("LIVEKIT_API_KEY")
    lk_secret = os.getenv("LIVEKIT_API_SECRET")

    # Linphone/SIP Configuration
    linphone_sip_domain = os.getenv("LINPHONE_SIP_DOMAIN", "sip.linphone.org")
    call_type = os.getenv("CALL_TYPE", "scheme_deadline") # Options: scheme_deadline, payment_reminder, itr_deadline
    linphone_username = os.getenv("LINPHONE_USERNAME")
    linphone_password = os.getenv("LINPHONE_PASSWORD")
    target_phone_number = os.getenv("TARGET_PHONE_NUMBER")
    if not target_phone_number and linphone_username:
        target_phone_number = linphone_username

    # Clean target_phone_number to get just the SIP user or phone number (no 'sip:' prefix or '@domain')
    clean_target = target_phone_number or ""
    if clean_target.lower().startswith("sip:"):
        clean_target = clean_target[4:]
    if "@" in clean_target:
        clean_target = clean_target.split("@")[0]

    # Check for missing required config
    missing = []
    if not lk_url: missing.append("LIVEKIT_URL")
    if not lk_key: missing.append("LIVEKIT_API_KEY")
    if not lk_secret: missing.append("LIVEKIT_API_SECRET")
    if not linphone_username: missing.append("LINPHONE_USERNAME")
    if not linphone_password: missing.append("LINPHONE_PASSWORD")
    if not clean_target: missing.append("TARGET_PHONE_NUMBER")

    if missing:
        print(f"Error: Missing required variables in .env.local: {', '.join(missing)}")
        print("Please configure them and try again.")
        return

    # For Linphone, the SIP outbound number format is sip:<username>
    linphone_sip_number = f"sip:{linphone_username}"
    # Try to load existing trunk ID from environment first
    trunk_id = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")

    print("Connecting to LiveKit API...")
    lkapi = api.LiveKitAPI(lk_url, lk_key, lk_secret)
    try:
        if trunk_id:
            print(f"Using configured LiveKit Outbound Trunk ID: {trunk_id}")
        else:
            # 1. Search for an existing outbound trunk
            print("Checking existing outbound trunks...")
            trunks = await lkapi.sip.list_sip_outbound_trunk(api.ListSIPOutboundTrunkRequest())
            for t in trunks.items:
                if t.name == "Linphone Outbound Trunk" or t.address == linphone_sip_domain:
                    trunk_id = t.sip_trunk_id
                    print(f"Found existing trunk: ID={trunk_id}, Name={t.name}")
                    break

            # 2. Create the trunk if not found
            if not trunk_id:
                print("No matching trunk found. Creating 'Linphone Outbound Trunk'...")
                request = api.CreateSIPOutboundTrunkRequest(
                    trunk=api.SIPOutboundTrunkInfo(
                        name="Linphone Outbound Trunk",
                        address=linphone_sip_domain,
                        transport=api.SIPTransport.SIP_TRANSPORT_TLS,
                        auth_username=linphone_username,
                        auth_password=linphone_password,
                        numbers=[linphone_sip_number]
                    )
                )
                new_trunk = await lkapi.sip.create_sip_outbound_trunk(request)
                trunk_id = new_trunk.sip_trunk_id
                print(f"Trunk created successfully! Trunk ID: {trunk_id}")

        # Generate a unique room name
        room_name = f"outbound_room_{random.randint(1000, 9999)}"
        print(f"Generated room name: {room_name}")

        # 3. Explicitly dispatch the agent to the room with metadata
        print("Dispatching agent to room...")
        dispatch_request = api.CreateAgentDispatchRequest(
            agent_name="my-agent",
            room=room_name,
            metadata=json.dumps({
                "is_outbound": True,
                "recipient_name": "Valued Customer",
                "call_type": call_type
            })
        )
        dispatch = await lkapi.agent_dispatch.create_dispatch(dispatch_request)
        print(f"Agent dispatched! Job ID: {dispatch.id}")

        # Wait a brief moment for the agent to initialize/spin up
        await asyncio.sleep(1.5)

        # 4. Create the SIP participant to dial the target number
        print(f"Dialing {clean_target} from {linphone_sip_number}...")
        call_request = api.CreateSIPParticipantRequest(
            sip_call_to=clean_target,
            sip_number=linphone_sip_number,
            room_name=room_name,
            participant_identity=f"sip_user_{random.randint(100, 999)}",
            participant_name="SIP Callee",
            sip_trunk_id=trunk_id,
            wait_until_answered=True
        )
        
        participant = await lkapi.sip.create_sip_participant(call_request)
        print(f"Call initiated successfully! SIP Participant ID: {participant.participant_id}")
        print("The agent should speak to the user once they pick up the call.")

    except Exception as e:
        print(f"Error during outbound call initiation: {e}")
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())
