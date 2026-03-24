from .bet_management import BetManager
from .comm_protocol import read_new_bet, send_message, OK_COMM_TYPE

import socket
import logging
import signal
import sys
import time

SHUTDOWM_RETRY_TIME = 0.1

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        # Initialize bet manager
        self._bet_manager = BetManager()

        # Initialize server's shutdown mechanism
        signal.signal(signal.SIGTERM, self.__shut_down_server)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # Server keeps accepting connections until SIGTERM is launched
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        while True:
            new_bet = read_new_bet(client_sock)

            # If client closes the connection
            if new_bet is None:
                client_sock.close()
                return

            # Process bet
            message = OK_COMM_TYPE
            try:
                self._bet_manager.store_bets_in_database(new_bet)
                logging.info(f'action: apuesta_almacenada | result: success | dni: {new_bet.document} | numero: {new_bet.number}')
            except Exception as e:
                message = str(e)
                logging.error(f"action: apuesta_almacenada | result: fail | error: {e}")

            # Answer client
            send_message(client_sock, message)


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
    
    def __shut_down_server(self, signum, frame):
        while True:
            try:
                self._server_socket.close()
                break
            except:
                time.sleep(SHUTDOWM_RETRY_TIME)
        sys.exit(0)
