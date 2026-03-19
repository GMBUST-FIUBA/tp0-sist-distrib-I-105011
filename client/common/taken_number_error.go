package common

type TakenNumberError struct {
	msg string
}

func (e *TakenNumberError) Error() string {
	return e.msg
}