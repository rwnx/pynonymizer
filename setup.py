import setuptools
import sys

if sys.version_info < (3, 6):
    sys.exit('pynonymizer requires Python 3.6+ to run')

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='pynonymizer',
    description='An anonymization tool for production databases',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Topic :: Database',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    author='Jerome Twell',
    author_email='jtwell1@gmail.com',
    url="https://github.com/jerometwell/pynonymizer",
    keywords="anonymization gdpr database mysql",
    license="MIT",
    packages=setuptools.find_packages(exclude=("tests", "tests.*")),
    install_requires=[
        "pyyaml>=5",
        "tqdm>=4",
        "faker>=1",
        "python-dotenv>=0.10",
    ],
    entry_points={
        'console_scripts': [
            'pynonymizer = pynonymizer.cli:cli'
        ]
    },
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    extras_require={
        'mssql': ["pyodbc>=4.0.26"]
    }
 )
