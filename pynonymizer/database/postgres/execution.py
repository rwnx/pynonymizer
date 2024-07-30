import logging
import shutil
import shlex
import subprocess
from pynonymizer.database.exceptions import DependencyError
import os

"""
Seperate everything that touches actual query exec into its own module
"""

RESTORE_CMD = "psql"
DUMP_CMD = "pg_dump"

logger = logging.getLogger(__name__)


class PSqlDumpRunner:
    def __init__(
        self, db_host, db_user, db_pass, db_name, db_port="5432", additional_opts=""
    ):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_port = db_port
        self.additional_opts = shlex.split(additional_opts)
        self.process = None

        if not (shutil.which(DUMP_CMD)):
            raise DependencyError(
                DUMP_CMD, f"The '{DUMP_CMD}' client must be present in the $PATH"
            )

    def __get_base_params(self):
        return [
            DUMP_CMD,
            "--host",
            self.db_host,
            "--port",
            self.db_port,
            "--username",
            self.db_user,
        ]

    def __get_env(self):
        new_env = os.environ.copy()
        if self.db_pass:
            new_env.update({"PGPASSWORD": self.db_pass})

        return new_env

    def open(self):
        self.close()
        self.process = subprocess.Popen(
            self.__get_base_params() + self.additional_opts + [self.db_name],
            stdout=subprocess.PIPE,
            env=self.__get_env(),
        )
        return self.process.stdout

    def close(self):
        if self.process is not None:
            self.process.stdout.close()
            return_code = self.process.wait()
            if return_code > 0:
                raise DependencyError(DUMP_CMD, "returned error during run")
            self.process = None


class PSqlCmdRunner:
    def __init__(
        self, db_host, db_user, db_pass, db_name, db_port="5432", additional_opts=""
    ):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_port = db_port
        self.additional_opts = shlex.split(additional_opts)
        self.process = None

        if not (shutil.which(RESTORE_CMD)):
            raise DependencyError(
                RESTORE_CMD, "The f'{RESTORE_CMD}' client must be present in the $PATH"
            )

    def __get_base_params(self):
        return [
            RESTORE_CMD,
            "--host",
            self.db_host,
            "--port",
            self.db_port,
            "--username",
            self.db_user,
        ]

    def __get_env(self):
        new_env = os.environ.copy()
        if self.db_pass:
            new_env.update({"PGPASSWORD": self.db_pass})

        return new_env

    def execute(self, statements):
        if not isinstance(statements, list):
            statements = [statements]

        outputs = []

        for statement in statements:
            logger.debug(statement)
            outputs.append(
                subprocess.check_output(
                    self.__get_base_params()
                    + self.additional_opts
                    + ["--command", statement],
                    env=self.__get_env(),
                )
            )

        return outputs

    def db_execute(self, statements):
        if not isinstance(statements, list):
            statements = [statements]

        outputs = []

        for statement in statements:
            logger.debug(statement)
            outputs.append(
                subprocess.check_output(
                    self.__get_base_params()
                    + [
                        "--dbname",
                        self.db_name,
                        *self.additional_opts,
                        "--command",
                        statement,
                    ],
                    env=self.__get_env(),
                )
            )

        return outputs

    def get_single_result(self, statement):
        logger.debug(statement)
        return subprocess.check_output(
            self.__get_base_params()
            + [
                "--dbname",
                self.db_name,
                "-tA",
                *self.additional_opts,
                "--command",
                statement,
            ],
            env=self.__get_env(),
        ).decode()

    def open(self):
        self.close()
        self.process = subprocess.Popen(
            self.__get_base_params()
            + ["--dbname", self.db_name, "--quiet"]
            + self.additional_opts,
            env=self.__get_env(),
            stdin=subprocess.PIPE,
        )
        return self.process.stdin

    def close(self):
        if self.process is not None:
            self.process.stdin.close()
            return_code = self.process.wait()
            if return_code > 0:
                raise DependencyError(RESTORE_CMD, "returned error during run")
            self.process = None
