package common

type NotAdultClientError struct {
	msg string
}

func (e *NotAdultClientError) Error() string {
	return e.msg
}