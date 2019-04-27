class UpdateColumnStrategy:
    pass


class EmptyUpdateColumnStrategy(UpdateColumnStrategy):
    pass


class UniqueLoginUpdateColumnStrategy(UpdateColumnStrategy):
    pass


class UniqueEmailUpdateColumnStrategy(UpdateColumnStrategy):
    pass


class FakeUpdateColumnStrategy(UpdateColumnStrategy):
    def __init__(self, fake_type):
        self.fake_type = fake_type
