TOTAL_MESSAGE_SIZE_BYTES = 2

# Reads message according to protocol defined on Readme.
def read_message(rx_socket):
    # Reads header for message size
    message_size = _read_message_header(rx_socket)

    # Reads message's content
    message = _read_message_content(rx_socket, message_size)
    
    return message

def _read_message_header(rx_socket):
    header = __read_n_bytes(rx_socket, TOTAL_MESSAGE_SIZE_BYTES)
    if header is None:
        return None
    return int.from_bytes(header, byteorder="big")

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
    encoded_message.extend(header)
    encoded_message.extend(content)

    # Send message
    tx_socket.sendall(encoded_message)