package client_errors

type TakenNumberError struct {
	msg string
}

func (e *TakenNumberError) Error() string {
	return e.msg
}

func NewTakenNumberError(msg string) *TakenNumberError {
	return &TakenNumberError{msg}
}