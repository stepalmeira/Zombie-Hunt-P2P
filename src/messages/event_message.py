from messages.message import Message


class EventMessage(Message):

    def __init__(
        self,
        event_type,
        player_id,
        timestamp,
        data=None,
        event_id=None
    ):

        super().__init__(
            msg_type=event_type,

            player_id=player_id,

            timestamp=timestamp,

            data=data,

            event_id=event_id
        )