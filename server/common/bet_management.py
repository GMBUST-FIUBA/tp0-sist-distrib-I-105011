from datetime import datetime, date
from .utils import Bet, store_bets, load_bets, has_won
from . import errors

import logging

# Birthday format
STRING_BIRTHDAY_FORMAT = '%Y-%m-%d'

# Years to become adult
ADULT_MINIMUM_AGE = 18

# Error messages


class BetManager:
    def __init__(self):
        self.staged_bets_numbers = set()
        self.staged_bets = {}

        self.sockets_to_agencies = {}

    # Store single bet
    def store_bet_in_database(self, new_bet: Bet):
        # Stage bet
        self.__stage_bet(new_bet)
        # Store bet
        self.__store_staged_bets()

    # Store batch of bets
    def store_bets_batch(self, bets: list[Bet]):
        # Stage all bets
        for bet in bets:
            try:
                self.__stage_bet(bet)
            except Exception as e:
                self.__erase_staged_bets()
                logging.error(f"apuesta_recibida | result: fail | cantidad: {len(bets)}")
                raise errors.WrongBatchException(str(e))
        # Store staged bets
        self.__store_staged_bets()

    def __stage_bet(self, new_bet):
        # Check document number
        if int(new_bet.document) < 0:
            raise errors.NotValidDocumentException()
        
        # Check client age
        if is_adult(new_bet.birthdate) == False:
            raise errors.NotAdultClientException()

        # Check number selected
        if new_bet.number < 0:
            raise errors.NotValidBetNumberException()

        # Store bet in manager and database
        if new_bet.document not in self.staged_bets:
            self.staged_bets[new_bet.document] = {}

        # Stage bets
        self.staged_bets[new_bet.document][new_bet.number] = new_bet

    def __store_staged_bets(self):
        # Store bets in memory
        all_staged_bets = [bet for bets_by_number in self.staged_bets.values() for bet in bets_by_number.values()]
        store_bets(all_staged_bets)

        # Erase staged bets
        self.__erase_staged_bets()

    def __erase_staged_bets(self):
        self.staged_bets = {}

    def load_winners(self, total_agencies):
        all_bets = load_bets()

        # Set empty lists for winners
        winners = { agency : [] for agency in range(1, total_agencies + 1) }

        # Store all winners
        for bet in all_bets:
            if has_won(bet):
                winners[bet.agency].append(bet.document)

        return winners


MARCH_MONTH_NUMBER = 3

def is_adult(birthday_date: date):
    current_date = date.today()

    try:
        minimum_date = birthday_date.replace(year=birthday_date.year + ADULT_MINIMUM_AGE)
    except ValueError:
        minimum_date = birthday_date.replace(year=birthday_date.year + ADULT_MINIMUM_AGE, month=MARCH_MONTH_NUMBER, day=1)

    return current_date >= minimum_date