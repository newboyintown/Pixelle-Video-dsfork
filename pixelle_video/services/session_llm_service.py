import json
from typing import Optional, Type, TypeVar, Union, Any, List, Dict
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from pixelle_video.services.llm_service import LLMService

T = TypeVar('T', bound=BaseModel)

class SessionLLMService:
    """
    A stateful wrapper around LLMService that maintains a conversation history.
    Implements a 50-turn defense mechanism to summarize and reset the session.
    """

    def __init__(self, base_llm: LLMService, max_turns: int = 50):
        self.base_llm = base_llm
        self.max_turns = max_turns
        self.messages: List[Dict[str, str]] = []

    async def __call__(
        self,
        prompt: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_type: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[str, T]:

        # Check if we reached the max turns defense limit
        if len(self.messages) >= self.max_turns:
            await self._summarize_and_reset()

        # 1. Add new user prompt to history
        enhanced_prompt = prompt
        if response_type is not None:
            json_schema_instruction = self.base_llm._get_json_schema_instruction(response_type)
            enhanced_prompt = f"{prompt}\n\n{json_schema_instruction}"

        self.messages.append({"role": "user", "content": enhanced_prompt})

        client = self.base_llm._create_client(api_key=api_key, base_url=base_url)
        final_model = (
            model
            or self.base_llm._get_config_value("model")
            or "gpt-3.5-turbo"
        )

        try:
            response = await client.chat.completions.create(
                model=final_model,
                messages=self.messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content

            # 2. Add assistant response to history
            self.messages.append({"role": "assistant", "content": content})

            if response_type is not None:
                return self.base_llm._parse_response_as_model(content, response_type)
            return content

        except Exception as e:
            logger.error(f"SessionLLM call error: {e}")
            raise

    async def _summarize_and_reset(self):
        """Summarize current chat history and reset session."""
        logger.info("Session reached turn limit. Summarizing context and resetting session.")

        summary_prompt = "Hãy tóm tắt lại toàn bộ nội dung quan trọng và trạng thái hiện tại của cuộc trò chuyện này để chúng ta có thể tiếp tục công việc trong một phiên làm việc mới một cách trơn tru. Hãy giữ lại các thông tin thiết yếu nhất."

        temp_messages = list(self.messages)
        temp_messages.append({"role": "user", "content": summary_prompt})

        client = self.base_llm._create_client()
        final_model = self.base_llm._get_config_value("model") or "gpt-3.5-turbo"

        try:
            response = await client.chat.completions.create(
                model=final_model,
                messages=temp_messages,
                temperature=0.7,
                max_tokens=2000
            )
            summary_content = response.choices[0].message.content

            # Reset and re-seed
            self.messages = [
                {"role": "system", "content": f"Đây là tóm tắt từ phiên làm việc trước: {summary_content}. Hãy tiếp tục công việc dựa trên ngữ cảnh này."}
            ]
            logger.info("Session successfully summarized and reset.")

        except Exception as e:
            logger.error(f"Failed to summarize session: {e}")
            if self.messages and self.messages[0]["role"] == "system":
                self.messages = [self.messages[0]] + self.messages[-10:]
            else:
                self.messages = self.messages[-10:]

    @property
    def active(self) -> str:
        return self.base_llm.active
