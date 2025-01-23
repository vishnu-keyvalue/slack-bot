import os
from dotenv import dotenv_values, find_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


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
