from langgraph.graph import MessagesState, START, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Optional
from src.bot.graphs.summarizer import summarize_messages
from src.bot.graphs.action_items import get_action_items
from src.bot.graphs.calender_event import create_calendar_event
from src.constants.actions import Actions


class ParentState(MessagesState):
    action: Actions
    summary: Optional[str] = None
    action_items: Optional[str] = None
    chat_history: Optional[str] = None


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
    builder.add_node("get_action_items", get_action_items)
    builder.add_node("summarizer", summarize_messages)
    builder.add_node("create_calendar_event", create_calendar_event)
    builder.add_conditional_edges(START, invoke_sub_graph)
    builder.add_edge("summarizer", END)
    builder.add_edge("get_action_items", END)
    builder.add_edge("create_calendar_event", END)

    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    return graph
