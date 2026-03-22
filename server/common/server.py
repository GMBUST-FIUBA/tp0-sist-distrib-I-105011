from .bet_management import BetManager
from .comm_protocol import *
from .errors import *

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
    ERR_TAKEN_BET = 9,
    ERR_WRONG_BATCH = 10,

## Inter actors messages convention
INTER_ACTOR_COMMAND_POS = 0
INTER_ACTOR_BET_POS = 1
INTER_ACTOR_BATCH_POS = 1
INTER_ACTOR_END_TX_POS = 1
INTER_ACTOR_WINNERS_POS = 1
INTER_ACTOR_ERR_TXT_POS = 1
INTER_ACTOR_PIPE_NUM_POS = 2

## Exception to inter command type
EXCEPTION_TO_INTER_COMMAND_TYPE = {
    NotAdultClientException: InterActorsCommand.ERR_NOT_ADULT,
    NotValidDocumentException: InterActorsCommand.ERR_NOT_VALID_DOC,
    NotValidBetNumberException: InterActorsCommand.ERR_NOT_VALID_NUM,
    RepeatedBetException: InterActorsCommand.ERR_REPEATED_BET,
    AlreadyUsedNumberException: InterActorsCommand.ERR_TAKEN_BET,
    WrongBatchException: InterActorsCommand.ERR_WRONG_BATCH
}

def bet_manager_process(agencies_tx_channel, agencies_rx_channel, total_agencies):
    bets_manager = BetManager()
    agencies_ready = set()
    agency_to_pipe_translator = {}

    while True:
        msg_from_agency = agencies_rx_channel.get()
        msg_type = msg_from_agency[INTER_ACTOR_COMMAND_POS]

        if msg_type == InterActorsCommand.ADD_BET:
            # Get bet
            new_bet = msg_from_agency[INTER_ACTOR_BET_POS]
            # Store pipe translation part
            pipe_used = msg_from_agency[INTER_ACTOR_PIPE_NUM_POS]
            if new_bet.agency not in agency_to_pipe_translator:
                agency_to_pipe_translator[new_bet.agency] = pipe_used
            # Try to store bet
            try:
                bets_manager.store_bet_in_database(new_bet)
                agencies_tx_channel[pipe_used].put((InterActorsCommand.OK,))
            except tuple(EXCEPTION_TO_INTER_COMMAND_TYPE.keys()) as e:
                agencies_tx_channel[pipe_used].put((EXCEPTION_TO_INTER_COMMAND_TYPE[type(e)], str(e)))
            # Log result
            logging.info(f'action: apuesta_almacenada | result: success | dni: {new_bet.document} | numero: {new_bet.number}')
        elif msg_type == InterActorsCommand.ADD_BATCH:
            # Get batch
            new_bets = msg_from_agency[INTER_ACTOR_BATCH_POS]
            # Store pipe translation part
            pipe_used = msg_from_agency[INTER_ACTOR_PIPE_NUM_POS]
            agency_id = new_bets[0].agency
            if agency_id not in agency_to_pipe_translator:
                agency_to_pipe_translator[agency_id] = pipe_used
            # Try to store batch
            try:
                bets_manager.store_bets_batch(new_bets)
                agencies_tx_channel[pipe_used].put((InterActorsCommand.OK,))
            except tuple(EXCEPTION_TO_INTER_COMMAND_TYPE.keys()) as e:
                agencies_tx_channel[pipe_used].put((EXCEPTION_TO_INTER_COMMAND_TYPE[type(e)], str(e)))
            # Log result
            logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(new_bets)}")
        elif msg_type == InterActorsCommand.END_TX_BETS:
            agency = msg_from_agency[INTER_ACTOR_END_TX_POS]

            # Store agency
            agencies_ready.add(agency)

            # If all agencies stopped sending bets, look for winners
            if len(agencies_ready) == total_agencies:
                winners_by_agency = bets_manager.load_winners(total_agencies)

                # Send to all clients its winners
                for agency, winners in winners_by_agency.items():
                    pipe_translation = agency_to_pipe_translator[agency]
                    agencies_tx_channel[pipe_translation].put((InterActorsCommand.WINNERS, winners))

