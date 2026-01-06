import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from services.booking_service import BookingService

load_dotenv()


class ConciergeAgent:
    """
    The Raava AI Concierge - Your Personal Luxury Automotive Advisor
    Concise, conversational, and genuinely helpful.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
        )

        self.system_prompt = """You are the Raava AI Concierge - a luxury automotive advisor who's warm, knowledgeable, and genuinely helpful.

🎩 YOUR PERSONALITY:
Think of yourself as the concierge at an exclusive club - refined, but never stuffy. You're conversational, friendly, and get straight to the point.

✅ YOUR COMMUNICATION STYLE:
• **Brief & Natural** - Keep responses to 2-4 sentences max per point
• **Conversational** - Talk like a person, not a brochure
• **Helpful** - Focus on what matters to the client
• **Warm** - Be genuinely interested in their needs

📋 BOOKING FLOW:
When a customer expresses interest in booking or renting a car:
1. Confirm they want to proceed with booking
2. Collect personal information in a natural conversational way (don't ask all at once)
3. For rentals, confirm dates
4. Confirm financing option
5. Once you have all info, explicitly ask them to confirm and then trigger booking

🎯 COLLECTING PERSONAL DATA:
Ask naturally, one or two questions at a time:
- "Great! What's the best email to reach you?"
- "And what's your phone number?"
- "What's your full address and postcode?"
For rentals also ask: "What dates are you looking to rent from?"

🏁 WHEN BOOKING IS READY:
Once you have confirmed all details, use this format in your response:
__BOOKING_CONFIRMATION_REQUESTED__
{
  "first_name": "value",
  "last_name": "value",
  "email": "value",
  "phone": "value",
  "address": "value",
  "postcode": "value",
  "car_title": "value",
  "booking_type": "purchase or rental",
  "rental_start_date": "DD/MM/YYYY (if rental)",
  "rental_end_date": "DD/MM/YYYY (if rental)",
  "financing_option": "PCP/HP/Personal Loan/Cash",
  "additional_notes": "any special requests"
}
__END_BOOKING__

The system will process this and confirm the booking with an order ID.

Remember: You're a helpful advisor, not a salesman. Be honest, be concise, be genuinely interested in helping them find the right car."""

        self.booking_service = BookingService()

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process client inquiry with luxury concierge service"""
        messages = state["messages"]

        # Add context awareness
        conversation_history = self._format_conversation(messages)

        # Prepare enriched prompt with conversation context
        enriched_messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "system",
                "content": f"Conversation context: {conversation_history}",
            },
        ] + [self._convert_message(msg) for msg in messages]

        response = await self.llm.ainvoke(enriched_messages)

        response_text = response.content
        if "__BOOKING_CONFIRMATION_REQUESTED__" in response_text:
            booking_data = self._extract_booking_data(response_text)
            if booking_data:
                is_valid, validation_msg = self.booking_service.validate_booking_data(
                    booking_data
                )
                if is_valid:
                    result = self.booking_service.create_order(booking_data)
                    summary = self.booking_service.get_booking_summary(booking_data)
                    confirmation_response = f"{summary}\n\n{result['message']}"
                    response.content = confirmation_response
                else:
                    response.content = f"There was an issue with the booking data: {validation_msg}. Please provide the missing information."

        return {"messages": [response]}

    def _format_conversation(self, messages) -> str:
        """Create conversation context summary"""
        if len(messages) <= 1:
            return "First inquiry - greet warmly and ask one clarifying question."

        return f"Ongoing conversation with {len(messages)-1} previous messages. Keep responses brief and conversational. Build on what you've already discussed."

    def _convert_message(self, msg) -> dict:
        """Convert LangChain message to dict format"""
        if isinstance(msg, HumanMessage):
            return {"role": "user", "content": msg.content}
        elif isinstance(msg, AIMessage):
            return {"role": "assistant", "content": msg.content}
        return {"role": "user", "content": str(msg)}

    def _extract_booking_data(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON booking data from response"""
        try:
            start = text.find("__BOOKING_CONFIRMATION_REQUESTED__")
            end = text.find("__END_BOOKING__")
            if start != -1 and end != -1:
                json_str = text[
                    start + len("__BOOKING_CONFIRMATION_REQUESTED__") : end
                ].strip()
                return json.loads(json_str)
        except Exception as e:
            print(f"Error extracting booking data: {str(e)}")
        return None
