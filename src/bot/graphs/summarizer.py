from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

from src.helpers import get_environment_variable


class State(MessagesState):
    summary: str
    chat_history: str


def summarize_messages(state: State):
    system_prompt = """
        You are a message summarizer. Your task is to summarize the conversation shared with you.
        The summary must be concise and capture the essence of the conversation.
        Do not hallucinate or add any information that is not present in the conversation.
    """

    system_message = SystemMessage(content=system_prompt)

    OPENAI_API_KEY = get_environment_variable("OPENAI_API_KEY")

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0,
    )

    class Summary(BaseModel):
        summary: Optional[str] = Field(
            description="summary of the conversation."
        )

    response = llm.with_structured_output(Summary).invoke(
        [system_message] + [state["chat_history"]]
    )

    return {"summary": response.summary}
