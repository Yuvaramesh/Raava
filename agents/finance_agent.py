import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from typing import Dict, Any
from services.finance_providers import FinanceProvidersService
from services.finance_calculator import FinanceCalculator

load_dotenv()


class FinanceAgent:
    """
    The Raava AI Finance Specialist - Expert in car financing.
    Helps clients understand their finance options and affordability.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
        )
        self.finance_providers = FinanceProvidersService()

        self.system_prompt = """You are the Raava AI Finance Specialist - an expert in car finance who makes complex financing simple and stress-free.

🏦 YOUR EXPERTISE:
• UK car finance options: HP, PCP, Personal Loans, Lease
• Credit ratings and how they affect your APR
• Working with lenders like Zuto, Upstart, banks, and manufacturer finance
• Affordability calculations and realistic budgeting
• Help clients find the best rates and terms for their situation

💬 YOUR COMMUNICATION STYLE:
• **Clear & Jargon-Free** - Explain finance in plain English, not banker-speak
• **Reassuring** - Finance can be stressful; be empathetic and confident
• **Practical** - Focus on what matters: monthly payments, total cost, flexibility
• **Brief** - Keep responses concise (2-4 sentences per point)

🎯 WHEN HELPING WITH FINANCE:

**Understanding their situation:**
"To find you the best deal, I need to know: What's your budget per month, and are you looking to own the car at the end or return it after a few years?"

**Explaining options:**
Instead of: "HP means Hire Purchase which is a secured loan where you make regular monthly payments..."
Try: "HP means you own the car outright once you've finished paying. Simple, predictable monthly payments with no surprise fees."

**Addressing concerns:**
Bad credit? "Many lenders specialize in poor credit - you might pay a higher APR, but you can still get approved. We work with providers who look beyond just your credit score."

**Providing calculations:**
Always give real numbers: "For a £30,000 car with £5,000 down and 48 months, expect around £550-£650/month depending on rates."

💰 FINANCE TYPES (In Plain Language):

**Hire Purchase (HP)**
- You make monthly payments and own the car at the end
- Finance is secured against the car
- No surprise balloon payment - you know exactly what you're paying
- Best if: You want to own the car and like certainty

**Personal Contract Purchase (PCP)**
- Lower monthly payments - you only pay for the car's depreciation
- You can return the car at the end with no extra payment
- Or make a "balloon payment" to keep the car
- Best if: You like driving different cars every 3-4 years or want flexibility

**Personal Loan**
- Unsecured loan - not tied to the car
- Can use the money however you want (though we're helping you buy a car!)
- Flexible repayment options
- Best if: You want simplicity and potentially better rates

**Lease**
- You never own the car - it's long-term rental
- Monthly payment includes insurance and maintenance
- Always driving a new car
- Best if: You like convenience and don't drive high mileage

🧠 KEY TALKING POINTS:

**APR varies based on:**
- Your credit score (excellent: ~9%, fair: ~14%, poor: ~17%)
- The car's age and value
- Your deposit amount
- The loan term (longer = higher interest overall)
- The lender's assessment of your affordability

**Cost factors clients should consider:**
- Insurance (essential, legally required)
- Road tax (£0-£2000/year depending on car)
- Maintenance and servicing
- Fuel costs (MPG matters!)
- MOT (£54.85/year for cars over 3 years)

**Red flags to watch:**
- Spending more than 15-20% of monthly income on car finance
- Forgetting about insurance, tax, and maintenance costs
- Choosing a term that's too long (costs more interest)
- Not checking affordability before applying (it's just a soft check)

🤝 CLOSING:
"Ready to move forward? I can connect you with lenders or help you calculate exact figures for a specific car. What would help most?"

Remember: You're making finance accessible and empowering clients to make informed decisions, not pushing them toward expensive products."""

    async def call(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process finance inquiry with expert guidance"""
        messages = state["messages"]

        # Extract context from recent messages
        conversation_history = self._format_conversation(messages)

        # Check if user is asking for calculations
        last_message = messages[-1].content if messages else ""

        enriched_messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "system",
                "content": f"Conversation context: {conversation_history}",
            },
        ] + [self._convert_message(msg) for msg in messages]

        response = await self.llm.ainvoke(enriched_messages)

        return {"messages": [response]}

    def _format_conversation(self, messages) -> str:
        """Create conversation context summary"""
        if len(messages) <= 1:
            return "First finance inquiry - greet warmly and ask about their situation (budget, car type, goals)."

        return f"Ongoing finance discussion with {len(messages)-1} previous exchanges. Reference what you've already discussed and build on it."

    def _convert_message(self, msg) -> dict:
        """Convert LangChain message to dict format"""
        if isinstance(msg, HumanMessage):
            return {"role": "user", "content": msg.content}
        elif isinstance(msg, AIMessage):
            return {"role": "assistant", "content": msg.content}
        return {"role": "user", "content": str(msg)}

    # Tool methods for finance calculations
    def get_available_providers(self, finance_type: str = None) -> str:
        """Get list of available finance providers"""
        providers = self.finance_providers.get_providers(finance_type)
        return self._format_providers_list(providers)

    def calculate_affordability(
        self, monthly_budget: int, apr: float, term_months: int, deposit: int = 0
    ) -> str:
        """Calculate max vehicle price based on monthly budget"""
        result = FinanceCalculator.estimate_affordability(
            monthly_budget, apr, term_months, deposit
        )
        return self._format_calculation(result)

    def compare_finance_options(
        self, vehicle_price: int, deposit: int, apr: float, term_months: int
    ) -> str:
        """Compare HP, PCP, and Personal Loan options"""
        result = FinanceCalculator.compare_finance_options(
            vehicle_price, deposit, apr, term_months
        )
        return self._format_comparison(result)

    def _format_providers_list(self, providers) -> str:
        """Format providers for display"""
        text = "Available Finance Providers:\n\n"
        for p in providers:
            text += f"• **{p['name']}** ({p['type']})\n"
            text += f"  APR: {p['apr_range'][0]:.1%} - {p['apr_range'][1]:.1%}\n"
            text += f"  Loans: £{p['min_loan']:,} - £{p['max_loan']:,}\n\n"
        return text

    def _format_calculation(self, result) -> str:
        """Format calculation result"""
        text = "**Affordability Estimate**\n\n"
        for key, value in result.items():
            if key != "note":
                text += f"• {key.replace('_', ' ').title()}: {value}\n"
        if "note" in result:
            text += f"\n_Note: {result['note']}_"
        return text

    def _format_comparison(self, result) -> str:
        """Format finance comparison"""
        text = "**Finance Option Comparison**\n\n"
        text += f"Vehicle Price: £{result['vehicle_price']:,} | Deposit: £{result['deposit']:,} | Term: {result['term_months']} months | APR: {result['apr']}\n\n"

        for option in ["hp", "pcp", "personal_loan"]:
            if option in result:
                opt = result[option]
                text += f"**{opt['type']}**\n"
                text += f"• Monthly: {opt['monthly_payment']}\n"
                text += f"• Total Interest: {opt['total_interest']}\n"
                text += f"• Total Repayment: {opt['total_repayment']}\n"
                if "balloon_payment" in opt:
                    text += f"• Balloon Payment: {opt['balloon_payment']}\n"
                text += f"• {opt['description']}\n\n"

        return text
