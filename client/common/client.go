package common

import (
	"encoding/binary"
	"encoding/csv"
	"io"
	"net"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	agency_commands "github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/commands"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// Constants
const BASE_AGENCY_BETS_FILE_PATH = "/volumes/agency-"
const AGENCY_BETS_FILE_TYPE = ".csv"

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	BatchMaxSize  uint
}

// Client Entity that encapsulates how
type Client struct {
	agency_number	uint
	config ClientConfig
	conn   net.Conn
	file_reader *csv.Reader
	sigterm_channel	chan	os.Signal
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(agency_number uint, config ClientConfig) (*Client, error) {
	// Open bets file
	file_reader, err := openBetsFile(agency_number)
	if err != nil {
		return nil, err
	}
	// Create client
	client := &Client{
		agency_number: agency_number,
		config: config,
		file_reader: file_reader,
		sigterm_channel: make(chan os.Signal, 1),
	}
	signal.Notify(client.sigterm_channel, syscall.SIGTERM)
	return client, nil
}

// Open bets file
func openBetsFile(agency_number uint) (*csv.Reader, error) {
	// Create file path
	file_path := BASE_AGENCY_BETS_FILE_PATH + strconv.FormatUint(uint64(agency_number), 10) + AGENCY_BETS_FILE_TYPE
	// Get file descriptor
	file, err := os.Open(file_path)
	if err != nil {
		return nil, err
	}
	// Get csv reader
	csv_reader := csv.NewReader(file)
	return csv_reader, nil
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// Send bets
	c.createClientSocket()
	continue_reading_batches := true

	// Close socket when exiting
	defer c.conn.Close()

	// Send all bets by batches
	for continue_reading_batches {
		select {
		case <-c.sigterm_channel:
			log.Infof("action: client_shutdown | result: success | client_id: %v", c.config.ID)
			c.conn.Close()
			return
		default:
		}

		next_batch, err := c.readNextBetsBatch()
		if err == io.EOF {
			continue_reading_batches = false
		} else if err != nil {
			log.Errorf("action: lectura_batch | result: failure | error: %v",
				err,
			)
		}
		// Send bets batch
		err = SendBetsBatch(c.conn, next_batch, c.agency_number)
		if err != nil {
			log.Errorf("action: apuestas_enviadas | result: fail | cantidad: %v",
				len(next_batch),
			)
			return
		}
		// Receive response
		resp, err := ReadServerResponse(c.conn)

		if err != nil || resp.CommandType == agency_commands.Ok {
			log.Errorf("action: apuestas_enviadas | result: fail | cantidad: %v",
				len(next_batch),
			)
			return
		}

		log.Infof("action: apuestas_enviadas | result: success | cantidad: %v",
			len(next_batch),
		)
	}

	// Send end of bets transmission
	SendEndTxBets(c.conn, c.agency_number)

	// Wait for winners
	resp, _ := ReadServerResponse(c.conn)
	if resp.CommandType == agency_commands.Winners {
		winners_list := getWinnersCommand(resp)
		log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %v",
			len(winners_list),
		)
	} else {
		log.Infof("action: consulta_ganadores | result: failure")
	}
}

func (c *Client) readNextBetsBatch() ([]Bet, error) {
	var new_batch []Bet
	var return_err error = nil
	for i := 0; i < int(c.config.BatchMaxSize); i++ {
		new_bet_str, err := c.file_reader.Read()
		if err == io.EOF {
			return_err = err
			break
		}
		new_bet := CreateBetFromCsvFile(new_bet_str)
		new_batch = append(new_batch, new_bet)
	}
	return new_batch, return_err
}

// Get winners from response
const DOCUMENT_LENGTH_BYTES = 4

func getWinnersCommand(command *agency_commands.AgencyCommand) []uint32 {
	total_winners := len(command.Arg) / DOCUMENT_LENGTH_BYTES
	var winners_docs []uint32
	for i := 0; i < total_winners; i++ {
		winner_doc_bytes := command.Arg[i: i+DOCUMENT_LENGTH_BYTES]
		winner_doc := binary.BigEndian.Uint32(winner_doc_bytes)
		winners_docs = append(winners_docs, winner_doc)
	}
	return winners_docs
}