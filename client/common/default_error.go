package common

type DefaultError struct {
	msg string
}

func (e *DefaultError) Error() string {
	return e.msg
}