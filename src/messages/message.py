import uuid


class Message:
    def __init__(self,msg_type,player_id,timestamp,data=None,event_id=None):

        self.event_id = (
            event_id
            if event_id
            else str(uuid.uuid4())
        )

        self.type = msg_type

        self.player_id = player_id

        self.timestamp = timestamp

        self.data = data if data else {}

    def to_dict(self):

        return {
            "event_id": self.event_id,

            "type": self.type,

            "player_id": self.player_id,

            "timestamp": self.timestamp,

            **self.data
        }

    @staticmethod
    def from_dict(data):

        msg = Message(
            msg_type=data["type"],

            player_id=data["player_id"],

            timestamp=data["timestamp"],

            data={

                k: v for k, v in data.items()

                if k not in [
                    "event_id",
                    "type",
                    "player_id",
                    "timestamp"
                ]
            },

            event_id=data["event_id"]
        )

        return msg