class CommunicationException:
    """Raised when there is an error in the socket."""
    pass

class NotAdultClientException:
    """Raised when the client is a minor."""
    pass

class AlreadyUsedNumberException:
    """Raised when a number is taken by another person."""
    pass

class RepeatedBetException:
    """Raised when the client already betted on a number and wants to do it again."""
    pass

class NotValidBetNumberException:
    """Raised when the bet number is not valid."""
    pass

class NotValidDocumentException:
    """Raised when the document number is not valid."""
    pass