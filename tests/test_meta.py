import os
import re

"""
This tests things about the package, e.g. the changelog format,
so we dont ship something that is in a corrupt state
"""


def test_module_version_changelog_parity():
    ## [1.19.0] 2021-04-24
    import pynonymizer

    with open("./CHANGELOG.md") as changelogfile:
        changelog = changelogfile.read()

    versions = re.findall(r"##\s+\[(.+)\]\s+\d\d\d\d-\d\d-\d\d", changelog)

    assert versions[0] == pynonymizer.__version__
