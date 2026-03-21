package client_errors

type DefaultError struct {
	msg string
}

func (e *DefaultError) Error() string {
	return e.msg
}

func NewDefaultError(msg string) *DefaultError {
	return &DefaultError{msg}
}