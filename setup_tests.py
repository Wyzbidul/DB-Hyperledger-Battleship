from __future__ import print_function

import os
import subprocess

from setuptools import setup, find_packages


data_files = []

if os.path.exists("tests"):
    data_files.append(('/data/tests/battleship', ['tests/test_tp_battleship.py']))
    data_files.append(('/data/tests/battleship', [
        '../../tests/sawtooth_integration/tests/test_battleship_smoke.py']))

try:
    os.environ["ST_VERSION"]
    print('Using ST_VERSION')
    VERSION = os.environ["ST_VERSION"]
except KeyError:
    print('ST_VERSION not set. Using get_version')
    VERSION = subprocess.check_output(
        ['../../bin/get_version']).decode('utf-8').strip()

setup(
    name='sawtooth-battleship-tests',
    version=VERSION,
    description='Sawtooth Battleship Python Test',
    author='Hyperledger Sawtooth',
    url='https://github.com/hyperledger/sawtooth-sdk-python',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'colorlog',
        'protobuf',
        'sawtooth-sdk',
        'PyYAML',
    ],
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'battleship = sawtooth_battleship.battleship_cli:main_wrapper',
            'battleship-tp-python = sawtooth_battleship.processor.main:main',
        ]
    })