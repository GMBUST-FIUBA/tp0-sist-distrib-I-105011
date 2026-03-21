from datetime import datetime, date
from .utils import Bet, store_bets
from . import errors

# Birthday format
STRING_BIRTHDAY_FORMAT = '%Y-%m-%d'

# Years to become adult
ADULT_MINIMUM_AGE = 18

# Error messages


class BetManager:
    def __init__(self):
        self.stored_bets = {}
        self.numbers_used = set()

    def store_bets_in_database(self, new_bet: Bet):
        # Check document number
        if int(new_bet.document) <= 0:
            raise errors.NotValidDocumentException()
        
        # Check client age
        if is_adult(new_bet.birthdate) == False:
            raise errors.NotAdultClientException()

        # Check number selected
        if new_bet.number <= 0:
            raise errors.NotValidBetNumberException()

        # Store bet in manager and database
        if new_bet.number not in self.numbers_used:

            if new_bet.document not in self.stored_bets:
                self.stored_bets[new_bet.document] = {}
            
            self.stored_bets[new_bet.document][new_bet.number] = new_bet
            store_bets([new_bet])

        elif new_bet.document in self.stored_bets:
            # Raise exception depending if the client already used the number or not
            if new_bet.number in self.stored_bets[new_bet.document]:
                raise errors.RepeatedBetException()
            else:
                raise errors.AlreadyUsedNumberException()
            



MARCH_MONTH_NUMBER = 3

def is_adult(birthday_date: date):
    current_date = date.today()

    try:
        minimum_date = birthday_date.replace(year=birthday_date.year + ADULT_MINIMUM_AGE)
    except ValueError:
        minimum_date = birthday_date.replace(year=birthday_date.year + ADULT_MINIMUM_AGE, month=MARCH_MONTH_NUMBER, day=1)

    return current_date >= minimum_date