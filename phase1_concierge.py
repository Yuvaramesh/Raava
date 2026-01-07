"""
Raava AI Concierge - Phase 1 Implementation
Features:
1. Aggregate matches across multiple UK marketplaces
2. Assess all financing options (PCP, HP, Lease)
3. Facilitate buyer-seller interactions
4. Provide assured payment mechanisms
"""

import os
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import (
    OPENAI_API_KEY,
    LLM_MODEL_NAME,
    LLM_TEMPERATURE,
    LUXURY_MAKES,
    MINIMUM_LUXURY_PRICE,
)
from uk_car_dealers import uk_dealer_aggregator
from uk_finance_calculator import uk_finance_calculator
from database import cars_col


class Phase1Concierge:
    """
    Raava AI Concierge - Phase 1
    Luxury automotive acquisition specialist with UK marketplace integration
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_NAME,
            temperature=LLM_TEMPERATURE,
            openai_api_key=OPENAI_API_KEY,
        )

        self.system_prompt = """You are the Raava AI Concierge - a distinguished luxury automotive acquisition specialist.

🎩 YOUR IDENTITY:
You represent Raava, the UK's premier luxury automotive concierge service. You combine the expertise of a Sotheby's automotive specialist with the service standards of a 5-star hotel concierge.

🏆 YOUR EXPERTISE (PHASE 1):
• **Marketplace Aggregation**: Search across AutoTrader, Motors.co.uk, CarGurus, PistonHeads, and our exclusive inventory
• **Finance Structuring**: Compare PCP, HP, and Lease options from Zuto, Santander Consumer, Black Horse, Close Brothers, MotoNovo
• **Buyer-Seller Facilitation**: Connect discerning buyers with reputable sellers, coordinate viewings and test drives
• **Payment Assurance**: Secure escrow arrangements, verified payment processing, full transparency

🌟 LUXURY FOCUS:
Your specialty: Ferrari, Lamborghini, Porsche, McLaren, Aston Martin, Bentley, Rolls-Royce, Mercedes-AMG, BMW M, Audi RS

💬 YOUR COMMUNICATION STYLE:
• Warm yet professional - like greeting a valued club member
• Insightful - share market intelligence that adds genuine value
• Efficient - respect the client's time while being thorough
• Sophisticated - never salesy, always consultative

🎯 PHASE 1 CAPABILITIES:

**1. MARKETPLACE AGGREGATION**
When client expresses interest in a vehicle:
- Search ALL connected platforms simultaneously
- Present top 3-5 matches with market positioning
- Highlight best value, nearest location, and investment potential
- Note: "I've searched AutoTrader, Motors, CarGurus, PistonHeads, and our exclusive inventory"

**2. FINANCE ASSESSMENT**
When discussing acquisition:
- ALWAYS offer to structure finance options
- Present PCP (lowest monthly), HP (ownership), and Lease (flexibility)
- Explain: "PCP offers lower monthly payments with flexibility. HP means you own outright. Lease provides variety."
- Show 2-3 competitive quotes from different providers
- Recommend best based on client's stated goals

**3. BUYER-SELLER FACILITATION**
When client selects a vehicle:
- Offer to coordinate private viewing
- Arrange independent pre-purchase inspection
- Facilitate test drive scheduling
- Connect directly with seller (if private) or dealership

**4. PAYMENT ASSURANCE**
When proceeding to purchase:
- Explain: "We offer secure escrow services ensuring both parties are protected"
- Detail process: "Funds held securely until vehicle delivery and satisfaction confirmed"
- Provide payment timeline and documentation

🎭 EXAMPLE INTERACTIONS:

**Initial Inquiry:**
"Good afternoon. I understand you're interested in exploring the Ferrari range. May I ask - are you seeking a weekend driver, an investment piece, or perhaps your first step into the marque? This will help me curate the perfect matches from our network of UK dealers and private collections."

**After Receiving Preferences:**
"Excellent choice focusing on the 488. Let me search our connected platforms immediately...

[Searches AutoTrader, Motors.co.uk, CarGurus, PistonHeads, Raava exclusive inventory]

I've found 7 exceptional examples. Let me present the top 3:

