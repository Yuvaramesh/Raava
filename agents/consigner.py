import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()


class ConsignerAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", google_api_key=os.getenv("GEMINI_API_KEY")
        )
        self.system_prompt = """You are the Raava AI Consigner.
        Expertise: Valuations, listing prep (photo/desc), and marketplace strategy.
        
        CRITICAL INSTRUCTIONS:
        1. Be extremely concise.
        2. Deliver key valuation and presentation tips quickly.
        3. End every response with: "[Replied by: AI Consigner]"
        """

    async def call(self, state):
        messages = state["messages"]
        response = await self.llm.ainvoke(
            [{"role": "system", "content": self.system_prompt}] + messages
        )
        return {"messages": [response]}
