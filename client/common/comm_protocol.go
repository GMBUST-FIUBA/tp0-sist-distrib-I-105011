package common

import (
	"encoding/binary"
	"io"
	"net"
)

const ADD_BET_MSG_HEADER = "ADD "

func SendBet(socket net.Conn, bet Bet, agency_number uint) error {
	// Create content
	var content []byte
	content = append(content, []byte(ADD_BET_MSG_HEADER)...)
	serialized_bet := bet.TurnToBytes(agency_number)
	content = append(content, serialized_bet...)
	
	// Calculate total message length
	total_length_bytes := binary.BigEndian.AppendUint16(nil, uint16(len(content)))

	// Create new message
	var message []byte
	message = append(message, total_length_bytes...)
	message = append(message, content...)

	// Send bytes from socket
	return SendBytes(socket, message)
}

// Allows to send array of bytes
func SendBytes(socket net.Conn, bytes_to_send []byte) error {
	total_sent_bytes := 0

	// Send bytes taking into account the number of bytes sent
	for total_sent_bytes < len(bytes_to_send) {
		bytes_sent, err := socket.Write(bytes_to_send[total_sent_bytes:])
		if err != nil {
			return &CommunicationError{"Socket error"}
		}
		total_sent_bytes += bytes_sent
	}

	return nil
}

const TOTAL_MSG_HEADER_BYTES = 2

// Reads response from server
func ReadServerResponse(socket net.Conn) error {
	return nil
}

// Receive bytes from server
func readMessageHeader(socket net.Conn, total_bytes uint) (uint16, error) {
	var message_size uint16

	// Read message header
	err := binary.Read(socket, binary.BigEndian, &message_size)
	if err != nil {
		return 0, &CommunicationError{"Socket error"}
	}
	return message_size, nil
}

func readMessageContent(socket net.Conn, total_bytes uint16) (string, error) {
	buffer := make([]byte, total_bytes)

	// Read all bytes expected
	_, err := io.ReadFull(socket, buffer)
	if err != nil {
		return "", &CommunicationError{"Socket error"}
	}
	return string(buffer), nil
}
