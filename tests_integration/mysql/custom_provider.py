from faker.providers import BaseProvider
from faker import Faker


class CustomProvider(BaseProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker()

    def name_email(self):
        fname = self.faker.first_name()
        lname = self.faker.last_name()
        return f"{fname} {lname} <{fname}.{lname}@example.com>"
