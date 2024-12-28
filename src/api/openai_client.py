from typing import List, Dict
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


class OpenAIWrapper:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def send_message(
        self, messages: List[Dict[str, str]], context: str = ""
    ) -> ChatCompletion:
        try:
            if context:
                messages.insert(0, {"role": "system", "content": context})

            response = await self.client.chat.completions.create(
                model=self.model, messages=messages
            )
            return response
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise
