"""Voice-enabled LangGraph travel planning agent with LiveKit integration"""

from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph, END
import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google, cartesia, deepgram, noise_cancellation

# Load environment variables
load_dotenv()

class TravelState(TypedDict):
    budget: Optional[int]
    activities: List[str]
    preference: Optional[str]
    flight_options: List[Dict]
    hotel_options: List[Dict]
    itinerary: Optional[str]
    summary: Optional[str]
    current_step: str
    user_message: Optional[str]
    agent_response: Optional[str]

# Initialize the LLM with proper API key handling
def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.7
    )

class TravelPlanningAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful AI travel planning assistant. 
            You will help users plan their perfect trip by gathering information about their budget, 
            preferred activities, and travel style, then create a personalized travel plan.
            
            Be conversational, friendly, and helpful. Ask one question at a time and wait for responses.
            """
        )
        self.travel_state = TravelState(
            budget=None,
            activities=[],
            preference=None,
            flight_options=[],
            hotel_options=[],
            itinerary=None,
            summary=None,
            current_step="greeting",
            user_message=None,
            agent_response=None
        )
        self.graph = self.create_graph()

    def create_graph(self):
        """Creates the LangGraph workflow for voice travel planning."""
        builder = StateGraph(TravelState)
        
        # Add nodes
        builder.add_node("greeting", self.greeting_agent)
        builder.add_node("budget_collection", self.budget_collection_agent)
        builder.add_node("activities_collection", self.activities_collection_agent)
        builder.add_node("preference_collection", self.preference_collection_agent)
        builder.add_node("flight_search", self.flight_search_agent)
        builder.add_node("hotel_search", self.hotel_search_agent)
        builder.add_node("itinerary_generator", self.itinerary_generator_agent)
        builder.add_node("summary", self.summary_agent)
        builder.add_node("final_presentation", self.final_presentation_agent)
        
        # Define conditional flow
        builder.set_entry_point("greeting")
        builder.add_edge("greeting", "budget_collection")
        builder.add_edge("budget_collection", "activities_collection")
        builder.add_edge("activities_collection", "preference_collection")
        builder.add_edge("preference_collection", "flight_search")
        builder.add_edge("flight_search", "hotel_search")
        builder.add_edge("hotel_search", "itinerary_generator")
        builder.add_edge("itinerary_generator", "summary")
        builder.add_edge("summary", "final_presentation")
        builder.add_edge("final_presentation", END)

        return builder.compile()

    def greeting_agent(self, state: TravelState):
        """Initial greeting and introduction."""
        response = """Hello! I'm your AI travel planning assistant. I'm excited to help you plan your perfect trip! 
        
        I'll need to gather some information about your preferences to create a personalized travel plan for you. 
        
        Let's start with your budget. What's your total budget for this trip?"""
        
        return {
            "current_step": "budget_collection",
            "agent_response": response
        }

    def budget_collection_agent(self, state: TravelState):
        """Collects and validates budget information."""
        user_input = state.get("user_message", "")
        
        # Try to extract budget from user input
        llm = get_llm()
        prompt = f"""
        The user said: "{user_input}" when asked about their travel budget.
        
        Extract the budget amount if mentioned. If they gave a number, return just the number.
        If they asked a question or need clarification, provide a helpful response and ask for their budget again.
        If unclear, ask them to specify their budget in dollars.
        
        Format your response as either:
        BUDGET: [number] (if you found a budget)
        RESPONSE: [your response] (if you need to ask again)
        """
        
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            if content.startswith("BUDGET:"):
                budget_str = content.replace("BUDGET:", "").strip()
                try:
                    budget = int(budget_str)
                    return {
                        "budget": budget,
                        "current_step": "activities_collection",
                        "agent_response": f"Perfect! ${budget} is a great budget to work with. Now, what activities do you enjoy when traveling? For example, museums, hiking, beaches, food tours, nightlife, or shopping?"
                    }
                except ValueError:
                    pass
            
            # If we couldn't extract a budget, ask again
            return {
                "current_step": "budget_collection",
                "agent_response": content.replace("RESPONSE:", "").strip() if content.startswith("RESPONSE:") else "I'd like to understand your budget better. Could you tell me how much you're planning to spend on this trip in dollars?"
            }
            
        except Exception as e:
            return {
                "current_step": "budget_collection",
                "agent_response": "I'd love to help you plan your trip! Could you tell me your total budget for this trip?"
            }

    def activities_collection_agent(self, state: TravelState):
        """Collects preferred activities."""
        user_input = state.get("user_message", "")
        
        llm = get_llm()
        prompt = f"""
        The user said: "{user_input}" when asked about their preferred travel activities.
        
        Extract the activities they mentioned and provide an encouraging response.
        If they seem unsure, suggest some popular activities.
        
        Format as: ACTIVITIES: [activity1, activity2, ...] | RESPONSE: [your response]
        """
        
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            # Extract activities
            activities = []
            if "ACTIVITIES:" in content:
                activities_part = content.split("ACTIVITIES:")[1].split("|")[0].strip()
                activities = [act.strip() for act in activities_part.split(",")]
            
            # Get response
            response_part = content.split("RESPONSE:")[1].strip() if "RESPONSE:" in content else "Great choices!"
            
            return {
                "activities": activities,
                "current_step": "preference_collection",
                "agent_response": f"{response_part} Now, do you prefer luxury experiences with premium accommodations and services, or are you more budget-conscious looking for good value options?"
            }
            
        except Exception as e:
            return {
                "current_step": "activities_collection",
                "agent_response": "What kind of activities do you enjoy? For example: sightseeing, adventure sports, cultural experiences, food and dining, or relaxation?"
            }

    def preference_collection_agent(self, state: TravelState):
        """Collects travel style preference."""
        user_input = state.get("user_message", "")
        
        llm = get_llm()
        prompt = f"""
        The user said: "{user_input}" when asked about luxury vs budget travel preferences.
        
        Determine if they prefer "luxury" or "economy" based on their response.
        
        Format as: PREFERENCE: [luxury/economy] | RESPONSE: [acknowledgment]
        """
        
        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            
            preference = "economy"  # default
            if "PREFERENCE:" in content:
                pref_part = content.split("PREFERENCE:")[1].split("|")[0].strip().lower()
                if "luxury" in pref_part:
                    preference = "luxury"
            
            return {
                "preference": preference,
                "current_step": "processing",
                "agent_response": "Perfect! I have all the information I need. Let me create your personalized travel plan. This will take just a moment..."
            }
            
        except Exception as e:
            return {
                "current_step": "preference_collection",
                "agent_response": "Would you prefer luxury accommodations and experiences, or are you looking for more budget-friendly options?"
            }

    def flight_search_agent(self, state: TravelState):
        """Generates flight options based on preferences."""
        llm = get_llm()
        
        prompt = f"""
        Generate 2-3 realistic flight options for a trip with:
        - Budget: ${state['budget']}
        - Preference: {state['preference']}
        
        Provide airline names, prices, and durations that fit the budget and preference.
        """
        
        try:
            response = llm.invoke(prompt)
            # Create structured flight options
            base_price = min(400, state['budget'] // 3) if state['preference'] == 'economy' else min(600, state['budget'] // 2)
            flight_options = [
                {"airline": "Budget Airways", "price": base_price, "duration": "8 hours"},
                {"airline": "Premium Airlines", "price": base_price + 200, "duration": "6 hours"},
            ]
        except Exception as e:
            flight_options = [
                {"airline": "Standard Airlines", "price": 500, "duration": "7 hours"}
            ]
        
        return {"flight_options": flight_options}

    def hotel_search_agent(self, state: TravelState):
        """Generates hotel options based on preferences."""
        base_price = 80 if state['preference'] == 'economy' else 200
        hotel_options = [
            {"hotel": "City Center Hotel", "price": base_price, "rating": 4},
            {"hotel": "Premium Resort", "price": base_price + 100, "rating": 5},
        ]
        
        return {"hotel_options": hotel_options}

    def itinerary_generator_agent(self, state: TravelState):
        """Generates personalized itinerary."""
        llm = get_llm()
        
        prompt = f"""
        Create a concise 3-day travel itinerary for:
        - Budget: ${state['budget']}
        - Activities: {', '.join(state['activities'])}
        - Style: {state['preference']}
        
        Keep it brief but engaging. Include specific attractions and activities.
        Format as Day 1, Day 2, Day 3.
        """
        
        try:
            response = llm.invoke(prompt)
            itinerary = response.content
        except Exception as e:
            itinerary = "Day 1: City exploration and local cuisine\nDay 2: Main attractions and cultural sites\nDay 3: Leisure activities and shopping"
        
        return {"itinerary": itinerary}

    def summary_agent(self, state: TravelState):
        """Creates travel plan summary."""
        llm = get_llm()
        
        prompt = f"""
        Create a brief travel summary highlighting:
        - Budget: ${state['budget']}
        - Best flight option: {state['flight_options'][0] if state['flight_options'] else 'Standard option'}
        - Recommended hotel: {state['hotel_options'][0] if state['hotel_options'] else 'Standard hotel'}
        - Key highlights from the itinerary
        
        Keep it concise and exciting.
        """
        
        try:
            response = llm.invoke(prompt)
            summary = response.content
        except Exception as e:
            summary = f"Your ${state['budget']} travel plan includes flights, accommodation, and activities tailored to your {state['preference']} preferences."
        
        return {"summary": summary}

    def final_presentation_agent(self, state: TravelState):
        """Presents the final travel plan."""
        response = f"""Here's your personalized travel plan!

        {state['summary']}

        Your 3-day itinerary:
        {state['itinerary']}

        I hope you have an amazing trip! Is there anything specific you'd like me to adjust or explain further about your travel plan?"""
        
        return {
            "current_step": "complete",
            "agent_response": response
        }

    async def process_user_input(self, message: str, session: AgentSession):
        """Process user input through the LangGraph workflow."""
        # Update state with user message
        self.travel_state["user_message"] = message
        
        # Run the appropriate step based on current state
        current_step = self.travel_state.get("current_step", "greeting")
        
        if current_step == "greeting":
            result = self.greeting_agent(self.travel_state)
        elif current_step == "budget_collection":
            result = self.budget_collection_agent(self.travel_state)
        elif current_step == "activities_collection":
            result = self.activities_collection_agent(self.travel_state)
        elif current_step == "preference_collection":
            result = self.preference_collection_agent(self.travel_state)
        elif current_step == "processing":
            # Run the full workflow for planning
            result = self.flight_search_agent(self.travel_state)
            self.travel_state.update(result)
            result = self.hotel_search_agent(self.travel_state)
            self.travel_state.update(result)
            result = self.itinerary_generator_agent(self.travel_state)
            self.travel_state.update(result)
            result = self.summary_agent(self.travel_state)
            self.travel_state.update(result)
            result = self.final_presentation_agent(self.travel_state)
        else:
            result = {"agent_response": "Thank you for using our travel planning service! Feel free to ask if you need any adjustments to your plan."}
        
        # Update state
        self.travel_state.update(result)
        
        # Send response
        if result.get("agent_response"):
            await session.generate_reply(instructions=result["agent_response"])

async def entrypoint(ctx: agents.JobContext):
    """Main entrypoint for the voice travel planning agent."""
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-2.0-flash"),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
    )

    travel_agent = TravelPlanningAgent()

    await session.start(
        room=ctx.room,
        agent=travel_agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony(),
            close_on_disconnect=False  # optional: keep session even if participant disconnects
        ),
    )

    await ctx.connect()

    # Initial greeting
    await session.generate_reply(
        instructions="Hello! I'm your AI travel planning assistant. I'm excited to help you plan your perfect trip! Let's start with your budget. What's your total budget for this trip?"
    )

    # Handle user messages (sync callback scheduling async work)
    def on_user_speech(message):
        asyncio.create_task(travel_agent.process_user_input(message.text, session))
    session.on("user_speech_committed", on_user_speech)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))