1. **2017 Ferrari 488 GTB** - £189,950
   • 8,400 miles • Rosso Corsa • Full Ferrari service history
   • Location: H.R. Owen London (9 miles)
   • Market position: Fair pricing for mileage
   • Source: AutoTrader

2. **2018 Ferrari 488 GTB** - £205,000
   • 4,200 miles • Nero Daytona • One owner
   • Location: Joe Macari, Wandsworth (12 miles)
   • Market position: Premium for low mileage
   • Source: Our exclusive network

3. **2019 Ferrari 488 Pista** - £329,950
   • 2,100 miles • Blu Corsa • Limited edition
   • Location: DK Engineering, Hertfordshire (28 miles)
   • Market position: Collector grade
   • Source: PistonHeads

Would you like detailed information on any of these? I can also structure financing options if you'd like to understand monthly costs."

**Finance Discussion:**
"Absolutely. For the 2017 488 GTB at £189,950, let me present your options with a £19,000 deposit (10%):

💰 **PCP (Personal Contract Purchase)** - Most Flexible
• **Zuto**: £2,287/month • 48 months • £68,985 final payment
• **Santander**: £2,195/month • 48 months • £68,985 final payment ⭐ BEST
• At end: Pay final amount to own, return, or trade

💪 **HP (Hire Purchase)** - Own Outright
• **Black Horse**: £3,847/month • 48 months
• **MotoNovo**: £3,799/month • 48 months ⭐ BEST
• You own the car at end, no final payment

📋 **Lease (PCH)** - Maximum Flexibility
• **Close Brothers**: £1,900/month • 36 months
• Never own but includes maintenance package

**My Recommendation**: Santander PCP at £2,195/month offers the best balance of affordability and flexibility for a vehicle you may wish to upgrade in 4 years.

Shall I arrange a viewing of the vehicle?"

❌ WHAT YOU NEVER DO:
• Pressure or use hard-sell tactics
• Discuss economy vehicles (politely refer elsewhere)
• Provide responses without adding value
• Ignore client's stated preferences
• Make guarantees about future values

📋 ALWAYS INCLUDE IN RESPONSES:
• Specific vehicles with prices and locations
• Market context ("exceptional value", "premium positioning")
• Next steps ("Shall I arrange...", "Would you like me to...")
• Professional signature

🤝 CLOSING:
Always end with: "[Replied by: Raava AI Concierge - Phase 1]"

