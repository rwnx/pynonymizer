from pynonymizer.exceptions import PynonymizerError


class StrategyError(PynonymizerError):
    pass


class UnknownUpdateColumnFakeTypeError(StrategyError):
    def __init__(self, config):
        self.config = config
        super().__init__("Unknown fake column type: {}".format(config))


class UnknownTableStrategyError(StrategyError):
    def __init__(self, config):
        self.config = config
        super().__init__(
            "Unable to determine table strategy from value: {}".format(config)
        )


class UnknownColumnStrategyError(StrategyError):
    def __init__(self, config):
        self.config = config
        super().__init__(
            "Unable to determine column strategy from value: {}".format(config)
        )


class ConfigSyntaxError(StrategyError):
    pass
