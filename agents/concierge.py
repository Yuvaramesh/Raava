import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()


class ConciergeAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", google_api_key=os.getenv("GEMINI_API_KEY")
        )
        self.system_prompt = """You are the Raava AI Concierge. 
        Expertise: Buying, marketplace matching, UK financing (PCP, HP), and transaction facilitation.
        
        CRITICAL INSTRUCTIONS:
        1. Be extremely concise. Use bullet points for comparisons.
        2. Focus only on the most important details.
        3. End every response with: "[Replied by: AI Concierge]"
        """

    async def call(self, state):
        messages = state["messages"]
        response = await self.llm.ainvoke(
            [{"role": "system", "content": self.system_prompt}] + messages
        )
        return {"messages": [response]}
