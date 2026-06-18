import hashlib

class DHTNode:
    def __init__(self, peer_id):
        self.peer_id = peer_id

    def hash(self, key):
        return int(hashlib.sha1(key.encode()).hexdigest(), 16)

    def find_peer(self, key):
        # versão simplificada
        hashed = self.hash(key)
        return hashed % 10  # mock