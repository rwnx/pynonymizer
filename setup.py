import setuptools

setuptools.setup(
    name='pynonymizer',
    version='0.1.0',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'pynonymizer = pynonymizer.__main__:main'
        ]
    },
 )