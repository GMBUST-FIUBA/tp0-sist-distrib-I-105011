package common

import (
	"strconv"
	"strings"

	"github.com/spf13/viper"
)

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

func CreateBetFromEnvFile(v *viper.Viper) Bet {
	document, _ := strconv.Atoi(v.GetString("document"))
	number, _ := strconv.Atoi(v.GetString("number"))

	return Bet{
		first_name: v.GetString("first_name"),
		last_name: v.GetString("last_name"),
		document: document,
		birthday: v.GetString("birthday"),
		number: number,
	}
}