import logging
import shutil
import shlex
import subprocess
from pynonymizer.database.exceptions import DependencyError

logger = logging.getLogger(__name__)

RESTORE_CMD = "mysql"
DUMP_CMD = "mysqldump"


def _optional_arg(condition, value):
    if condition:
        return value
    else:
        return []


def _optional_arg_pair(arg_value_pair):
    return _optional_arg(arg_value_pair[1], arg_value_pair)


class MySqlDumpRunner:
    def __init__(
        self,
        db_host,
        db_user,
        db_pass,
        db_name,
        db_port,
        additional_opts="",
    ):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_port = db_port
        self.additional_opts = shlex.split(additional_opts)
        self.process = None

        if db_name is None:
            raise ValueError("db_name cannot be null")

        if not (shutil.which(DUMP_CMD)):
            raise DependencyError(
                DUMP_CMD, f"The '{DUMP_CMD}' client must be present in the $PATH"
            )

    def __get_base_params(self):
        return [
            *_optional_arg_pair(["--host", self.db_host]),
            *_optional_arg_pair(["--port", self.db_port]),
            *_optional_arg_pair(["--user", self.db_user]),
            *_optional_arg(self.db_pass, [f"-p{self.db_pass}"]),
        ]

    def open(self):
        self.close()

        self.process = subprocess.Popen(
            [DUMP_CMD]
            + self.__get_base_params()
            + self.additional_opts
            + [self.db_name],
            stdout=subprocess.PIPE,
        )
        return self.process.stdout

    def close(self):
        if self.process is not None:
            self.process.stdout.close()
            return_code = self.process.wait()
            if return_code > 0:
                raise DependencyError(DUMP_CMD, "returned error during run")
            self.process = None


class MySqlCmdRunner:
    def __init__(
        self,
        db_host,
        db_user,
        db_pass,
        db_name,
        db_port,
        additional_opts="",
    ):
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.db_port = db_port
        self.additional_opts = shlex.split(additional_opts)
        self.process = None

        if db_name is None:
            raise ValueError("db_name cannot be null")

        if not (shutil.which(RESTORE_CMD)):
            raise DependencyError(
                RESTORE_CMD, f"The '{RESTORE_CMD}' client must be present in the $PATH"
            )

    def __mask_subprocess_error(self, error):
        """
        messes with the internals of a CalledProcessError to hide the fact that there's a password in there,
        in case it bubbles out in a traceback.

        This might be better as a wrapping exception, rather than messing around inside other people's classes.
        """
        error.cmd = [
            RESTORE_CMD,
            "-h",
            self.db_host,
            "-P",
            self.db_port,
            "-u",
            self.db_user,
            "-p******",
        ]
        raise error from None

    def __get_base_params(self):
        return [
            RESTORE_CMD,
            *_optional_arg_pair(["-h", self.db_host]),
            *_optional_arg_pair(["-P", self.db_port]),
            *_optional_arg_pair(["-u", self.db_user]),
            *_optional_arg(self.db_pass, [f"-p{self.db_pass}"]),
        ]

    def execute(self, statements):
        if not isinstance(statements, list):
            statements = [statements]

        outputs = []

        for statement in statements:
            logger.debug(statement)
            try:
                outputs.append(
                    subprocess.check_output(
                        self.__get_base_params()
                        + self.additional_opts
                        + ["--execute", statement]
                    )
                )
            except subprocess.CalledProcessError as error:
                self.__mask_subprocess_error(error)

        return outputs

    def db_execute(self, statements):
        if not isinstance(statements, list):
            statements = [statements]

        outputs = []

        for statement in statements:
            logger.debug(statement)
            try:
                outputs.append(
                    subprocess.check_output(
                        self.__get_base_params()
                        + self.additional_opts
                        + [self.db_name, "--execute", statement]
                    )
                )
            except subprocess.CalledProcessError as error:
                self.__mask_subprocess_error(error)

        return outputs

    def get_single_result(self, statement):
        logger.debug(statement)
        try:
            return subprocess.check_output(
                self.__get_base_params()
                + ["-sN", *self.additional_opts, self.db_name, "--execute", statement]
            ).decode()
        except subprocess.CalledProcessError as error:
            self.__mask_subprocess_error(error)

    def open(self):
        self.close()
        self.process = subprocess.Popen(
            self.__get_base_params() + self.additional_opts + [self.db_name],
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
