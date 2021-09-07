class PynonymizerError(Exception):
    """
    A base error class for this application.
    """

    pass


class ArgumentValidationError(PynonymizerError):
    def __init__(self, validation_messages):
        self.validation_messages = validation_messages


class DatabaseConnectionError(PynonymizerError):
    pass
