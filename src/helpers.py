import os
from dotenv import dotenv_values, find_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional


def get_environment_variable(key: str, default: str = "", value_type: type = str) -> any:
    """
    Get the environment variable value for the specified key.
    :param key: The key of the environment variable.
    :param default: The default value to return if the environment variable is not set.
    :param value_type: The type to cast the environment variable value to.
    :return: The casted value of the environment variable.
    """
    try:
        dotenv_path = find_dotenv()
        env_vars = dotenv_values(dotenv_path)

        os.environ.update(env_vars)

        env_value = os.getenv(key, default)

        if env_value is None or env_value == "":
            return default

        return value_type(env_value)
    except (ValueError, TypeError, Exception):
        return default


def get_chat_history(channel_id, limit=5):
    try:
        SLACK_BOT_TOKEN = get_environment_variable("SLACK_BOT_TOKEN")
        client = WebClient(token=SLACK_BOT_TOKEN)
        response = client.conversations_history(
            channel=channel_id, limit=limit)
        messages = response['messages']
        text_data = [msg['text'] for msg in messages if 'text' in msg]
        conversation = "\n".join(text_data)
        return conversation
    except SlackApiError as e:
        print(f"Failed to fetch messages: {e.response['error']}")
        return ''
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return ''


def get_user_threads(client: WebClient, channel_id: str, user_id: str):
    response = client.conversations_history(
        channel=channel_id, limit=10)
    messages = response.get('messages', [])
    user_threads = []

    for message in messages:
        print(f"Message: {message}")
        if message.get('thread_ts') and (user_id in message.get('text', '') or message.get('user') == user_id):
            user_threads.append(message['thread_ts'])

    return user_threads


def get_thread_messages(client: WebClient, channel_id: str, thread_ts: str):
    response = client.conversations_replies(
        channel=channel_id,
        ts=thread_ts
    )
    return [msg['text'] for msg in response.get('messages', [])]


def is_relevant_response_to_interrupt(interrupt: str, response: str):
    system_prompt = f"""
    Your task it to identify if the user response is relevant to the interrupt message shared by the bot.
    Input:
    Interrupt: {interrupt} - The instruction shared by the bot.
    Response: {response} - The user response.
    Output:
    True - If the user response is relevant to the interrupt message.
    False - If the user response is not relevant to the interrupt message.
    """

    system_prompt.format(interrupt=interrupt, response=response)

    system_message = SystemMessage(content=system_prompt)

    OPENAI_API_KEY = get_environment_variable("OPENAI_API_KEY")

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0,
    )

    class FindRelevance(BaseModel):
        is_relevant: Optional[bool] = Field(
            description="True if the user response is relevant to the interrupt message. False otherwise."
        )

    response = llm.with_structured_output(FindRelevance).invoke(
        [system_message])

    return response.is_relevant


def identify_action(user_messages: list[str]):
    system_prompt = """
        You are an intent classifier. Your task is to identify the intended action from the user messages. Based on the messages, classify the action into one of the following:
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
        [system_message] + user_messages)

    return response.action
