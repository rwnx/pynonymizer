import shutil
import subprocess
from pynonymizer.database.exceptions import DependencyError
import os
"""
Seperate everything that touches actual query exec into its own module
"""

class PSqlDumpRunner:
    def __init__(self, db_host, db_user, db_pass, db_name, db_port="5432"):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_port = db_port

        if not (shutil.which("pg_dump")):
            raise DependencyError( "pg_dump", "The 'pg_dump' client must be present in the $PATH")

    def __get_base_params(self):
        return ["pg_dump", "--host", self.db_host, "--port", self.db_port, "--username", self.db_user]

    def __get_env(self):
        new_env = os.environ.copy()
        new_env.update({"PGPASSWORD": self.db_pass})

        return new_env

    def open_dumper(self):
        return subprocess.Popen(self.__get_base_params() + [self.db_name],
                                stdout=subprocess.PIPE,
                                env=self.__get_env()
                                ).stdout


class PSqlCmdRunner:
    def __init__(self, db_host, db_user, db_pass, db_name, db_port="5432"):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_port = db_port

        if not (shutil.which("psql")):
            raise DependencyError("psql", "The 'psql' client must be present in the $PATH")

    def __get_base_params(self):
        return ["psql", "--host", self.db_host, "--port", self.db_port, "--username", self.db_user]

    def __get_env(self):
        new_env = os.environ.copy()
        new_env.update({"PGPASSWORD": self.db_pass})

        return new_env

    def execute(self, statements):
        if not isinstance(statements, list):
            statements = [statements]

        outputs = []

        for statement in statements:
            outputs.append( subprocess.check_output(self.__get_base_params() + ["--command", statement], env=self.__get_env()) )

        return outputs

    def db_execute(self, statements):
        if not isinstance(statements, list):
            statements = [statements]

        outputs = []
        
        for statement in statements:
            outputs.append(subprocess.check_output(
                self.__get_base_params() + ["--dbname", self.db_name,  "--command", statement],
                env=self.__get_env()
            ))

        return outputs

    def get_single_result(self, statement):
        return subprocess.check_output(
            self.__get_base_params() + ["--dbname", self.db_name, "-tA", "--command", statement],
            env=self.__get_env()
        ).decode()


    def open_batch_processor(self):
        return subprocess.Popen(
            self.__get_base_params() + ["--dbname", self.db_name, "--quiet"],
            env=self.__get_env(),
            stdin=subprocess.PIPE
        ).stdin
