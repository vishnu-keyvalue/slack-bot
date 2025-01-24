import ssl
import certifi

from slack_bolt import App
from slack_sdk.errors import SlackApiError
from src.bot.graphs.parent import get_graph as get_parent_graph
from src.helpers import get_environment_variable, get_chat_history, get_user_threads, get_thread_messages, identify_action, is_relevant_response_to_interrupt
from src.constants.actions import Actions
from langgraph.errors import NodeInterrupt

SLACK_BOT_TOKEN = get_environment_variable("SLACK_BOT_TOKEN")
SLACK_BOT_ID = get_environment_variable("SLACK_BOT_ID")
ssl.create_default_context(cafile=certifi.where())

app = App(token=SLACK_BOT_TOKEN)

graph = get_parent_graph()

thread_id = 0


@app.message(f"@{SLACK_BOT_ID}")
def handle_app_mention(message, say):
    global thread_id
    user_id = message['user']
    text = message['text']
    channel_id = message['channel']
    config = {"configurable": {"thread_id": thread_id}}
    chat_history = get_chat_history(channel_id)
    try:
        state = graph.get_state(config=config)
        messages = state.values.get("messages", [])
        interrupt_message = state.tasks[0].interrupts[0].value if state.next else None

        is_relevant_response = is_relevant_response_to_interrupt(
            interrupt=interrupt_message,
            response=text
        ) if interrupt_message else False

        if is_relevant_response:
            graph.update_state(
                config,
                {
                    "messages": [text] + messages
                }
            )
            graph.invoke(None, config=config)
        else:
            new_action = identify_action([text])
            context = {
                "messages": [text],
                "chat_history": chat_history,
                "action": new_action,
            }
            graph.invoke(context, config=config)
            current_state = graph.get_state(config=config)
            if current_state.next:
                interrupt_value = current_state.tasks[0].interrupts[0].value
                say(interrupt_value)
                return

        current_state = graph.get_state(config=config)
        action = current_state.values.get("action", Actions.NONE.value)
        action_response_map = {
            Actions.SUMMARIZE.value: f"Hi <@{user_id}>, here's the summary:\n\n{current_state.values.get('summary', '')}",
            Actions.ACTION_ITEM.value: f"Hi <@{user_id}>, here are the action items:\n\n{current_state.values.get('action_items', '')}",
            Actions.SCHEDULE.value: "Calendar event created successfully!",
        }
        action_response = action_response_map.get(
            action,
            f"""Hi <@{user_id}>, I am an assistant for summarizing Slack conversations and to list actionable items.\n I do not have the capability to understand your query. Please try again with a valid query."""
        )

        say(action_response)

        thread_id = thread_id + 1

    except NodeInterrupt as e:
        say(str(e))
    except Exception as e:
        say(f"An error occurred: {str(e)}")


@app.command("/summarize-threads")
def handle_summarize_threads(ack, say, command):
    ack()
    user_id = command['user_id']
    channel_id = command['channel_id']

    print(f"User ID: {user_id}, Channel ID: {channel_id}")

    try:
        threads = get_user_threads(
            client=app.client,
            channel_id=channel_id,
            user_id=user_id
        )
        summaries = []

        for thread_ts in threads:
            thread_messages = get_thread_messages(channel_id, thread_ts)
            if thread_messages:
                print(f"Thread Messages: {thread_messages}")
                summaries.append("\n".join(thread_messages))

        if summaries:
            say(f"Here are your thread summaries:\n\n" + "\n\n".join(summaries))
        else:
            say("No relevant threads found.")

    except Exception as e:
        say(f"An error occurred: {str(e)}")


@app.message("hi")
def get_user_conversation_history(message, say):
    try:
        users_conversations = app.client.users_conversations(
            user=message['user'],
            limit=5,
            exclude_archived=True,
            types=["private_channel", "mpim", "im", "public_channel"]
        )

        for channel in users_conversations['channels']:
            channel_id = channel['id']
            user = channel['user'] if 'user' in channel else ''
            channel_name = channel['name'] if 'name' in channel else ''
            say(f"Channel ID: <#{channel_id}>, User: <@{user}>, Name: {channel_name}")

            history = app.client.conversations_history(
                channel=channel_id,
                limit=2
            )

            for message in history["messages"]:
                say(f"Message: {message['text']}")

    except SlackApiError as e:
        print(f"An error occurred: {e.response['error']}")
