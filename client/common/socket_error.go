package common

type CommunicationError struct {
	msg string
}

func (e *CommunicationError) Error() string {
	return e.msg
}