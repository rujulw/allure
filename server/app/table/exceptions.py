class TableError(Exception):
    """Base exception for table-domain validation failures."""


class TableNotFoundError(TableError):
    pass


class SeatOccupiedError(TableError):
    pass


class InvalidSeatError(TableError):
    pass


class InvalidBuyInError(TableError):
    pass


class DuplicatePlayerError(TableError):
    pass


class PlayerNotAtTableError(TableError):
    pass


class PlayerAlreadySeatedError(TableError):
    pass


class RejoinNotAvailableError(TableError):
    pass


class HandStartError(TableError):
    pass
