from game.player import Player


class GameState:

    def __init__(self):

        # player_id -> Player
        self.players = {}

        # eventos já processados
        self.processed_events = set()

        # seed distribuída
        self.global_seed = None

        # rodada atual
        self.round_number = 1

        # pares atuais
        self.current_pairs = []

        # jogadas da rodada
        self.round_plays = {}

    # ======================================
    # PLAYERS
    # ======================================

    def add_player(self, player_id, name):

        if player_id not in self.players:

            self.players[player_id] = Player(
                player_id,
                name
            )

    def remove_player(self, player_id):

        if player_id in self.players:
            del self.players[player_id]

    def get_player(self, player_id):

        return self.players.get(player_id)

    def get_alive_players(self):

        return [
            player
            for player in self.players.values()
            if player.is_alive()
        ]

    # ======================================
    # SEED / RODADAS
    # ======================================

    def set_global_seed(self, seed):

        self.global_seed = seed

    def next_round(self):

        self.round_number += 1

        self.round_plays = {}

    # ======================================
    # PAPÉIS
    # ======================================

    def set_player_role(self, player_id, role):

        player = self.get_player(player_id)

        if not player:
            return

        if role == Player.ZOMBIE:
            player.become_zombie()

        else:
            player.become_hunter()

    # ======================================
    # JOGADAS
    # ======================================

    def register_play(self, player_id, card):

        player = self.get_player(player_id)

        if not player:
            return

        played_card = player.play_card(card)

        self.round_plays[player_id] = played_card

    def discard_random_card(self, player_id):

        player = self.get_player(player_id)

        if not player:
            return

        discarded = player.discard_card()

        print(
            f"Player {player_id} discarded {discarded}"
        )

    # ======================================
    # DUELOS
    # ======================================

    def resolve_duel(self, player1_id, player2_id):

        if player1_id not in self.round_plays:
            return

        if player2_id not in self.round_plays:
            return

        player1 = self.players[player1_id]
        player2 = self.players[player2_id]

        card1 = self.round_plays[player1_id]
        card2 = self.round_plays[player2_id]

        print(
            f"\nDUEL: "
            f"{player1.name} ({card1}) "
            f"vs "
            f"{player2.name} ({card2})"
        )

        # empate
        if card1 == card2:

            print("Tie! Nobody wins.")

            return "DRAW"

        # vencedor e derrotado
        if card1 > card2:
            winner = player1
            loser = player2

        else:
            winner = player2
            loser = player1

        print(
            f"Winner: {winner.name}"
        )

        # ======================================
        # REGRAS ZUMBI
        # ======================================

        # zumbi vence -> humano vira zumbi
        if winner.is_zombie() and loser.is_hunter():

            loser.become_zombie()

            print(
                f"{loser.name} became a ZOMBIE"
            )

        # humano vence -> zumbi eliminado
        elif winner.is_hunter() and loser.is_zombie():

            loser.eliminate()

            print(
                f"{loser.name} was ELIMINATED"
            )

        return winner.id

    # ======================================
    # GAME OVER
    # ======================================

    def check_player_game_over(self, player_id):

        player = self.get_player(player_id)

        if not player:
            return False

        return player.is_game_over()

    def count_hunters(self):

        return len([
            p for p in self.players.values()
            if p.is_alive() and p.is_hunter()
        ])

    def count_zombies(self):

        return len([
            p for p in self.players.values()
            if p.is_alive() and p.is_zombie()
        ])

    def check_winner_side(self):

        hunters = self.count_hunters()
        zombies = self.count_zombies()

        if hunters > zombies:
            return Player.HUNTER

        elif zombies > hunters:
            return Player.ZOMBIE

        return "DRAW"

    # ======================================
    # EVENTOS DISTRIBUÍDOS
    # ======================================

    def apply_event(self, event):

        event_id = event["event_id"]

        # evita duplicação
        if event_id in self.processed_events:
            return

        self.processed_events.add(event_id)

        event_type = event["type"]

        # ======================================
        # JOGADA DE CARTA
        # ======================================

        if event_type == "CARD_PLAY":

            self.register_play(
                event["player_id"],
                event["card_value"]
            )

        # ======================================
        # ROLE ASSIGNMENT
        # ======================================

        elif event_type == "SET_ROLE":

            self.set_player_role(
                event["target_id"],
                event["role"]
            )

    # ======================================
    # DEBUG
    # ======================================

    def print_state(self):

        print("\n===== GAME STATE =====")

        print(
            f"Round: {self.round_number}"
        )

        print(
            f"Global Seed: {self.global_seed}"
        )

        print("\nPlayers:")

        for player in self.players.values():

            print(
                f"\nPlayer {player.id}"
            )

            print(
                f"Name: {player.name}"
            )

            print(
                f"Role: {player.role}"
            )

            print(
                f"Status: {player.status}"
            )

            print(
                f"Cards: {player.cards}"
            )