package common

type NotValidDocumentError struct {
	msg string
}

func (e *NotValidDocumentError) Error() string {
	return e.msg
}