package client_errors

type NotValidNumberError struct {
	msg string
}

func (e *NotValidNumberError) Error() string {
	return e.msg
}

func NewNotValidNumberError(msg string) *NotValidNumberError {
	return &NotValidNumberError{msg}
}