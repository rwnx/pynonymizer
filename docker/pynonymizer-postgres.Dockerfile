# Use the python:3.12-slim-bookworm base image
FROM python:3.12-slim-bookworm

# Install PostgreSQL client
RUN apt-get update && apt-get install -y \
    postgresql-client

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install .

ENTRYPOINT [ "pynonymizer" ]

