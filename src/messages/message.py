class Message:
    def __init__(self, msg_type, payload, timestamp):
        self.type = msg_type
        self.payload = payload
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp
        }