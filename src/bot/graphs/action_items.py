from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

from src.helpers import get_environment_variable


class State(MessagesState):
    action_items: str
    chat_history: str


def get_action_items(state: State):
    system_prompt = """
        You are an expert in listing action items. Your task is to identify and list the action items from the conversation shared with you.
        Return the list of action items in a structured format.
    """

    system_message = SystemMessage(content=system_prompt)

    OPENAI_API_KEY = get_environment_variable("OPENAI_API_KEY")

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0,
    )

    class ActionItems(BaseModel):
        action_items: Optional[str] = Field(
            description="action_items from the conversation."
        )

    response = llm.with_structured_output(ActionItems).invoke(
        [system_message] + [state["chat_history"]]
    )

    return {"action_items": response.action_items}
