package common

import (
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"strconv"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/commands"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/errors"
)

// Ok message
const OK_MESSAGE = 0

// Winner message
const WINNERS_MESSAGE = 87

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

// Add bets batch header message
const ADD_BETS_BATCH_MSG_HEADER = "B"

// End of bets transmission
const END_OF_BETS_MSG_HEADER = "E"

// Winners from server
const WINNERS_MSG_HEADER = "W"

// End of bets transmission
const END_OF_BETS_HEADER = "END "

// Winners from server
const WINNERS_HEADER = "WIN "

// Header length in bytes
const TOTAL_MSG_HEADER_BYTES = 2

// Batch total bets length in bytes
const TOTAL_BETS_BATCH_HEADER_BYTES = 1

// Agency number in batch message in bytes
const AGENCY_NUMBER_BATCH_HEADER_BYTES = 1

// Calculate package length according to protocol
func calcPackageLength(packet []byte) []byte {
	total_length_bytes := make([]byte, TOTAL_MSG_HEADER_BYTES)
	binary.BigEndian.PutUint16(total_length_bytes, uint16(len(packet)))
	return total_length_bytes
}

// Serialize message
func CreateMessage(content []byte) []byte {
	// Calculate total message length
	total_length_bytes := calcPackageLength(content)

	// Create new message
	var message []byte
	message = append(message, total_length_bytes...)
	message = append(message, content...)
	return message
}


// Send bet to server
func SendBet(socket net.Conn, bet Bet, agency_number uint) error {
	// Create content
	var content []byte
	content = append(content, []byte(ADD_BET_MSG_HEADER)...)
	serialized_bet := bet.TurnToBytes(agency_number)
	content = append(content, serialized_bet...)

	// Create new message
	message := CreateMessage(content)

	// Send bytes from socket
	return SendBytes(socket, message)
}

// Send bets batch
func SendBetsBatch(socket net.Conn, bets []Bet, agency_number uint) error {
	// Create message content
	var bets_to_bytes []byte
	// Iterate over bets batch
	bets_to_bytes = append(bets_to_bytes, []byte(ADD_BETS_BATCH_MSG_HEADER)...)
	for pos, bet := range bets {
		serialized_bet := bet.TurnToBatchBytes(agency_number)
		bets_to_bytes = append(bets_to_bytes, serialized_bet...)
		if pos + 1 < len(bets) {
			bets_to_bytes = append(bets_to_bytes, ';')
		}
	}

	// Get total bets in bytes
	total_bets_bytes := byte(len(bets))

	// Get agency number in bytes
	agency_number_bytes := byte(agency_number)

	// Create message content
	message_content := []byte(ADD_BETS_BATCH_MSG_HEADER)

	message_content = append(message_content, total_bets_bytes)
	message_content = append(message_content, agency_number_bytes)
	message_content = append(message_content, bets_to_bytes...)

	// Create new message
	message := CreateMessage(message_content)

	// Send bytes from socket
	return SendBytes(socket, message)
}

// Send end of bets transmission
func SendEndTxBets(socket net.Conn, agency_number uint) error {
	message_content := END_OF_BETS_MSG_HEADER
	message_content += strconv.FormatUint(uint64(agency_number), 10)
	message_content_bytes := []byte(message_content)

	// Create new message
	message := CreateMessage(message_content_bytes)

	// Send bytes
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
func ReadServerResponse(socket net.Conn) (*agency_commands.AgencyCommand, error) {
	// Read message header
	total_msg_size, err := readMessageHeader(socket)
	if err != nil {
		return nil, err
	}
	// Read message content
	content, err := readMessageContent(socket, total_msg_size)
	if err != nil {
		return nil, err
	}

	// Return response
	return processServerResponse(content)
}

// Generate error according to response or nil if it is ok
func processServerResponse(content []byte) (*agency_commands.AgencyCommand, error) {
	command_type := content[0]
	rest_command := content[1:]

	if command_type == OK_MESSAGE {
		fmt.Println("Se recibió OK")
		return agency_commands.NewOkCommand(), nil
	} else if command_type == WINNERS_MESSAGE {
		fmt.Println("Se recibieron los ganadores")
		return agency_commands.NewWinnersCommand(rest_command), nil
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
	default:
		fmt.Println(("Error desconocido"))
	}
	fmt.Println("Error recibido: ", error_received)
	return nil, error_received
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
