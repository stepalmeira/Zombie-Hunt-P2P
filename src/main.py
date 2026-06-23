import sys
from network.peer import Peer


def main():
    if len(sys.argv) < 4:

        print(
            "Usage:"
        )

        print(
            "python main.py "
            "<peer_id> "
            "<player_name> "
            "<port>"
        )

        return

    peer_id = int(sys.argv[1])
    player_name = sys.argv[2]
    port = int(sys.argv[3])

    peer = Peer(
        peer_id=peer_id,
        player_name=player_name,
        port=port
    )

    # ======================================
    # FULL MESH MANUAL
    # ======================================

    # exemplo:
    #
    # peer 1 conhece 2 e 3
    # peer 2 conhece 1 e 3
    # etc

    known_peers = {

        1: ("localhost", 5001),
        2: ("localhost", 5002),
        3: ("localhost", 5003),
        4: ("localhost", 5004)

    }

    for other_peer_id, addr in known_peers.items():

        if other_peer_id == peer_id:
            continue

        peer.network.add_peer(
            other_peer_id,
            addr[0],
            addr[1]
        )

    peer.start()

    print(
        f"\nPlayer {player_name} started "
        f"on port {port}"
    )

    # ======================================
    # LOOP PRINCIPAL
    # ======================================

    while True:

        print("\n===== MENU =====")

        print("1 - Show State")
        print("2 - Generate Pairings")
        print("3 - Play Card")
        print("4 - Exit")

        choice = input("> ")

        # ======================================
        # SHOW STATE
        # ======================================

        if choice == "1":

            peer.print_state()

        # ======================================
        # GENERATE PAIRS
        # ======================================

        elif choice == "2":

            pairs = peer.generate_pairings()

            print("\nPairs:")

            for pair in pairs:

                print(pair)

        # ======================================
        # PLAY CARD
        # ======================================

        elif choice == "3":

            target_id = int(
                input("Target player id: ")
            )

            card = int(
                input("Card to play: ")
            )

            peer.play_card(
                card,
                target_id
            )

        # ======================================
        # EXIT
        # ======================================

        elif choice == "4":
            print("Closing peer...")
            break


if __name__ == "__main__":
    main()