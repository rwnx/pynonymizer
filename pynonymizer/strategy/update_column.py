class UnsupportedFakeTypeError(Exception):
    def __init__(self, fake_type):
        super().__init__(f"Unsupported Fake type: {fake_type}")
        self.fake_type = fake_type


class UpdateColumnStrategy:
    pass


class EmptyUpdateColumnStrategy(UpdateColumnStrategy):
    pass


class UniqueLoginUpdateColumnStrategy(UpdateColumnStrategy):
    pass


class UniqueEmailUpdateColumnStrategy(UpdateColumnStrategy):
    pass


class FakeUpdateColumnStrategy(UpdateColumnStrategy):
    def __init__(self, fake_seeder, fake_type):
        if not fake_seeder.supports_fake_type(fake_type):
            raise UnsupportedFakeTypeError(fake_type)
        self.fake_type = fake_type
