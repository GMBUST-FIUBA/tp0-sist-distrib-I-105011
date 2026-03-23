from .bet_management import BetManager
from .comm_protocol import *
from .errors import *

import selectors
import socket
import logging
import signal
import sys
import time
import multiprocessing

SHUTDOWM_RETRY_TIME = 0.1
TOTAL_AGENCIES = 5

TOTAL_THREADS_IN_POOL = 4

# Bet manager process
## Enum of commands
class InterActorsCommand(Enum):
    OK = 0,
    ADD_BET = 1,
    ADD_BATCH = 2,
    END_TX_BETS = 3,
    WINNERS = 4
    ERR_NOT_ADULT = 5,
    ERR_NOT_VALID_DOC = 6,
    ERR_NOT_VALID_NUM = 7,
    ERR_REPEATED_BET = 8,
    ERR_TAKEN_BET = 9

## Inter actors messages convention
INTER_ACTOR_COMMAND_POS = 0
INTER_ACTOR_BET_POS = 1
INTER_ACTOR_BATCH_POS = 1
INTER_ACTOR_END_TX_POS = 1
INTER_ACTOR_WINNERS_POS = 1

def bet_manager_process(agencies_tx_channel, agencies_rx_channel, total_agencies):
    bets_manager = BetManager()
    agencies_ready = set()

    while True:
        msg_from_agency = agencies_rx_channel.recv()
        msg_type = msg_from_agency[INTER_ACTOR_COMMAND_POS]

        if msg_type == InterActorsCommand.ADD_BET:
            # Get bet
            new_bet = msg_from_agency[INTER_ACTOR_BET_POS]
            # Store bet
            bets_manager.store_bet_in_database()
            # Log result
            logging.info(f'action: apuesta_almacenada | result: success | dni: {new_bet.document} | numero: {new_bet.number}')
        elif msg_type == InterActorsCommand.ADD_BATCH:
            # Get batch
            new_bets = msg_from_agency[INTER_ACTOR_BATCH_POS]
            # Store batch
            bets_manager.store_bets_batch(new_bets)
            # Log result
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(new_bets)}')
        elif msg_type == InterActorsCommand.END_TX_BETS:
            agency = msg_from_agency[INTER_ACTOR_END_TX_POS]

            # Store agency
            agencies_ready.add(agency)

            # If all agencies stopped sending bets, look for winners
            if len(agencies_ready) == total_agencies:
                winners_by_agency = bets_manager.load_winners(total_agencies)

                # Send to all clients its winners
                for agency, winners in winners_by_agency.items():
                    tx_socket = agencies_tx_channel[agency]
                    send_winners(tx_socket, winners)

# Agency process
def agency_process(client_sock, bets_manager_rx_channel, bets_tx_channel):
    while True:
        try:
            new_message = read_message(client_sock)

            # If client closes the connection
            if new_message is None:
                client_sock.close()
                break

            # Process bet
            response = OK_MESSAGE
            try:
                command = __agency_process_message(new_message, client_sock, bets_manager_rx_channel, bets_tx_channel)

                if command != Command.END_TX:
                    send_message(client_sock, response)

            except WrongBatchException as e:
                response = str(e)
                send_message(client_sock, response)
                raise e
            except Exception as e:
                response = str(e)
                send_message(client_sock, response)
                logging.error(f"action: apuesta_almacenada | result: fail | error: {e}")
                raise e

        except Exception:
            client_sock.close()

def __agency_process_message(message, client_socket, bets_manager_rx_channel, bets_tx_channel):
        command = comm_protocol.identify_command(message)

        # Check type
        if command == comm_protocol.Command.ADD_BET:
            # Get new bet
            new_bet = create_new_bet(message)
            # Send to manager new bet
            bets_tx_channel.send((InterActorsCommand.ADD_BET, new_bet))
        elif command == comm_protocol.Command.ADD_BATCH:
            # Get bets batch
            new_bets = create_new_bets_batch(message)
            # Send to manager the batch
            bets_tx_channel.send((InterActorsCommand.ADD_BET, new_bets))
        elif command == comm_protocol.Command.END_TX:
            # Get agency that stopped
            agency = get_stopped_bet_sending_agency(message)

            # Send to manager the agency that stopped sending data
            bets_tx_channel.send((InterActorsCommand.END_TX_BETS, agency))
            
            # When the winners are received, send them to agency
            response = bets_manager_rx_channel.recv()
            if response[INTER_ACTOR_COMMAND_POS] == InterActorsCommand.WINNERS:
                send_winners(client_socket, response[INTER_ACTOR_WINNERS_POS])

        return command

# Server class
class Server:
    def __init__(self, port, listen_backlog, total_agencies):
        # Initialize agencies that stopped to send bets
        self._agencies_ready = set()

        # Initialize agencies that are detected
        self._agencies_detected = {}

        # Store total agencies
        self._total_agencies = total_agencies

        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_socket.setblocking(False)

        # Initialize bet manager
        self._bet_manager = BetManager()

        # Create thread pool
        self._thread_pool = multiprocessing.Pool(processes=TOTAL_THREADS_IN_POOL)

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

                if command != Command.END_TX:
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
        command = comm_protocol.identify_command(message)

        # Check type
        if command == comm_protocol.Command.ADD_BET:
            new_bet = create_new_bet(message)
            self._bet_manager.store_bet_in_database(new_bet)
            self.__log_agency(new_bet.agency, client_socket)
            logging.info(f'action: apuesta_almacenada | result: success | dni: {new_bet.document} | numero: {new_bet.number}')
        elif command == comm_protocol.Command.ADD_BATCH:
            new_bets = create_new_bets_batch(message)
            self._bet_manager.store_bets_batch(new_bets)
            self.__log_agency(new_bets[0].agency, client_socket)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(new_bets)}')
        elif command == comm_protocol.Command.END_TX:
            agency = get_stopped_bet_sending_agency(message)

            # Store agency that stopped sending data
            self._agencies_ready.add(agency)
            
            # If all agencies stopped sending bets, look for winners
            if len(self._agencies_ready) == self._total_agencies:
                winners_by_agency = self._bet_manager.load_winners(self._total_agencies)

                # Send to all clients its winners
                for agency, winners in winners_by_agency.items():
                    tx_socket = self._agencies_detected[agency]
                    send_winners(tx_socket, winners)
        
        return command

    def __log_agency(self, agency, client_socket):
        self._agencies_detected[agency] = client_socket