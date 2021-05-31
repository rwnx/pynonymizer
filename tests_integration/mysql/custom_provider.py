from faker.providers import BaseProvider

from faker.providers.person import Provider as PersonProvider

class CustomProvider(BaseProvider):
  def name_email():
    fname = PersonProvider.first_name()
    lname = PersonProvider.last_name()
    return f"{fname}_{lname} <{fname}.{lname}@example.com>"