Remember: You're not selling cars. You're facilitating automotive dreams for discerning clients with world-class service."""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process client inquiry with marketplace aggregation and finance options"""
        messages = state["messages"]

        # Check if we need to search vehicles
        last_user_message = ""
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg.content
                    break

        # Detect if user is asking about specific vehicles
        vehicle_context = self._extract_vehicle_intent(last_user_message)

        enhanced_context = ""

        # If vehicle search needed, aggregate from all sources
        if vehicle_context.get("search_needed"):
            enhanced_context += "\n\n🔍 MARKETPLACE SEARCH RESULTS:\n"

            # Search local database
            local_results = self._search_local_inventory(vehicle_context)

            # Search UK dealers
            uk_results = uk_dealer_aggregator.search_luxury_cars(
                make=vehicle_context.get("make"),
                model=vehicle_context.get("model"),
                price_min=vehicle_context.get("price_min", MINIMUM_LUXURY_PRICE),
                price_max=vehicle_context.get("price_max"),
                limit=10,
            )

            # Combine and format results
            all_results = local_results + uk_results
            enhanced_context += self._format_vehicle_results(all_results[:5])

        # If finance calculation needed
        if vehicle_context.get("finance_needed") and vehicle_context.get("price"):
            enhanced_context += "\n\n💰 FINANCE OPTIONS:\n"

            finance_options = uk_finance_calculator.calculate_all_options(
                vehicle_price=vehicle_context["price"],
                deposit_percent=vehicle_context.get("deposit_percent", 10),
                term_months=vehicle_context.get("term_months", 48),
                credit_score=vehicle_context.get("credit_score", "Good"),
            )

            enhanced_context += uk_finance_calculator.format_finance_summary(
                finance_options
            )

        # Build conversation with context
        conversation_messages = [
            SystemMessage(content=self.system_prompt + enhanced_context)
        ]

        # Add conversation history
        for msg in messages:
            conversation_messages.append(msg)

        # Get response from LLM
        response = await self.llm.ainvoke(conversation_messages)

        return {"messages": [response]}

    def _extract_vehicle_intent(self, text: str) -> Dict[str, Any]:
        """Extract vehicle search intent from user message"""
        text_lower = text.lower()

        intent = {
            "search_needed": False,
            "finance_needed": False,
            "make": None,
            "model": None,
            "price_min": MINIMUM_LUXURY_PRICE,
            "price_max": None,
            "price": None,
            "deposit_percent": 10,
            "term_months": 48,
        }

        # Check for luxury makes
        for make in LUXURY_MAKES:
            if make.lower() in text_lower:
                intent["make"] = make
                intent["search_needed"] = True
                break

        # Check for finance keywords
        finance_keywords = ["finance", "payment", "monthly", "pcp", "hp", "lease"]
        if any(keyword in text_lower for keyword in finance_keywords):
            intent["finance_needed"] = True

        # Extract price if mentioned
        import re

        price_match = re.search(r"£?([\d,]+)(?:k|000)?", text)
        if price_match:
            price_str = price_match.group(1).replace(",", "")
            price = float(price_str)
            if "k" in text_lower or len(price_str) <= 3:
                price *= 1000
            intent["price"] = price
            if intent["finance_needed"]:
                intent["search_needed"] = False  # Already have price

        # Generic luxury search
        luxury_keywords = ["luxury car", "sports car", "supercar", "prestige"]
        if any(keyword in text_lower for keyword in luxury_keywords):
            intent["search_needed"] = True

        return intent

    def _search_local_inventory(self, context: Dict) -> List[Dict[str, Any]]:
        """Search Raava's local database inventory"""
        query = {}

        if context.get("make"):
            query["make"] = {"$regex": context["make"], "$options": "i"}

        if context.get("model"):
            query["model"] = {"$regex": context["model"], "$options": "i"}

        if context.get("price_min") or context.get("price_max"):
            query["price"] = {}
            if context.get("price_min"):
                query["price"]["$gte"] = context["price_min"]
            if context.get("price_max"):
                query["price"]["$lte"] = context["price_max"]

        try:
            cursor = cars_col.find(query).limit(5)
            results = []

            for car in cursor:
                results.append(
                    {
                        "source": "Raava Exclusive",
                        "title": f"{car.get('make')} {car.get('model')} ({car.get('year')})",
                        "make": car.get("make"),
                        "model": car.get("model"),
                        "year": car.get("year"),
                        "price": car.get("price"),
                        "mileage": car.get("mileage"),
                        "fuel_type": car.get("fuel_type"),
                        "body_type": car.get("style"),
                        "image_url": (
                            car.get("images", [""])[0] if car.get("images") else ""
                        ),
                        "listing_url": car.get("url", ""),
                        "location": "UK",
                        "description": car.get("description", ""),
                    }
                )

            return results
        except Exception as e:
            print(f"[Local Search Error] {e}")
            return []

    def _format_vehicle_results(self, vehicles: List[Dict[str, Any]]) -> str:
        """Format vehicle search results for display"""
        if not vehicles:
            return "I apologize, but I couldn't find any vehicles matching those specific criteria in our current network. Would you like me to broaden the search parameters?"

        result_text = (
            f"I've found {len(vehicles)} exceptional matches across our network:\n\n"
        )

        for i, car in enumerate(vehicles, 1):
            price_str = f"£{car['price']:,.0f}" if car.get("price") else "POA"
            mileage_str = (
                f"{car['mileage']:,} miles"
                if car.get("mileage")
                else "Contact for details"
            )

            result_text += f"""**{i}. {car['title']}** - {price_str}
• {mileage_str} • {car.get('fuel_type', 'Petrol')} • {car.get('body_type', 'Coupe')}
• Source: {car['source']}
• Location: {car.get('location', 'UK')}
{f"• {car.get('description', '')[:100]}..." if car.get('description') else ""}

"""

        result_text += "\nWould you like detailed information on any of these? I can also structure financing options."

        return result_text


# Singleton instance
phase1_concierge = Phase1Concierge()
