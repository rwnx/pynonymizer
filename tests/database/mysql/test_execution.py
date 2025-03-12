import os
from pathlib import Path

import pytest
from unittest import mock
from pynonymizer.database.mysql import execution


@pytest.mark.parametrize(
    argnames=("mocked_command", "expected_restore_cmd", "expected_dump_cmd"),
    argvalues=[("mysql", "mysql", "mysqldump"), ("mariadb", "mariadb", "mariadb-dump")],
    ids=["mysql", "mariadb"],
)
def test_set_mysql_cmd(
    mocked_command: str, expected_restore_cmd: str, expected_dump_cmd: str, tmpdir
) -> None:
    # create a fake binary for shutil to find
    fake_binary_path: Path = tmpdir / mocked_command
    fake_binary_path.write_text("#!/bin/bash\nexit 0", encoding="utf-8")
    fake_binary_path.chmod(0o755)

    with mock.patch.dict(os.environ, {"PATH": str(tmpdir)}):
        # Make sure the global variables are set to the default values
        assert execution.RESTORE_CMD == "mysql"
        assert execution.DUMP_CMD == "mysqldump"
        execution._set_mysql_cmd()
        # Check if the global variables are set to the expected values
        assert execution.RESTORE_CMD == expected_restore_cmd
        assert execution.DUMP_CMD == expected_dump_cmd
