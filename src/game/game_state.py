import socket
import threading
import json

class NetworkManager:
    def __init__(self, port):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("localhost", port))
        self.peers = []  # lista de (ip, port)

    def start_listening(self, callback):
        thread = threading.Thread(target=self.listen, args=(callback,))
        thread.start()

    def listen(self, callback):
        while True:
            data, addr = self.sock.recvfrom(4096)
            message = json.loads(data.decode())
            callback(message, addr)

    def send(self, message, addr):
        self.sock.sendto(json.dumps(message).encode(), addr)

    def broadcast(self, message):
        for peer in self.peers:
            self.send(message, peer)