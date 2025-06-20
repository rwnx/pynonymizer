# Pynonymizer Anonymization Syntax Guide

A comprehensive guide to all anonymization strategies and syntax available for creating realistic anonymized database dumps while maintaining GDPR compliance.

## Overview

Pynonymizer uses strategy files (YAML or JSON) to define how to anonymize your database. The tool replaces personally identifiable information (PII) with realistic pseudorandom data using the [Faker library](https://faker.readthedocs.io/).

## Basic Strategy File Structure

```yaml
# Optional: Set locale for localized fake data
locale: en_US

# Optional: Custom faker providers
providers:
  - faker_airtravel.AirtravelProvider
  - my_custom_provider.MyProvider

# Define anonymization strategies for tables
tables:
  table_name:
    columns:
      column_name: anonymization_strategy

# Optional: SQL scripts to run before/after anonymization
scripts:
  before:
    - "DELETE FROM config WHERE name = 'secret'"
  after:
    - "SELECT COUNT(*) FROM users"
```

## Most Common Anonymization Patterns

| Data Type                | Anonymization Strategy | Example Output       |
| ------------------------ | ---------------------- | -------------------- |
| **Names**                |
| First Name               | `first_name`           | John                 |
| Last Name                | `last_name`            | Smith                |
| Full Name                | `name`                 | John Smith           |
| Username                 | `user_name`            | john.smith           |
| **Contact**              |
| Email                    | `email`                | john@example.com     |
| Unique Email             | `unique_email`         | john123@example.com  |
| Company Email            | `company_email`        | john@company.com     |
| Phone Number             | `phone_number`         | +1-555-123-4567      |
| **Addresses**            |
| Street Address           | `street_address`       | 123 Main St          |
| City                     | `city`                 | New York             |
| State                    | `state`                | California           |
| Postal Code              | `postcode`             | 12345                |
| Country                  | `country`              | United States        |
| **Business**             |
| Company                  | `company`              | Tech Corp Inc        |
| Job Title                | `job`                  | Software Engineer    |
| **Internet**             |
| Website URL              | `uri`                  | https://example.com  |
| IP Address               | `ipv4_public`          | 203.0.113.1          |
| User Agent               | `user_agent`           | Mozilla/5.0...       |
| **Content**              |
| Paragraph                | `paragraph`            | Lorem ipsum dolor... |
| Sentence                 | `sentence`             | This is a sentence.  |
| **Clear Sensitive Data** |
| Password                 | `( '' )`               | (empty string)       |
| Secret Token             | `( NULL )`             | NULL                 |
| SSN                      | `( '' )`               | (empty string)       |

## Table Strategies

### Truncate Table

Remove all data from the table using `TRUNCATE` (ignores foreign key constraints):

```yaml
tables:
  logs: truncate
  temporary_data: truncate
```

### Delete Table

Remove all data using `DELETE` (respects foreign key constraints):

```yaml
tables:
  audit_logs: delete
  session_data: delete
```

### Update Columns

Anonymize specific columns while keeping the rest of the data:

```yaml
tables:
  users:
    columns:
      email: email
      first_name: first_name
      last_name: last_name
```

## Column Anonymization Strategies

### 1. Unique Strategies

#### `unique_email`

Generates unique email addresses:

```yaml
columns:
  email: unique_email
  contact_email: unique_email
```

#### `unique_login`

Generates unique usernames:

```yaml
columns:
  username: unique_login
  login_id: unique_login
```

### 2. Literal Values

Replace with specific literal values:

```yaml
columns:
  # Simple literal (compact syntax)
  password: ( '' )
  secret_key: ( NULL )

  # With SQL functions
  created_at: ( NOW() )
  random_number: ( RAND() )

  # Verbose syntax
  api_key:
    type: literal
    value: CONCAT('key_', RAND())
```

### 3. Empty Values (Deprecated)

Replace with empty strings:

```yaml
columns:
  optional_field: empty
  notes: empty
```

### 4. Fake Data (Most Common)

Use Faker library generators:

```yaml
columns:
  # Compact syntax
  first_name: first_name
  email: email
  phone: phone_number

  # Verbose syntax with options
  bio:
    type: fake_update
    fake_type: paragraph
    fake_args:
      nb_sentences: 3
```

## Faker Data Types by Category

### Personal Information

#### Names

```yaml
first_name: first_name # John
last_name: last_name # Smith
name: name # John Smith
user_name: user_name # john.smith
prefix: prefix # Mr.
suffix: suffix # Jr.
```

#### Contact Information

```yaml
email: email # john@example.com
company_email: company_email # john@company.com
phone_number: phone_number # +1-555-123-4567
```

### Geographic Data

#### Addresses

```yaml
address: address # 123 Main St
street_address: street_address # 123 Main St
city: city # New York
state: state # California
country: country # United States
postcode: postcode # 12345
postal_code: postcode # 12345 (alias)
```

#### Location Details

```yaml
latitude: latitude # 40.7128
longitude: longitude # -74.0060
```

### Business Information

#### Company Data

```yaml
company: company # Tech Corp Inc
bs: bs # "innovate scalable solutions"
catch_phrase: catch_phrase # "Innovative solutions for tomorrow"
job: job # Software Engineer
```

### Internet & Technology

#### Web-related

```yaml
uri: uri # https://example.com/path
url: url # https://example.com
domain_name: domain_name # example.com
ipv4_private: ipv4_private # 192.168.1.1
ipv4_public: ipv4_public # 203.0.113.1
ipv6: ipv6 # 2001:db8::1
mac_address: mac_address # 00:1B:44:11:3A:B7
user_agent: user_agent # Mozilla/5.0...
```

#### File System

```yaml
file_name: file_name # document.pdf
file_path: file_path # /path/to/file.txt
file_extension: file_extension # .pdf
```

### Dates & Times

```yaml
date: date # 2023-05-15
date_of_birth: date_of_birth # 1985-03-22
past_date: past_date # 2020-01-15
future_date: future_date # 2025-12-31
past_datetime: past_datetime # 2020-01-15 14:30:00
future_datetime: future_datetime # 2025-12-31 09:15:00
```

### Numbers & Financial

#### Basic Numbers

```yaml
random_int: random_int # 42
pyint: pyint # 1337
pyfloat: pyfloat # 123.45
pydecimal: pydecimal # 999.99
```

#### Financial

```yaml
credit_card_number: credit_card_number # 4111-1111-1111-1111
currency_code: currency_code # USD
```

### Text Content

#### Lorem Ipsum & Text

```yaml
word: word # lorem
text: text # Long paragraph...
paragraph: paragraph # Medium length text
sentence: sentence # A complete sentence.
```

#### Identifiers

```yaml
uuid4: uuid4 # 550e8400-e29b-41d4-a716-446655440000
isbn13: isbn13 # 978-3-16-148410-0
```

### Custom Faker Arguments

Many faker types accept additional arguments:

```yaml
columns:
  # Generate paragraphs with specific sentence count
  description:
    type: fake_update
    fake_type: paragraph
    fake_args:
      nb_sentences: 5

  # Generate files with specific depth
  file_path:
    type: fake_update
    fake_type: file_path
    fake_args:
      depth: 3

  # Generate random integers in range
  score:
    type: fake_update
    fake_type: random_int
    fake_args:
      min: 1
      max: 100
```

## Common Anonymization Patterns

### User/Customer Table

```yaml
tables:
  users:
    columns:
      # Personal info
      first_name: first_name
      last_name: last_name
      email: unique_email
      phone: phone_number

      # Authentication (clear sensitive data)
      password: ( '' )
      password_hash: ( '' )
      api_token: ( NULL )

      # Address
      street_address: street_address
      city: city
      state: state
      postal_code: postcode
      country: country

      # Keep non-sensitive data as-is by not listing them
```

### E-commerce Order Table

```yaml
tables:
  orders:
    columns:
      # Customer info
      billing_email: email
      billing_name: name
      billing_phone: phone_number

      # Address
      billing_address: street_address
      billing_city: city
      billing_postcode: postcode

      shipping_address: street_address
      shipping_city: city
      shipping_postcode: postcode

      # Keep order amounts, dates, status (business data)
```

### Comments/Reviews

```yaml
tables:
  comments:
    columns:
      author_name: name
      author_email: email
      author_ip: ipv4_public
      content: paragraph
      user_agent: user_agent
```

### Employee Records

```yaml
tables:
  employees:
    columns:
      first_name: first_name
      last_name: last_name
      email: company_email
      phone: phone_number
      address: address
      emergency_contact: name
      emergency_phone: phone_number

      # Clear sensitive data
      ssn: ( '' )
      bank_account: ( '' )
      salary: ( 0 )
```

## Advanced Features

### Conditional Anonymization

Apply anonymization only to specific rows:

```yaml
tables:
  users:
    columns:
      email:
        type: fake_update
        fake_type: company_email
        where: "role != 'admin'"

      first_name:
        type: fake_update
        fake_type: first_name
        where: "active = 1"
```

### Multiple Strategies for Same Column

```yaml
tables:
  users:
    columns:
      - column_name: email
        type: literal
        value: "admin@company.com"
        where: "role = 'admin'"
      - column_name: email
        type: fake_update
        fake_type: email
        where: "role != 'admin'"
```

### Custom Data Types

Specify SQL data types for generated values:

```yaml
columns:
  large_text:
    type: fake_update
    fake_type: paragraph
    sql_type: TEXT

  precise_number:
    type: fake_update
    fake_type: pydecimal
    sql_type: DECIMAL(10,2)
```

### Localization

Generate locale-specific data:

```yaml
locale: fr_FR # French locale

tables:
  users:
    columns:
      first_name: first_name # Will generate French names
      address: address # Will generate French addresses
      phone: phone_number # Will generate French phone format
```

## Examples

### WordPress Database

```yaml
tables:
  wp_users:
    columns:
      user_login: user_name
      user_pass: ( '' )
      user_nicename: user_name
      user_email: email
      user_url: uri
      display_name: name
      user_activation_key: ( '' )

  wp_comments:
    columns:
      comment_author: name
      comment_author_email: email
      comment_author_IP: ipv4_public
      comment_agent: user_agent
```

### E-commerce (Sylius)

```yaml
tables:
  sylius_address:
    columns:
      first_name: first_name
      last_name: last_name
      street: street_address
      city: city
      postcode: postcode
      phone_number: phone_number
      company: company

  sylius_user:
    columns:
      username: email
      username_canonical: email
      email: email
      email_canonical: email
      salt: ( '' )
      first_name: first_name
      last_name: last_name
      confirmation_token: ( '' )

  # Remove payment-related tables entirely
  sylius_payment: truncate
  sylius_credit_card: truncate
```

### Complete CRM Example

```yaml
locale: en_US

tables:
  # Customer data
  customers:
    columns:
      first_name: first_name
      last_name: last_name
      email: unique_email
      phone: phone_number
      company: company
      title: job

      # Address
      street: street_address
      city: city
      state: state
      zip: postcode
      country: country

      # Clear sensitive fields
      ssn: ( '' )
      credit_score: ( NULL )

  # Communication logs
  communications:
    columns:
      subject: catch_phrase
      body: paragraph
      sender_email: email
      recipient_email: email
      sender_ip: ipv4_public

  # Remove sensitive tables
  payment_methods: truncate
  credit_reports: delete

scripts:
  before:
    - "DELETE FROM audit_log WHERE action = 'login'"
  after:
    - "SELECT COUNT(*) as anonymized_customers FROM customers"
```
