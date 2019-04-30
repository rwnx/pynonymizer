import setuptools
import sys


if sys.version_info < (3, 6):
    sys.exit('pypinfo requires Python 3.6+')

setuptools.setup(
    name='pynonymizer',
    version='0.1.0',
    packages=setuptools.find_packages(),
    install_requires=[
        "pyyaml>=5",
        "tqdm>=4",
        "faker>=1"
    ],
    entry_points={
        'console_scripts': [
            'pynonymizer = pynonymizer.__main__:main'
        ]
    },
 )