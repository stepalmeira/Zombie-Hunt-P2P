from network.network_manager import NetworkManager
from game.game_state import GameState
from core.logical_clock import LogicalClock

class Peer:
    def __init__(self, peer_id, port):
        self.peer_id = peer_id
        self.network = NetworkManager(port)
        self.state = GameState()
        self.clock = LogicalClock()
        self.running = False

    def start(self):
        self.running = True
        self.network.start_listening(self.handle_message)

    def handle_message(self, message, addr):
        self.clock.update(message.timestamp)
        # roteia mensagem
        print(f"[{self.peer_id}] Received:", message)

    def send_event(self, event):
        msg = event.to_message(self.clock.tick())
        self.network.broadcast(msg)