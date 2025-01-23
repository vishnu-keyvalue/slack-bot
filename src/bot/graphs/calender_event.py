from langgraph.graph import MessagesState
from langgraph.errors import NodeInterrupt
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

from src.helpers import get_environment_variable


class State(MessagesState):
    action_items: str
    chat_history: str


def get_event_details(user_message: str):
    system_prompt = """
        You are an expert in extracting calendar event details.
        Your task is to extract details required for creating a calendar event from the conversation.
        The required details include the event title, date, time, and attendees.
        If any of the required details are missing, identify and return them in the missing_details field.
    """

    system_message = SystemMessage(content=system_prompt)

    OPENAI_API_KEY = get_environment_variable("OPENAI_API_KEY")

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0,
    )

    class CalendarEventDetails(BaseModel):
        event_title: Optional[str] = Field(
            description="title of the calendar event."
        )
        date: Optional[str] = Field(
            description="date of the calendar event."
        )
        time: Optional[str] = Field(
            description="time of the calendar event."
        )
        attendees: Optional[list[str]] = Field(
            description="attendees of the calendar event."
        )
        missing_details: list[str] = Field(
            description="missing details for the calendar event."
        )

    messages = [system_message] + [user_message]
    response = llm.with_structured_output(
        CalendarEventDetails).invoke(messages)

    return response


def create_calendar_event(state: State):
    user_message = state["messages"][0].content
    print(f"User Message: {user_message}")
    calendar_event_details = get_event_details(user_message)

    print(f"Calendar Event Details: {calendar_event_details}")

    if len(calendar_event_details.missing_details) > 0:
        raise NodeInterrupt(
            f"Please re-share the instruction by also including the following details to create the meeting:\n {', '.join(calendar_event_details.missing_details)}")

    return state
