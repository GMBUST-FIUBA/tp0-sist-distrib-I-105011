from .utils import Bet

from . import comm_protocol

# Total message length in bytes
TOTAL_MESSAGE_SIZE_BYTES = 2

# Add bet header
ADD_BET_HEADER = "ADD "

# Correctly processed bet
OK_MESSAGE = "OK"

# Message parts positions
BET_CLIENT_FIRST_NAME_MSG_POS = 0
BET_CLIENT_SURNAME_MSG_POS = 1
BET_CLIENT_DOCUMENT_MSG_POS = 2
BET_CLIENT_BIRTHDAY_MSG_POS = 3
BET_CLIENT_AGENCY_MSG_POS = 4
BET_CLIENT_LOTTERY_NUMBER_MSG_POS = 5

## Bets serialization and deserialization from protocol

# Create new bet
def read_new_bet(rx_socket):
    message = comm_protocol.read_message(rx_socket)

    if message is None:
        return None

    parsed_message = _parse_message(message)

    new_bet = Bet(agency=parsed_message[BET_CLIENT_AGENCY_MSG_POS],
                  first_name=parsed_message[BET_CLIENT_FIRST_NAME_MSG_POS],
                  last_name=parsed_message[BET_CLIENT_SURNAME_MSG_POS],
                  document=parsed_message[BET_CLIENT_DOCUMENT_MSG_POS],
                  birthdate=parsed_message[BET_CLIENT_BIRTHDAY_MSG_POS],
                  number=parsed_message[BET_CLIENT_LOTTERY_NUMBER_MSG_POS])

    return new_bet

def _parse_message(message: str):
    message = message.removeprefix(ADD_BET_HEADER)
    split_message = message.split(',')
    return split_message


## Bytes management from input/output

# Reads message according to protocol defined on Readme.
def read_message(rx_socket):
    # Reads header for message size
    message_size = _read_message_header(rx_socket)

    # Reads message's content
    message = _read_message_content(rx_socket, message_size)
    
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
    return content.decode("utf-8", errors="ignore")

# Returns None if sender disconnects
def __read_n_bytes(rx_socket, n_bytes):
    data = bytearray()
    remaining_bytes = n_bytes
    while n_bytes > 0:
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