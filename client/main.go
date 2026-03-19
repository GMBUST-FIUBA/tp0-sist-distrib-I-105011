package main

import (
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/op/go-logging"
	"github.com/pkg/errors"
	"github.com/spf13/viper"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common"
)

var log = logging.MustGetLogger("log")

const STORED_BETS_FILE_PATH = "./data/test_client_bet.env"

// InitConfig Function that uses viper library to parse configuration parameters.
// Viper is configured to read variables from both environment variables and the
// config file ./config.yaml. Environment variables takes precedence over parameters
// defined in the configuration file. If some of the variables cannot be parsed,
// an error is returned
func InitConfig() (*viper.Viper, error) {
	v := viper.New()

	v.AutomaticEnv()

	// Configure viper to read bets from env file
	v.SetConfigFile(STORED_BETS_FILE_PATH)
	v.SetConfigType("env")
	if err := v.ReadInConfig(); err != nil {
		fmt.Printf("Configuration could find environment file")
	}

	// Configure viper to read env variables with the CLI_ prefix
	v.SetEnvPrefix("cli")
	// Use a replacer to replace env variables underscores with points. This let us
	// use nested configurations in the config file and at the same time define
	// env variables for the nested configurations
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

	// Add env variables supported
	v.BindEnv("id")
	v.BindEnv("server", "address")
	v.BindEnv("loop", "period")
	v.BindEnv("loop", "amount")
	v.BindEnv("log", "level")

	// Try to read configuration from config file. If config file
	// does not exists then ReadInConfig will fail but configuration
	// can be loaded from the environment variables so we shouldn't
	// return an error in that case
	v.SetConfigFile("./volumes/client_config.yaml")
	if err := v.ReadInConfig(); err != nil {
		fmt.Printf("Configuration could not be read from config file. Using env variables instead")
	}

	// Parse time.Duration variables and return an error if those variables cannot be parsed

	if _, err := time.ParseDuration(v.GetString("loop.period")); err != nil {
		return nil, errors.Wrapf(err, "Could not parse CLI_LOOP_PERIOD env var as time.Duration.")
	}

	return v, nil
}

// InitLogger Receives the log level to be set in go-logging as a string. This method
// parses the string and set the level to the logger. If the level string is not
// valid an error is returned
func InitLogger(logLevel string) error {
	baseBackend := logging.NewLogBackend(os.Stdout, "", 0)
	format := logging.MustStringFormatter(
		`%{time:2006-01-02 15:04:05} %{level:.5s}     %{message}`,
	)
	backendFormatter := logging.NewBackendFormatter(baseBackend, format)

	backendLeveled := logging.AddModuleLevel(backendFormatter)
	logLevelCode, err := logging.LogLevel(logLevel)
	if err != nil {
		return err
	}
	backendLeveled.SetLevel(logLevelCode, "")

	// Set the backends to be used.
	logging.SetBackend(backendLeveled)
	return nil
}

// PrintConfig Print all the configuration parameters of the program.
// For debugging purposes only
func PrintConfig(v *viper.Viper) {
	log.Infof("action: config | result: success | client_id: %s | server_address: %s | loop_amount: %v | loop_period: %v | log_level: %s",
		v.GetString("id"),
		v.GetString("server.address"),
		v.GetInt("loop.amount"),
		v.GetDuration("loop.period"),
		v.GetString("log.level"),
	)
}

// Read bets from environment variables
func ReadOrderedBets(v *viper.Viper) []common.Bet {
	// Get all bets keys from env file
	var bets_keys []string
	for _, key := range v.AllKeys() {
        if strings.HasPrefix(key, "bet") {
            bets_keys = append(bets_keys, key)
        }
    }

	// Sort bets
	sort.Strings(bets_keys)

	// Get bets from env file
	var stored_bets_env_file []string
	for _, key := range bets_keys {
		stored_bets_env_file = append(stored_bets_env_file, viper.GetString(key))
	}

	// Create bet structures
	var bets []common.Bet
	for _, stored_bet_str := range stored_bets_env_file {
		new_bet := common.CreateBetFromEnvFileString(stored_bet_str)
		bets = append(bets, new_bet)
	}

	return bets
}

func main() {
	v, err := InitConfig()
	if err != nil {
		log.Criticalf("%s", err)
	}

	if err := InitLogger(v.GetString("log.level")); err != nil {
		log.Criticalf("%s", err)
	}

	// Print program config with debugging purposes
	PrintConfig(v)

	clientConfig := common.ClientConfig{
		ServerAddress: v.GetString("server.address"),
		ID:            v.GetString("id"),
		LoopAmount:    v.GetInt("loop.amount"),
		LoopPeriod:    v.GetDuration("loop.period"),
	}

	// Read agency ID
	agency_number_str,_ := strconv.Atoi(v.GetString("agency"))
	agency_number := uint(agency_number_str)

	// Read and order bets
	bets = ReadOrderedBets(v)

	client := common.NewClient(agency_number, clientConfig)
	client.StartClientLoop()
}
