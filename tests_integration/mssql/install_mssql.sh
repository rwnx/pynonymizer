#!/bin/bash -e

MSSQL_PID='developer'

echo Adding Microsoft repositories...
sudo curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
repoargs="$(curl https://packages.microsoft.com/config/ubuntu/18.04/mssql-server-2019.list)"
sudo add-apt-repository "${repoargs}"
repoargs="$(curl https://packages.microsoft.com/config/ubuntu/18.04/prod.list)"
sudo add-apt-repository "${repoargs}"

echo Running apt-get update -y...
sudo apt-get update -y

echo Installing SQL Server...
sudo apt-get install -y mssql-server

echo Running mssql-conf setup...
sudo MSSQL_SA_PASSWORD=$MSSQL_SA_PASSWORD \
     MSSQL_PID=$MSSQL_PID \
     /opt/mssql/bin/mssql-conf -n setup accept-eula

echo Installing mssql-tools and unixODBC developer...
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools unixodbc-dev

# Add SQL Server tools to the path by default:
echo Adding SQL Server tools to your path...
echo PATH="$PATH:/opt/mssql-tools/bin" >> ~/.bash_profile
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
source ~/.bashrc

echo manual starting SQL Server...
sudo service mssql-server start 

# Connect to server and get the version:
counter=1
errstatus=1
while [ $counter -le 20 ] && [ $errstatus = 1 ]
do
  echo Waiting for SQL Server to start...
  sleep 3s
  /opt/mssql-tools/bin/sqlcmd \
    -S localhost \
    -U SA \
    -P $MSSQL_SA_PASSWORD \
    -Q "SELECT @@VERSION" 2>/dev/null
  errstatus=$?
  ((counter++))
done

if [ $errstatus = 1 ]
then
  echo trying to start mssql again...
  sudo service mssql-server start 

  # Connect to server and get the version:
  counter=1
  errstatus=1
  while [ $counter -le 20 ] && [ $errstatus = 1 ]
  do
    echo Waiting for SQL Server to start...
    sleep 3s
    /opt/mssql-tools/bin/sqlcmd \
      -S localhost \
      -U SA \
      -P $MSSQL_SA_PASSWORD \
      -Q "SELECT @@VERSION" 2>/dev/null
    errstatus=$?
    ((counter++))
  done

  if [ $errstatus = 1 ]
  then
    echo Cannot connect to SQL Server, installation aborted
    exit $errstatus
  fi
fi

echo Done!