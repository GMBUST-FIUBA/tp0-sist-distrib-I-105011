package common

import (
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	agency_number	uint
	config ClientConfig
	conn   net.Conn
	sigterm_channel	chan	os.Signal
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(agency_number uint, config ClientConfig) *Client {
	client := &Client{
		agency_number: agency_number,
		config: config,
		sigterm_channel: make(chan os.Signal, 1),
	}
	signal.Notify(client.sigterm_channel, syscall.SIGTERM)
	return client
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
func (c *Client) StartClientLoop(bet Bet) {
	// Send bets
	c.createClientSocket()
	select {
	case <-c.sigterm_channel:
		log.Infof("action: client_shutdown | result: success | client_id: %v", c.config.ID)
		return
	default:
		// Send bet
		err := SendBet(c.conn, bet, c.agency_number)
		if err != nil {
			log.Errorf("action: apuesta_enviada | result: failure | dni: %v | numero: %v | error: %v",
				bet.document,
				bet.number,
				err,
			)
			c.conn.Close()
			return
		}
		
	}

	// Receive response
	err := ReadServerResponse(c.conn)

	if err != nil {
		log.Errorf("action: apuesta_enviada | result: failure | dni: %v | numero: %v | error: %v",
			bet.document,
			bet.number,
			err,
		)
		c.conn.Close()
		return
	}

	log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
		bet.document,
		bet.number,
	)
	c.conn.Close()
}
