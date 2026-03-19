package common

type RepeatedBetError struct {
	msg string
}

func (e *RepeatedBetError) Error() string {
	return e.msg
}