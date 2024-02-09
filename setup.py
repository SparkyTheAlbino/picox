from setuptools import setup, find_packages

setup(
    name='piconnect',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pyserial'
    ],
    entry_points={
        'console_scripts': [
            'piconnect = piconnect.cli:main',
        ],
    },
)
