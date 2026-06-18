class LeaderElection:
    def __init__(self, peers):
        self.peers = peers

    def elect(self):
        # menor ID vence
        return min(self.peers)