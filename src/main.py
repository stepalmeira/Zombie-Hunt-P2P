from network.peer import Peer

if __name__ == "__main__":
    peer = Peer(peer_id="peer2", port=5000)
    peer.start()