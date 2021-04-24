import os
import re

def test_module_version_changelog_parity():
  ## [1.19.0] 2021-04-24
  import pynonymizer
  with open("./CHANGELOG.md") as changelogfile:
    changelog = changelogfile.read()
  
  versions = re.findall(r"##\s+\[(.+)\]\s+\d\d\d\d-\d\d-\d\d", changelog)

  assert versions[0] == pynonymizer.__version__
