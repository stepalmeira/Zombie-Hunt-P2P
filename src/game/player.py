class Player:

    HUNTER = "HUNTER"
    ZOMBIE = "ZOMBIE"

    ALIVE = "ALIVE"
    ELIMINATED = "ELIMINATED"

    def __init__(self, player_id, name):

        self.id = player_id
        self.name = name

        # papel atual
        self.role = Player.HUNTER

        # estado do jogador
        self.status = Player.ALIVE

        # deck fixo do jogo
        self.cards = [1,2,3,4,5,6,7,8,9,10]

        # controle da jogada atual
        self.current_card = None

    # ======================================
    # CARTAS
    # ======================================

    def has_card(self, card):
        return card in self.cards

    def play_card(self, card):

        if card not in self.cards:
            raise ValueError(
                f"Player {self.id} does not have card {card}"
            )

        self.cards.remove(card)

        self.current_card = card

        return card

    def discard_card(self):

        # usado na regra de folga

        if len(self.cards) == 0:
            return None

        discarded = self.cards.pop(0)

        return discarded

    def cards_remaining(self):
        return len(self.cards)

    # ======================================
    # PAPÉIS
    # ======================================

    def become_zombie(self):
        self.role = Player.ZOMBIE

    def become_hunter(self):
        self.role = Player.HUNTER

    # ======================================
    # ESTADO
    # ======================================

    def eliminate(self):
        self.status = Player.ELIMINATED

    def is_alive(self):
        return self.status == Player.ALIVE

    def is_zombie(self):
        return self.role == Player.ZOMBIE

    def is_hunter(self):
        return self.role == Player.HUNTER

    def is_game_over(self):

        # eliminado
        if self.status == Player.ELIMINATED:
            return True

        # sem cartas
        if len(self.cards) == 0:
            return True

        return False

    # ======================================
    # SERIALIZAÇÃO
    # ======================================

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,

            "role": self.role,
            "status": self.status,

            "cards": self.cards,

            "current_card": self.current_card
        }

    @staticmethod
    def from_dict(data):

        player = Player(
            data["id"],
            data["name"]
        )

        player.role = data["role"]
        player.status = data["status"]

        player.cards = data["cards"]

        player.current_card = data["current_card"]

        return player