# Use the python:3.12-slim-bookworm base image
FROM python:3.12-slim-bookworm

# Install prerequisites for SQL Server tools
RUN apt-get update && \
    apt-get install -y gnupg2 curl lsb-release && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    curl https://packages.microsoft.com/config/debian/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update

RUN ACCEPT_EULA=Y apt-get install -y mssql-tools18 msodbcsql18
ENV PATH="${PATH}:/opt/mssql-tools18/bin"

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install . .[mssql]

ENTRYPOINT [ "pynonymizer" ]