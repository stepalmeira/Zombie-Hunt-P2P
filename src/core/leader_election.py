class LeaderElection:
    def __init__(self, peer_ids):
        self.peer_ids = peer_ids
        self.leader_id = None

    def elect_leader(self):
        # menor ID vence
        self.leader_id = min(
            self.peer_ids
        )

        return self.leader_id

    def get_leader(self):
        return self.leader_id

    def is_leader(self, peer_id):
        return peer_id == self.leader_id