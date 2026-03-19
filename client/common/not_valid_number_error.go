package common

type NotValidNumberError struct {
	msg string
}

func (e *NotValidNumberError) Error() string {
	return e.msg
}