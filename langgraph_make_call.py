"""Make outbound calls using the LangGraph voice travel planning agent"""

import asyncio
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def make_travel_planning_call(phone_number: str = "+000000000000"):
    """
    Make an outbound call to start a travel planning conversation.
    
    Args:
        phone_number: The phone number to call (default: +000000000000)
    """
    livekit_api = api.LiveKitAPI()
    
    # Generate unique room name for this call
    room_name = f"travel-planning-{int(asyncio.get_event_loop().time())}"
    
    # Create SIP participant for outbound call
    request = api.CreateSIPParticipantRequest(
        sip_trunk_id="----",  # Replace with your actual SIP trunk ID
        sip_call_to=phone_number,
        room_name=room_name,
        participant_identity="travel_caller",
        participant_name="Travel Planning Call"
    )
    
    try:
        print(f"🌍 Initiating travel planning call to {phone_number}...")
        print(f"📞 Room: {room_name}")
        print("🤖 The AI travel agent will greet you and help plan your trip!")
        
        participant = await livekit_api.sip.create_sip_participant(request)
        
        print(f"\n📱 Answer the call on {phone_number} to start your travel planning session!")
        
    except Exception as e:
        print(f"❌ Error making call: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Make sure your SIP trunk is configured in LiveKit Cloud")
        print("   2. Verify the SIP trunk ID is correct")
        print("   3. Ensure the phone number format is correct (+country_code_number)")
        print("   4. Check that your LiveKit API credentials are set in .env")
    
    await livekit_api.aclose()

async def make_call_interactive():
    """Interactive version that asks for phone number."""
    print("🌍 LangGraph Travel Planning Voice Agent")
    print("=" * 50)
    
    # Get phone number from user
    phone_number = input("Enter phone number to call (or press Enter for default ): +000000000000 ").strip()
    if not phone_number:
        phone_number = ""
    
    # Validate phone number format
    if not phone_number.startswith("+"):
        print("⚠️  Phone number should start with + and country code")
        phone_number = "+" + phone_number
    
    print(f"\n📞 Calling {phone_number}...")
    await make_travel_planning_call(phone_number)

if __name__ == "__main__":
    # You can run this in two ways:
    # 1. Interactive mode: python langgraph_make_call.py
    # 2. Direct call: uncomment the line below and set the phone number
    
    # For interactive mode:
    asyncio.run(make_call_interactive())
    
    # For direct call (uncomment and modify):

    # asyncio.run(make_travel_planning_call("+1234567890"))
