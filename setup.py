import setuptools
import sys


if sys.version_info < (3, 6):
    sys.exit('pynonymizer requires Python 3.6+ to run')

setuptools.setup(
    name='pynonymizer',
    version='1.0.0',
    description='An anonymization tool for production databases',
    author='Jerome Twell',
    author_email='jerome@examtrack.co.uk',
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
    setup_requires=["pytest-runner"],
    tests_require=["pytest"]
 )
