from typing import Optional, List
from langgraph.graph import MessagesState, START, StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver

from src.helpers import get_environment_variable
from src.bot.graphs.summarizer import summarize_messages
from src.bot.graphs.action_items import get_action_items
from src.bot.graphs.calender_event import create_calendar_event
from src.constants.actions import Actions


class ParentState(MessagesState):
    action: str
    summary: str
    action_items: str
    chat_history: str
    interrupts: Optional[List[str]] = None


def identify_action(state: ParentState):
    system_prompt = """
        You are an intent classifier. Your task is to identify the intended action from the user query. Based on the query, classify the action into one of the following:
            - SUMMARIZE: If the user is asking to summarize messages or conversations (including 'summarize this', 'get a summary', 'what was said', etc.).
            - ACTION_ITEM: If the user is asking to list action items or tasks (including 'list action items', 'what are the tasks', 'what needs to be done', etc.).
            - SCHEDULE: If the user is asking to schedule a meeting or event (including 'schedule a meeting', 'set up a meeting', 'create a calendar invite/event', etc.).
            - NONE: If the query does not match any of the above.
    """

    system_message = SystemMessage(content=system_prompt)

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
        [system_message] + state["messages"])

    return {"action": response.action}


def invoke_sub_graph(state: ParentState):

    action = state.get("action", Actions.NONE.value)

    action_map = {
        Actions.SUMMARIZE.value: "summarizer",
        Actions.ACTION_ITEM.value: "get_action_items",
        Actions.SCHEDULE.value: "create_calendar_event",
        Actions.NONE.value: END,
    }
    return action_map.get(action, END)


def get_graph():
    builder = StateGraph(ParentState)
    builder.add_node("identify_action", identify_action)
    builder.add_node("get_action_items", get_action_items)
    builder.add_node("summarizer", summarize_messages)
    builder.add_node("create_calendar_event", create_calendar_event)
    builder.add_edge(START, "identify_action")
    builder.add_conditional_edges("identify_action", invoke_sub_graph)
    builder.add_edge("summarizer", END)
    builder.add_edge("get_action_items", END)
    builder.add_edge("create_calendar_event", END)

    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    return graph
