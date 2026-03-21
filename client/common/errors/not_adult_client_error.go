package client_errors

type NotAdultClientError struct {
	msg string
}

func (e *NotAdultClientError) Error() string {
	return e.msg
}

func NewNotAdultClientError(msg string) *NotAdultClientError {
	return &NotAdultClientError{msg}
}