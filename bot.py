import requests
import socket
import json

class Bot:

    def _init_(self, host, port):
        self.address = (host, port)
        self.clients = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.address)
        self.socket.listen(10)


    def run(self):
        pass


    def send_requests(self, url, n):
        for _ in range(n):
            response = requests.get(url)
            print(response.status_code)


HOST = '127.0.0.1'
PORT = 80

if __name__ == '__main__':
    pass

    # bot.send_requests('https://google.com', 3)
