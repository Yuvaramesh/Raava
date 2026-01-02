import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()


class ServiceManagerAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", google_api_key=os.getenv("GEMINI_API_KEY")
        )
        self.system_prompt = """You are the Raava AI Service Manager.
        Expertise: Maintenance reminders, upgrades, vetted service providers, and appointment booking.
        
        CRITICAL INSTRUCTIONS:
        1. Be extremely concise.
        2. Provide direct, actionable advice for luxury vehicle care.
        3. End every response with: "[Replied by: AI Service Manager]"
        """

    async def call(self, state):
        messages = state["messages"]
        response = await self.llm.ainvoke(
            [{"role": "system", "content": self.system_prompt}] + messages
        )
        return {"messages": [response]}
