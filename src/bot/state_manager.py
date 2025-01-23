from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class FlowState:
    channel_id: str
    pending_action: Optional[str] = None
    missing_details: Optional[List[str]] = None
    context: Dict[str, str] = None


class StateManager:
    def __init__(self):
        self.channel_states: Dict[str, FlowState] = {}

    def set_pending_state(self, channel_id: str, pending_action: str, missing_details: List[str], context: Dict = None):
        self.channel_states[channel_id] = FlowState(
            channel_id=channel_id,
            pending_action=pending_action,
            missing_details=missing_details,
            context=context or {}
        )

    def get_pending_state(self, channel_id: str) -> Optional[FlowState]:
        return self.channel_states.get(channel_id)

    def clear_pending_state(self, channel_id: str):
        if channel_id in self.channel_states:
            del self.channel_states[channel_id]
