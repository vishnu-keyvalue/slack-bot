from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional
from src.constants.actions import Actions
from src.helpers import get_environment_variable


class State(MessagesState):
    action: Actions


def identify_action(state: State):
    system_prompt = """
        You are an intent classifier. Your task is to identify the intended action from the user message. Based on the message, classify the action into one of the following:
            - SUMMARIZE: If the user is asking to summarize messages or conversations (including 'summarize this', 'get a summary', 'what was said', etc.).
            - ACTION_ITEM: If the user is asking to list action items or tasks (including 'list action items', 'what are the tasks', 'what needs to be done', etc.).
            - SCHEDULE: If the user is asking to schedule a meeting or event (including 'schedule a meeting', 'set up a meeting', 'create a calendar invite/event', etc.).
            - NONE: If the query does not match any of the above.
    """

    system_message = SystemMessage(content=system_prompt)

    user_message = state["messages"][-1]

    OPENAI_API_KEY = get_environment_variable("OPENAI_API_KEY")

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0,
    )

    class FindAction(BaseModel):
        action: Optional[str] = Field(
            description="user action from the list of actions."
        )

    response = llm.with_structured_output(FindAction).invoke(
        [system_message] + [user_message])

    return {"action": response.action}
