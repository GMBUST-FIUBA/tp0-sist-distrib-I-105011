package client_errors

type CommunicationError struct {
	msg string
}

func (e *CommunicationError) Error() string {
	return e.msg
}

func NewCommunicationError(msg string) *CommunicationError {
	return &CommunicationError{msg}
}