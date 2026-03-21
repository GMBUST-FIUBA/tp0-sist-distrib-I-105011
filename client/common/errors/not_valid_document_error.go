package client_errors

type NotValidDocumentError struct {
	msg string
}

func (e *NotValidDocumentError) Error() string {
	return e.msg
}

func NewNotValidDocumentError(msg string) *NotValidDocumentError {
	return &NotValidDocumentError{msg}
}