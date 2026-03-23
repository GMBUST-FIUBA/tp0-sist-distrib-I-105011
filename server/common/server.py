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
    ERR_TAKEN_BET = 9

## Inter actors messages convention
INTER_ACTOR_COMMAND_POS = 0
INTER_ACTOR_BET_POS = 1
INTER_ACTOR_BATCH_POS = 1
INTER_ACTOR_END_TX_POS = 1
INTER_ACTOR_WINNERS_POS = 1
INTER_ACTOR_PIPE_NUM_POS = 2

def bet_manager_process(agencies_tx_channel, agencies_rx_channel, total_agencies):
    bets_manager = BetManager()
    agencies_ready = set()
    agency_to_pipe_translator = {}

    while True:
        msg_from_agency = agencies_rx_channel.get()
        logging.info(f"Admin de apuestas recibe {msg_from_agency}")
        msg_type = msg_from_agency[INTER_ACTOR_COMMAND_POS]

        if msg_type == InterActorsCommand.ADD_BET:
            # Get bet
            new_bet = msg_from_agency[INTER_ACTOR_BET_POS]
            # Store pipe translation part
            pipe_used = msg_from_agency[INTER_ACTOR_PIPE_NUM_POS]
            if new_bet.agency not in agency_to_pipe_translator:
                agency_to_pipe_translator[new_bet.agency] = pipe_used
            # Store bet
            bets_manager.store_bet_in_database()
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
                    pipe_translation = agency_to_pipe_translator[agency]
                    agencies_tx_channel[pipe_translation].put((InterActorsCommand.WINNERS, winners))

# Agency process
def agency_process(client_fd, bets_manager_rx_channel, bets_tx_channel, pipe_used):
    client_sock = socket.socket(fileno=client_fd)
    logging.info(f"Agencia nueva creada para pipe {pipe_used}")
    while True:
        try:
            logging.info(f"Agencia para pipe {pipe_used} espera datos")
            new_message = read_message(client_sock)
            logging.info(f"Agencia para pipe {pipe_used} recibió {new_message}")

            # If client closes the connection
            if new_message is None:
                client_sock.close()
                logging.info(f"Agencia para pipe {pipe_used} cierra")
                break

            # Process bet
            response = OK_MESSAGE
            try:
                command = __agency_process_message(new_message, client_sock, bets_manager_rx_channel, bets_tx_channel, pipe_used)

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

        except Exception as e:
            client_sock.close()
            logging.error(f"Agencia para pipe {pipe_used} cierra")

def __agency_process_message(message, client_socket, bets_manager_rx_channel, bets_tx_channel, pipe_used):
        command = comm_protocol.identify_command(message)

        # Check type
        if command == comm_protocol.Command.ADD_BET:
            logging.info(f"Agencia para pipe {pipe_used} recibe apuesta")
            # Get new bet
            new_bet = create_new_bet(message)
            # Send to manager new bet
            bets_tx_channel.put((InterActorsCommand.ADD_BET, new_bet, pipe_used))
        elif command == comm_protocol.Command.ADD_BATCH:
            logging.info(f"Agencia para pipe {pipe_used} recibe batch de apuestas")
            # Get bets batch
            new_bets = create_new_bets_batch(message)
            # Send to manager the batch
            bets_tx_channel.put((InterActorsCommand.ADD_BATCH, new_bets, pipe_used))
        elif command == comm_protocol.Command.END_TX:
            logging.info(f"Agencia para pipe {pipe_used} recibe fin de recepción de apuestas")
            # Get agency that stopped
            agency = get_stopped_bet_sending_agency(message)

            # Send to manager the agency that stopped sending data
            bets_tx_channel.put((InterActorsCommand.END_TX_BETS, agency, pipe_used))

            # When the winners are received, send them to agency
            response = bets_manager_rx_channel.get()
            if response[INTER_ACTOR_COMMAND_POS] == InterActorsCommand.WINNERS:
                send_winners(client_socket, response[INTER_ACTOR_WINNERS_POS])

        return command

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

        # Create thread pool
        self._thread_pool = multiprocessing.Pool(processes=TOTAL_THREADS_IN_POOL)

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
            args=(c.fileno(), self._bet_manager_pipe, self._bet_manager_to_worker_pipes[pipe_number], pipe_number),
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