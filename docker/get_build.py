#!/usr/bin/env python3
import pynonymizer
from packaging.version import Version

version = Version(pynonymizer.__version__)
tags = []

if not (version.is_prerelease or version.is_devrelease or version.is_postrelease):
    tags.append("latest")
    tags.append(f"{version.major}")
    tags.append(f"{version.major}.{version.minor}")
    tags.append(f"{version.major}.{version.minor}.{version.micro}")
else:
    tags.append(pynonymizer.__version__)

buildstr = " ".join(
    [
        "docker build .",
        *[f"-t rwnxt/pynonymizer:{tag}" for tag in tags],
    ]
)

pushstr = "\n".join([*[f"docker push rwnxt/pynonymizer:{tag}" for tag in tags]])

print(buildstr)
print(pushstr)
