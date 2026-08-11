import { NextResponse } from 'next/server';
import { SipClient, AgentDispatchClient } from 'livekit-server-sdk';

const LIVEKIT_URL = process.env.LIVEKIT_URL;
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const TRUNK_ID = process.env.LIVEKIT_SIP_OUTBOUND_TRUNK_ID;
const LINPHONE_USERNAME = process.env.LINPHONE_USERNAME;

export async function POST(req: Request) {
  try {
    if (!LIVEKIT_URL || !API_KEY || !API_SECRET || !TRUNK_ID || !LINPHONE_USERNAME) {
      throw new Error('Missing server credentials or configurations. Please set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_SIP_OUTBOUND_TRUNK_ID and LINPHONE_USERNAME.');
    }

    const { target, callType, customMessage } = await req.json();

    if (!target) {
      return NextResponse.json({ error: 'Target is required' }, { status: 400 });
    }

    // Clean target (strip sip: and @domain)
    let cleanTarget = target.trim();
    if (cleanTarget.toLowerCase().startsWith('sip:')) {
      cleanTarget = cleanTarget.substring(4);
    }
    if (cleanTarget.includes('@')) {
      cleanTarget = cleanTarget.split('@')[0];
    }

    const roomName = `outbound_room_${Math.floor(Math.random() * 9000) + 1000}`;
    const agentName = 'my-agent';

    // 1. Dispatch the agent
    const dispatchClient = new AgentDispatchClient(LIVEKIT_URL, API_KEY, API_SECRET);
    const metadata = JSON.stringify({
      is_outbound: true,
      recipient_name: 'Valued Customer',
      call_type: callType || 'scheme_deadline',
      custom_message: customMessage || '',
    });
    
    console.log(`Dispatching agent ${agentName} to room ${roomName}`);
    await dispatchClient.createDispatch(roomName, agentName, { metadata });

    // Wait a brief moment for agent worker to warm up
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // 2. Trigger the SIP call
    const sipClient = new SipClient(LIVEKIT_URL, API_KEY, API_SECRET);
    const sipNumber = `sip:${LINPHONE_USERNAME}`;
    const participantIdentity = `sip_user_${Math.floor(Math.random() * 900) + 100}`;
    
    console.log(`Dialing ${cleanTarget} from ${sipNumber} with trunk ${TRUNK_ID}`);
    const participant = await sipClient.createSipParticipant(TRUNK_ID, cleanTarget, roomName, {
      fromNumber: sipNumber,
      participantIdentity,
      participantName: 'SIP Callee',
      waitUntilAnswered: true,
    });

    return NextResponse.json({
      success: true,
      roomName,
      participantId: participant.participantId || participant.participantIdentity,
    });
  } catch (error) {
    console.error('Outbound call failed:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
