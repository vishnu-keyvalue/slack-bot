import signal
from slack_bolt.adapter.socket_mode import SocketModeHandler

from src.helpers import get_environment_variable
from src.bot.init import app


if __name__ == "__main__":
    SLACK_APP_TOKEN = get_environment_variable("SLACK_APP_TOKEN")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)

    def signal_handler(signal, frame):
        handler.close()
        print("Shutting down gracefully...")
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    handler.start()
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
