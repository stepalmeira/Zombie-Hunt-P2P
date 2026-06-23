import uuid
import random

from network.network_manager import NetworkManager
from game.game_state import GameState
from core.logical_clock import LogicalClock


class Peer:
    def __init__(self, peer_id, player_name, port):
        self.peer_id = peer_id
        self.player_name = player_name

        self.network = NetworkManager(port)

        self.state = GameState()
        self.clock = LogicalClock()

        self.running = False

        # seed local para o consenso distribuído
        self.local_seed = random.randint(1, 10000)

        # seeds recebidas dos outros peers
        self.received_seeds = {
            self.peer_id: self.local_seed
        }

        # adiciona jogador local
        self.state.add_player(
            player_id=peer_id,
            name=player_name
        )

    def start(self):
        self.running = True

        print(f"[Peer {self.peer_id}] Started")

        self.network.start_listening(
            self.handle_message
        )

        # envia seed local para todos
        self.send_event(
            "SEED_SHARE",
            {
                "seed_value": self.local_seed
            }
        )

    def handle_message(self, message, addr):

        # relógio lógico
        self.clock.update(
            message["timestamp"]
        )

        event_id = message["event_id"]

        # evita duplicação
        if event_id in self.state.processed_events:
            return

        print(
            f"[{self.peer_id}] "
            f"Received {message['type']} "
            f"from {message['player_id']}"
        )

        # marca evento como processado
        self.state.processed_events.add(event_id)

        event_type = message["type"]

        # ======================================
        # TROCA DE SEEDS
        # ======================================

        if event_type == "SEED_SHARE":

            sender_id = message["player_id"]
            seed_value = message["seed_value"]

            self.received_seeds[sender_id] = seed_value

            print(
                f"[{self.peer_id}] "
                f"Seed received from {sender_id}: {seed_value}"
            )

            # calcula seed global
            global_seed = sum(
                self.received_seeds.values()
            )

            self.state.set_global_seed(global_seed)

            print(
                f"[{self.peer_id}] "
                f"Global seed updated: {global_seed}"
            )

        # ======================================
        # EVENTOS DE JOGO
        # ======================================

        else:
            self.state.apply_event(message)

        # repassa mensagem para rede
        self.network.broadcast(message)

    def send_event(self, event_type, data):
        timestamp = self.clock.tick()

        message = {
            "event_id": str(uuid.uuid4()),

            "type": event_type,

            "player_id": self.peer_id,

            "timestamp": timestamp,

            **data
        }

        # aplica localmente
        if event_type != "SEED_SHARE":
            self.state.apply_event(message)

        # envia para rede
        self.network.broadcast(message)

    def generate_pairings(self):

        if self.state.global_seed is None:
            print("Global seed not defined yet")
            return []

        alive_players = self.state.get_alive_players()

        player_ids = [
            player["id"]
            for player in alive_players
        ]

        # seed muda por rodada
        seed = (
            self.state.global_seed
            + self.state.round_number
        )

        random.seed(seed)

        random.shuffle(player_ids)

        pairs = []

        for i in range(0, len(player_ids) - 1, 2):

            pair = (
                player_ids[i],
                player_ids[i + 1]
            )

            pairs.append(pair)

        # jogador sobrando
        if len(player_ids) % 2 == 1:

            resting_player = player_ids[-1]

            print(
                f"[{self.peer_id}] "
                f"Player {resting_player} is resting"
            )

            self.state.discard_random_card(
                resting_player
            )

        self.state.current_pairs = pairs

        return pairs

    def play_card(self, card_value, target_id):

        self.send_event(
            "CARD_PLAY",
            {
                "target_id": target_id,
                "card_value": card_value
            }
        )

    def print_state(self):
        self.state.print_state()