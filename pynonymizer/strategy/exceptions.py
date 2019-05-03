class UnknownUpdateColumnFakeTypeError(Exception):
    def __init__(self, config):
        self.config = config
        super().__init__("Unknown fake column type: {}".format(config))


class UnknownTableStrategyError(Exception):
    def __init__(self, config):
        self.config = config
        super().__init__("Unable to determine table strategy from value: {}".format(config))


class UnknownColumnStrategyError(Exception):
    def __init__(self, config):
        self.config = config
        super().__init__("Unable to determine column strategy from value: {}".format(config))