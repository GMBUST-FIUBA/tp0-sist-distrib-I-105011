package common

import (
	"strconv"
	"strings"
)

type Bet struct {
	first_name	string
	last_name	string
	document	uint
	birthday	string
	number		uint
}

const FIRST_NAME_ENV_FILE_ROW_POS = 0
const LAST_NAME_ENV_FILE_ROW_POS = 1
const DOCUMENT_ENV_FILE_ROW_POS = 2
const BIRTHDAY_ENV_FILE_ROW_POS = 3
const NUMBER_ENV_FILE_ROW_POS = 4

func CreateBetFromEnvFileString(stored_bet string) Bet {
	split_stored_bet := strings.Split(stored_bet, ",")

	document, _ := strconv.Atoi(split_stored_bet[DOCUMENT_ENV_FILE_ROW_POS])
	number, _ := strconv.Atoi(split_stored_bet[NUMBER_ENV_FILE_ROW_POS])

	return Bet{
		first_name: split_stored_bet[FIRST_NAME_ENV_FILE_ROW_POS],
		last_name: split_stored_bet[LAST_NAME_ENV_FILE_ROW_POS],
		document: uint(document),
		birthday: split_stored_bet[BIRTHDAY_ENV_FILE_ROW_POS],
		number: uint(number),
	}
}