# Agency process
def agency_process(client_fd, bets_manager_rx_channel, bets_tx_channel, pipe_used):
    client_sock = socket.socket(fileno=client_fd)
    while True:
        try:
            new_message = read_message(client_sock)

            # If client closes the connection
            if new_message is None:
                client_sock.close()
                break

            # Process bet
            __agency_process_message(new_message, client_sock, bets_manager_rx_channel, bets_tx_channel, pipe_used)

        except Exception as e:
            client_sock.close()

def __agency_process_message(message, client_socket, bets_manager_rx_channel, bets_tx_channel, pipe_used):
        command = comm_protocol.identify_command(message)

        # Check type
        if command == comm_protocol.Command.ADD_BET:
            # Get new bet
            new_bet = create_new_bet(message)
            # Send to manager new bet
            bets_tx_channel.put((InterActorsCommand.ADD_BET, new_bet, pipe_used))
            # Receive response
            response = bets_manager_rx_channel.get()

            # Answer according to response
            if response[INTER_ACTOR_COMMAND_POS] == InterActorsCommand.OK:
                send_message(client_socket, OK_MESSAGE)
            else:
                send_message(client_socket, response[INTER_ACTOR_ERR_TXT_POS])
        elif command == comm_protocol.Command.ADD_BATCH:
            # Get bets batch
            new_bets = create_new_bets_batch(message)
            # Send to manager the batch
            bets_tx_channel.put((InterActorsCommand.ADD_BATCH, new_bets, pipe_used))
            # Receive response
            response = bets_manager_rx_channel.get()

            # Answer according to response
            if response[INTER_ACTOR_COMMAND_POS] == InterActorsCommand.OK:
                send_message(client_socket, OK_MESSAGE)
            else:
                send_message(client_socket, response[INTER_ACTOR_ERR_TXT_POS])
        elif command == comm_protocol.Command.END_TX:
            # Get agency that stopped
            agency = get_stopped_bet_sending_agency(message)

            # Send to manager the agency that stopped sending data
            bets_tx_channel.put((InterActorsCommand.END_TX_BETS, agency, pipe_used))

            # When the winners are received, send them to agency
            response = bets_manager_rx_channel.get()
            if response[INTER_ACTOR_COMMAND_POS] == InterActorsCommand.WINNERS:
                send_winners(client_socket, response[INTER_ACTOR_WINNERS_POS])

# Server class
class Server:
    def __init__(self, port, listen_backlog, total_agencies):

        # Store total agencies
        self._total_agencies = total_agencies

        # Store total connected agencies
        self._total_connected_agencies = 0

        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        # Create agencies workers to bet manager pipeline
        self._bet_manager_pipe = multiprocessing.Queue()

        # Create pipes from bet manager to each worker
        self._bet_manager_to_worker_pipes = {i: multiprocessing.Queue() for i in range(1, total_agencies + 1)}
        bet_manager_tx_pipes_side = self._bet_manager_to_worker_pipes

        # Create bets manager process
        bets_manager_process = multiprocessing.Process(
            target=bet_manager_process, 
            args=(bet_manager_tx_pipes_side, self._bet_manager_pipe, total_agencies)
        )
        bets_manager_process.start()

        # Initialize server's shutdown mechanism
        signal.signal(signal.SIGTERM, self.__shut_down_server)

    def run(self):
        # Accept connections
        while True:
            self.__accept_new_connection()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        pipe_number = self._total_connected_agencies + 1

        # Submit agency process
        new_process = multiprocessing.Process(
            target=agency_process,
            args=(c.fileno(), self._bet_manager_to_worker_pipes[pipe_number], self._bet_manager_pipe, pipe_number),
        )
        new_process.start()
        c.close()
        self._total_connected_agencies += 1

        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')

    def __shut_down_server(self, signum, frame):
        while True:
            try:
                self._server_socket.close()
                break
            except:
                time.sleep(SHUTDOWM_RETRY_TIME)
        sys.exit(0)
