These files can build pynonymizer + client image for each database type. 

run this script from the root of the repo:

```sh
docker build -f docker/pynonymizer-mssql.Dockerfile . -t rwnxt/pynonymizer:mssql
docker push rwnxt/pynonymizer:mssql

docker build -f docker/pynonymizer-mysql.Dockerfile . -t rwnxt/pynonymizer:mysql
docker push rwnxt/pynonymizer:mysql

docker build -f docker/pynonymizer-postgres.Dockerfile . -t rwnxt/pynonymizer:postgres
docker push rwnxt/pynonymizer:postgres
```