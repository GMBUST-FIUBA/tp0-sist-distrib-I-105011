package agency_commands

type AgencyCommand struct {
	CommandType AgencyCommandType
	Arg []byte
}

func NewOkCommand() *AgencyCommand {
	return &AgencyCommand{CommandType: Ok}
}

func NewWinnersCommand(winners []byte) *AgencyCommand {
	return &AgencyCommand{CommandType: Winners, Arg: winners}
}