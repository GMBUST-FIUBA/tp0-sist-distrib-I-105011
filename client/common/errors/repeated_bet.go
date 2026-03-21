package client_errors

type RepeatedBetError struct {
	msg string
}

func (e *RepeatedBetError) Error() string {
	return e.msg
}

func NewRepeatedBetError(msg string) *RepeatedBetError {
	return &RepeatedBetError{msg}
}