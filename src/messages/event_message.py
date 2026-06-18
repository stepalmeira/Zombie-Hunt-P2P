from messages.message import Message

class EventMessage(Message):
    def __init__(self, payload, timestamp):
        super().__init__("event", payload, timestamp)