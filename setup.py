import setuptools

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