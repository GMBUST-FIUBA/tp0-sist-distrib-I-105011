package common

import (
	"strconv"
	"strings"
)

// Stored bets parts positions
const FIRST_NAME_CSV_FILE_POS = 0
const LAST_NAME_CSV_FILE_POS = 1
const DOCUMENT_CSV_FILE_POS = 2
const BIRTHDAY_CSV_FILE_POS = 3
const BET_NUMBER_CSV_FILE_POS = 4

type Bet struct {
	first_name	string
	last_name	string
	document	int
	birthday	string
	number		int
}

func (b *Bet) TurnToBytes(agency_number uint) []byte {
	const SEPARATOR = ","
	var byte_array_bet strings.Builder

	// Append all parts of bet according to protocol
	byte_array_bet.WriteString(b.first_name)
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(b.last_name)
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(strconv.FormatInt(int64(b.document), 10))
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(b.birthday)
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(strconv.FormatUint(uint64(agency_number), 10))
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(strconv.FormatInt(int64(b.number), 10))

	return []byte(byte_array_bet.String())
}

func (b *Bet) TurnToBatchBytes(agency_number uint) []byte {
	const SEPARATOR = ","
	var byte_array_bet strings.Builder

	// Append all parts of bet according to protocol
	byte_array_bet.WriteString(b.first_name)
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(b.last_name)
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(strconv.FormatInt(int64(b.document), 10))
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(b.birthday)
	byte_array_bet.WriteString(SEPARATOR)
	byte_array_bet.WriteString(strconv.FormatInt(int64(b.number), 10))

	return []byte(byte_array_bet.String())
}

func CreateBetFromCsvFile(bet_stored []string) Bet {
	document, _ := strconv.Atoi(bet_stored[DOCUMENT_CSV_FILE_POS])
	number, _ := strconv.Atoi(bet_stored[BET_NUMBER_CSV_FILE_POS])

	return Bet{
		first_name: bet_stored[FIRST_NAME_CSV_FILE_POS],
		last_name: bet_stored[LAST_NAME_CSV_FILE_POS],
		document: document,
		birthday: bet_stored[BIRTHDAY_CSV_FILE_POS],
		number: number,
	}
}