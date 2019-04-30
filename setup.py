import setuptools
import sys


if sys.version_info < (3, 6):
    sys.exit('pynonymizer requires Python 3.6+ to run')

setuptools.setup(
    name='pynonymizer',
    version='0.1.0',
    packages=setuptools.find_packages(),
    install_requires=[
        "pyyaml>=5",
        "tqdm>=4",
        "faker>=1",
        "python-dotenv>=0.10"
    ],
    entry_points={
        'console_scripts': [
            'pynonymizer = pynonymizer.__main__:main'
        ]
    },
 )