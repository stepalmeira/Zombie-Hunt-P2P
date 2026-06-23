import socket
import threading
import json


class NetworkManager:

    def __init__(self, port):

        self.port = port

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        self.sock.bind(
            ("localhost", port)
        )

        # peer_id -> (ip, port)
        self.peers = {}

    # ======================================
    # PEERS
    # ======================================

    def add_peer(self, peer_id, ip, port):

        self.peers[peer_id] = (
            ip,
            port
        )

    def remove_peer(self, peer_id):

        if peer_id in self.peers:
            del self.peers[peer_id]

    # ======================================
    # LISTENER
    # ======================================

    def start_listening(self, callback):

        thread = threading.Thread(
            target=self.listen,
            args=(callback,),
            daemon=True
        )

        thread.start()

    def listen(self, callback):

        while True:

            try:

                data, addr = self.sock.recvfrom(4096)

                message = json.loads(
                    data.decode()
                )

                callback(message, addr)

            except Exception as e:

                print(
                    f"[NETWORK ERROR] {e}"
                )

    # ======================================
    # SEND
    # ======================================

    def send(self, message, addr):

        try:

            self.sock.sendto(
                json.dumps(message).encode(),
                addr
            )

        except Exception as e:

            print(
                f"[SEND ERROR] {e}"
            )

    def send_to_peer(self, peer_id, message):

        if peer_id not in self.peers:

            print(
                f"Peer {peer_id} not found"
            )

            return

        addr = self.peers[peer_id]

        self.send(message, addr)

    # ======================================
    # BROADCAST | Full Mesh
    # ======================================

    def broadcast(
        self,
        message,
        exclude_peer=None
    ):

        for peer_id, addr in self.peers.items():

            # evita devolver
            # para quem enviou
            if peer_id == exclude_peer:
                continue

            self.send(message, addr)

    # ======================================
    # DEBUG
    # ======================================

    def print_peers(self):

        print("\n===== CONNECTED PEERS =====")

        for peer_id, addr in self.peers.items():

            print(
                f"{peer_id} -> {addr}"
            )