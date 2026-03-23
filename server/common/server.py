from .bet_management import BetManager
from .comm_protocol import *
from .errors import *

import selectors
import socket
import logging
import signal
import sys
import time

SHUTDOWM_RETRY_TIME = 0.1
TOTAL_AGENCIES = 5

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize agencies that stopped to send bets
        self._agencies_ready = set()

        # Initialize agencies that are detected
        self._agencies_detected = {}

        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_socket.setblocking(False)

        # Initialize bet manager
        self._bet_manager = BetManager()

        # Initialize selector
        self._selector = selectors.DefaultSelector()
        self._selector.register(self._server_socket, selectors.EVENT_READ, data=self.__accept_new_connection)

        # Initialize server's shutdown mechanism
        signal.signal(signal.SIGTERM, self.__shut_down_server)

    def run(self):

        # Server keeps accepting connections until SIGTERM is launched
        # Selector keeps iterating over all sockets when something is read
        while True:
            events = self._selector.select(timeout=None)
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

    def __handle_client_connection(self, client_sock, mask):
        try:
            new_message = read_message(client_sock)

            # If client closes the connection
            if new_message is None:
                self._selector.unregister(client_sock)
                client_sock.close()
                return

            # Process bet
            response = OK_MESSAGE
            try:
                command = self.__process_message(new_message, client_sock)

                if command == Command.END_TX:
                    self.__close_client(client_sock)
                else:
                    send_message(client_sock, response)
            except WrongBatchException as e:
                response = str(e)
                raise e
            except Exception as e:
                response = str(e)
                logging.error(f"action: apuesta_almacenada | result: fail | error: {e}")
                raise e
        except Exception:
            self.__close_client(client_sock)

    def __close_client(self, client_sock):
        try:
            self._selector.unregister(client_sock)
        except KeyError:
            pass
        client_sock.close()

    def __accept_new_connection(self, server_socket, mask):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')

        c, addr = self._server_socket.accept()
        c.setblocking(False)
        self._selector.register(c, selectors.EVENT_READ, data=self.__handle_client_connection)

        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
    
    def __shut_down_server(self, signum, frame):
        while True:
            try:
                self._server_socket.close()
                break
            except:
                time.sleep(SHUTDOWM_RETRY_TIME)
        sys.exit(0)

    def __process_message(self, message, client_socket):
        print(f"Mensaje a analizar: {message}")
        
        command = comm_protocol.identify_command(message)

        # Check type
        if command == comm_protocol.Command.ADD_BET:
            print(f"Agrego apuesta: ", message)
            new_bet = create_new_bet(message)
            self._bet_manager.store_bet_in_database(new_bet)
            self.__log_agency(new_bet.agency, client_socket)
            logging.info(f'action: apuesta_almacenada | result: success | dni: {new_bet.document} | numero: {new_bet.number}')
        elif command == comm_protocol.Command.ADD_BATCH:
            print(f"Agrego batch: ", len(message))
            new_bets = create_new_bets_batch(message)
            self._bet_manager.store_bets_batch(new_bets)
            self.__log_agency(new_bets[0].agency, client_socket)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(new_bets)}')
        elif command == comm_protocol.Command.END_TX:
            agency = get_stopped_bet_sending_agency(message)

            # Store agency that stopped sending data
            self._agencies_ready.add(agency)
            
            # If all agencies stopped sending bets, look for winners
            if len(self._agencies_ready) == len(self._agencies_detected):
                winners_by_agency = self._bet_manager.load_winners()
                print("Los ganadores entre todos son: ", len(winners_by_agency))

                # Send to all clients its winners
                for agency, winners in winners_by_agency.items():
                    tx_socket = self._agencies_detected[agency]
                    send_winners(tx_socket, winners)
        
        return command

    def __log_agency(self, agency, client_socket):
        self._agencies_detected[agency] = client_socket