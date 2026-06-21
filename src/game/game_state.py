class GameState:
    def __init__(self):
        self.players = {}
        self.entities = {}

    def update_player(self, player_id, data):
        self.players[player_id] = data

    def apply_event(self, event):
        # lógica do jogo
        pass

    def resolve_conflict(self, event1, event2):
        # timestamp + ID
        if event1["timestamp"] > event2["timestamp"]:
            return event1
        return event2