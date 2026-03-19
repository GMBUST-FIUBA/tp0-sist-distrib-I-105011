NOT_ADULT_CLIENT_MSG = "ERR NOT_ADULT"
NUMBER_ALREADY_TAKEN_MSG = "ERR NUMBER_TAKEN"
REPEATED_BET_MSG = "ERR REPEATED_BET"
NOT_VALID_NUMBER_MSG = "ERR NOT_VALID_NUMBER"
NOT_VALID_DOC_MSG = "ERR NOT_VALID_DNI"

class NotAdultClientException:
    def __init__(self, message=NOT_ADULT_CLIENT_MSG, *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class AlreadyUsedNumberException:
    def __init__(self, message=NUMBER_ALREADY_TAKEN_MSG, *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class RepeatedBetException:
    def __init__(self, message=REPEATED_BET_MSG, *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class NotValidBetNumberException:
    def __init__(self, message=NOT_VALID_NUMBER_MSG, *args, **kwargs):
        super().__init__(message, *args, **kwargs)

class NotValidDocumentException:
    def __init__(self, message=NOT_VALID_DOC_MSG, *args, **kwargs):
        super().__init__(message, *args, **kwargs)