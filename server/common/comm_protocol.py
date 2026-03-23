from enum import Enum

from .utils import Bet

from . import comm_protocol

# Total message length in bytes
TOTAL_MESSAGE_SIZE_BYTES = 2

# Add bet header
ADD_BET_HEADER = "ADD "

# Add batch of bets header
ADD_BETS_BATCH_HEADER = "ADDB"

# End bets transmission
END_BETS_TX_HEADER = "END "

# Correctly processed bet
OK_MESSAGE = "OK"

# Winners message header
WINNERS_HEADER = "WIN "

# Add single bet message parts positions
BET_CLIENT_FIRST_NAME_MSG_POS = 0
BET_CLIENT_SURNAME_MSG_POS = 1
BET_CLIENT_DOCUMENT_MSG_POS = 2
BET_CLIENT_BIRTHDAY_MSG_POS = 3
BET_CLIENT_AGENCY_MSG_POS = 4
BET_CLIENT_LOTTERY_NUMBER_MSG_POS = 5

# Add bet from batch message parts positions
BATCH_BET_CLIENT_FIRST_NAME_MSG_POS = 0
BATCH_BET_CLIENT_SURNAME_MSG_POS = 1
BATCH_BET_CLIENT_DOCUMENT_MSG_POS = 2
BATCH_BET_CLIENT_BIRTHDAY_MSG_POS = 3
BATCH_BET_CLIENT_LOTTERY_NUMBER_MSG_POS = 4

## Bets serialization and deserialization from protocol

class Command(Enum):
    ADD_BET = 1,
    ADD_BATCH = 2,
    END_TX = 3

command_header_to_enum = {
    ADD_BET_HEADER: Command.ADD_BET,
    ADD_BETS_BATCH_HEADER: Command.ADD_BATCH,
    END_BETS_TX_HEADER: Command.END_TX
}

def identify_command(message):
    message_header = message[0:4].decode("utf-8", errors="ignore")

    if message_header not in command_header_to_enum:
        return None

    return command_header_to_enum[message_header]

# Create new single bet
def create_new_bet(message):
    parsed_message = _parse_message_single_bet(message)

    new_bet = Bet(agency=parsed_message[BET_CLIENT_AGENCY_MSG_POS],
                  first_name=parsed_message[BET_CLIENT_FIRST_NAME_MSG_POS],
                  last_name=parsed_message[BET_CLIENT_SURNAME_MSG_POS],
                  document=parsed_message[BET_CLIENT_DOCUMENT_MSG_POS],
                  birthdate=parsed_message[BET_CLIENT_BIRTHDAY_MSG_POS],
                  number=parsed_message[BET_CLIENT_LOTTERY_NUMBER_MSG_POS])

    return new_bet

def _parse_message_single_bet(message):
    message = message.decode("utf-8", errors="ignore")
    message = message.removeprefix(ADD_BET_HEADER)
    split_message = message.split(',')
    return split_message

# Create new bets batch
def create_new_bets_batch(message):
    _, agency_number, parsed_message = _parse_message_bets_batch(message)
    new_bets = []
    for bet_contained in parsed_message:
        parsed_bet_contained = bet_contained.split(',')

        new_bet = Bet(agency=agency_number,
                    first_name=parsed_bet_contained[BATCH_BET_CLIENT_FIRST_NAME_MSG_POS],
                    last_name=parsed_bet_contained[BATCH_BET_CLIENT_SURNAME_MSG_POS],
                    document=parsed_bet_contained[BATCH_BET_CLIENT_DOCUMENT_MSG_POS],
                    birthdate=parsed_bet_contained[BATCH_BET_CLIENT_BIRTHDAY_MSG_POS],
                    number=parsed_bet_contained[BATCH_BET_CLIENT_LOTTERY_NUMBER_MSG_POS])
        
        new_bets.append(new_bet)

    return new_bets

def _parse_message_bets_batch(message):
    message = message[4:]
    total_bets = message.pop(0)
    agency_number = message.pop(0)
    message = message.decode("utf-8", errors="ignore")
    split_message = message.split(';')
    return total_bets, agency_number, split_message

# Get agency that stops sending bets
def get_stopped_bet_sending_agency(message):
    message = message[4:].decode("utf-8", errors="ignore")
    return int(message)

## Bytes management from input/output

# Reads message according to protocol defined on Readme.
def read_message(rx_socket):
    # Reads header for message size
    message_size = _read_message_header(rx_socket)
    if message_size is None:
        return None

    # Reads message's content
    message = _read_message_content(rx_socket, message_size)
    if message is None:
        return None

    return message

# Reads header of message, which is the byte length of the message
def _read_message_header(rx_socket):
    header = __read_n_bytes(rx_socket, TOTAL_MESSAGE_SIZE_BYTES)
    if header is None:
        return None
    return int.from_bytes(header, byteorder="big")

# Reads content of message
def _read_message_content(rx_socket, size):
    content = __read_n_bytes(rx_socket, size)
    if content is None:
        return None
    return content

# Returns None if sender disconnects
def __read_n_bytes(rx_socket, n_bytes):
    data = bytearray()
    remaining_bytes = n_bytes
    while remaining_bytes > 0:
        rx_data = rx_socket.recv(remaining_bytes)
        if not rx_data:
            return None
        remaining_bytes -= len(rx_data)
        data.extend(rx_data)
    return data


# Sends message according to protocol defined on Readme.
def send_message(tx_socket, message):
    content = message.encode("utf-8", errors="ignore")
    header = len(message)

    # Append header and content
    encoded_message = bytearray()
    encoded_message.extend(header.to_bytes(TOTAL_MESSAGE_SIZE_BYTES, "big"))
    encoded_message.extend(content)

    # Send message
    tx_socket.sendall(encoded_message)

TOTAL_BYTES_WINNER_DOCUMENT = 4

# Send winners to agency
def send_winners(tx_socket, winners_docs):
    message = WINNERS_HEADER.encode("utf-8", errors="ignore")
    header = len(message) + TOTAL_BYTES_WINNER_DOCUMENT * len(winners_docs)

    # Append content to header
    encoded_message = bytearray()
    encoded_message.extend(header.to_bytes(TOTAL_MESSAGE_SIZE_BYTES, "big"))
    encoded_message.extend(message)

    # Store all documents
    for doc in winners_docs:
        encoded_message.extend(int(doc).to_bytes(TOTAL_BYTES_WINNER_DOCUMENT, "big"))

    # Send message
    tx_socket.sendall(encoded_message)