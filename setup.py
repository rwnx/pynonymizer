import setuptools
import sys
from pynonymizer.version import __version__


if sys.version_info < (3, 6):
    sys.exit('pynonymizer requires Python 3.6+ to run')

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='pynonymizer',
    version=__version__,
    description='An anonymization tool for production databases',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Topic :: Database',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6'
    ],
    author='Jerome Twell',
    author_email='jtwell1@gmail.com',
    url="https://gitlab.com/jerometwell/pynonymizer",
    keywords="anonymization gdpr database mysql",
    license="MIT",
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
