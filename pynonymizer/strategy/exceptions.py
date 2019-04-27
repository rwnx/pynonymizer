class UnknownUpdateColumnFakeTypeError(Exception):
    def __init__(self, config):
        self.config = config
        super().__init__("Unknown fake column type: {}".format(config))


class UnknownTableStrategyError:
    def __init__(self, config):
        self.config = config
        super().__init__("Unable to determine table strategy from value: {}".format(config))


class UnknownColumnStrategyError:
    def __init__(self, config):
        self.config = config
        super().__init__("Unable to determine column strategy from value: {}".format(config))