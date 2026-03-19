package common

import (
	"encoding/binary"
	"io"
	"net"
	"strings"
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

// Messages
const OK_MESSAGE = "OK"

// Prefixes
const ERROR_MESSAGE_PREFIX = "ERR "

// Error messages
const NOT_ADULT_CLIENT_ERR_MSG = "NOT_ADULT"
const NUMBER_TAKEN_ERR_MSG = "NUMBER_TAKEN"
const REPEATED_BET_ERR_MSG = "REPEATED_BET"
const NOT_VALID_NUMBER_ERR_MSG = "NOT_VALID_NUMBER"
const NOT_VALID_DOCUMENT_ERR_MSG = "NOT_VALID_DNI"

// Generate error according to response or nil if it is ok
func processServerResponse(content string) error {
	if content == OK_MESSAGE {
		return nil
	}
	// Check error type
	err_message := strings.TrimPrefix(content, ERROR_MESSAGE_PREFIX)
	switch err_message {
	case NOT_ADULT_CLIENT_ERR_MSG:
		return &NotAdultClientError{"Underage client"}
	case NUMBER_TAKEN_ERR_MSG:
		return &TakenNumberError{"Number already taken"}
	case REPEATED_BET_ERR_MSG:
		return &RepeatedBetError{"Repeated bet"}
	case NOT_VALID_NUMBER_ERR_MSG:
		return &NotValidNumberError{"Not valid number"}
	case NOT_VALID_DOCUMENT_ERR_MSG:
		return &NotValidDocumentError{"Not valid document"}
	default:
		return &DefaultError{err_message}
	}
}

// Receive bytes from server
func readMessageHeader(socket net.Conn) (uint16, error) {
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
