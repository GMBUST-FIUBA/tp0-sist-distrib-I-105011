package common

import (
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/errors"
	"encoding/binary"
	"io"
	"net"
)

// Ok message
const OK_MESSAGE = 0

// Errors messages for logs
const LOG_SOCKET_ERROR_MSG = "Socket error"
const LOG_NOT_ADULT_ERROR_MSG = "Underage client"
const LOG_BET_NUMBER_TAKEN_ERROR_MSG = "Number already taken"
const LOG_REPEATED_BET_ERROR_MSG = "Repeated bet"
const LOG_NOT_VALID_BET_NUMBER_ERROR_MSG = "Not valid bet number"
const LOG_NOT_VALID_DOC_ERROR_MSG = "Not valid document"


// Error types
const NOT_ADULT_CLIENT_ERR_TYPE = 1
const NUMBER_TAKEN_ERR_TYPE = 2
const REPEATED_BET_ERR_TYPE = 3
const NOT_VALID_NUMBER_ERR_TYPE = 4
const NOT_VALID_DOCUMENT_ERR_TYPE = 5

// Add bet header message
const ADD_BET_MSG_HEADER = "A"

// Header length in bytes
const TOTAL_MSG_HEADER_BYTES = 2

// Send bet to server
func SendBet(socket net.Conn, bet Bet, agency_number uint) error {
	// Create content
	var content []byte
	content = append(content, []byte(ADD_BET_MSG_HEADER)...)
	serialized_bet := bet.TurnToBytes(agency_number)
	content = append(content, serialized_bet...)
	
	// Calculate total message length
	total_length_bytes := make([]byte, TOTAL_MSG_HEADER_BYTES)
	binary.BigEndian.PutUint16(total_length_bytes, uint16(len(content)))

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
			return client_errors.NewCommunicationError(LOG_SOCKET_ERROR_MSG)
		}
		total_sent_bytes += bytes_sent
	}

	return nil
}

// Reads response from server
func ReadServerResponse(socket net.Conn) error {
	// Read message header
	total_msg_size, err := readMessageHeader(socket)
	if err != nil {
		return err
	}
	// Read message content
	content, err := readMessageContent(socket, total_msg_size)
	if err != nil {
		return err
	}

	// Return response
	return processServerResponse(content)
}

// Generate error according to response or nil if it is ok
func processServerResponse(content []byte) error {
	command_type := content[0]

	if command_type == OK_MESSAGE {
		return nil
	}
	// Check error type
	var error_received error
	switch command_type {
	case NOT_ADULT_CLIENT_ERR_TYPE:
		error_received = client_errors.NewNotAdultClientError(LOG_NOT_ADULT_ERROR_MSG)
	case NUMBER_TAKEN_ERR_TYPE:
		error_received = client_errors.NewTakenNumberError(LOG_BET_NUMBER_TAKEN_ERROR_MSG)
	case REPEATED_BET_ERR_TYPE:
		error_received = client_errors.NewRepeatedBetError(LOG_REPEATED_BET_ERROR_MSG)
	case NOT_VALID_NUMBER_ERR_TYPE:
		error_received = client_errors.NewNotValidNumberError(LOG_NOT_VALID_BET_NUMBER_ERROR_MSG)
	case NOT_VALID_DOCUMENT_ERR_TYPE:
		error_received = client_errors.NewNotValidDocumentError(LOG_NOT_VALID_DOC_ERROR_MSG)
	}
	return error_received
}

// Receive bytes from server
func readMessageHeader(socket net.Conn) (uint16, error) {
	var message_size uint16

	// Read message header
	err := binary.Read(socket, binary.BigEndian, &message_size)
	if err != nil {
		return 0, client_errors.NewCommunicationError(LOG_SOCKET_ERROR_MSG)
	}
	return message_size, nil
}

func readMessageContent(socket net.Conn, total_bytes uint16) ([]byte, error) {
	buffer := make([]byte, total_bytes)

	// Read all bytes expected
	_, err := io.ReadFull(socket, buffer)
	if err != nil {
		return nil, client_errors.NewCommunicationError(LOG_SOCKET_ERROR_MSG)
	}
	return buffer, nil
}
