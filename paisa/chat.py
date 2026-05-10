"""
Conversation history management for chat mode.
Maintains full context across model switches.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from platformdirs import user_config_dir


class ConversationHistory:
    """
    Stores full conversation history and sends it with
    every request so any model has full context.
    """

    def __init__(self):
        self.messages = []  # list of {"role": "user/assistant", "content": "..."}
        self.model_log = []  # track which model handled each turn

    def add_user(self, content: str):
        """Add a user message to history."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str, model: str):
        """Add an assistant message to history and log the model used."""
        self.messages.append({"role": "assistant", "content": content})
        self.model_log.append(model)

    def get_messages(self) -> list:
        """Return a copy of the message history."""
        return self.messages.copy()

    def summary(self) -> str:
        """Return a summary of the conversation."""
        turns = len(self.model_log)
        models_used = list(dict.fromkeys(self.model_log))  # unique, ordered
        return f"{turns} turns | models used: {', '.join(models_used)}"

    def save(self, path: Path):
        """Save conversation history to a JSON file."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "messages": self.messages,
            "model_log": self.model_log,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
