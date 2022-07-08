# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

# pylint: disable=attribute-defined-outside-init

import unittest
import logging
import operator
import subprocess
import shlex
import urllib.request
import urllib.error
import json
from base64 import b64decode

import cbor

from sawtooth_intkey.intkey_message_factory import IntkeyMessageFactory
from sawtooth_integration.tests.integration_tools import wait_for_rest_apis


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


INTKEY_PREFIX = '1cf126'
BATTLESHIP_PREFIX = '5b7349'
WAIT = 300


class TestTwoFamilies(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        wait_for_rest_apis(['rest-api:8008'])

    def test_two_families(self):
        '''
        After starting a validator with both intkey and battleship
        transaction processors and initializing battleship, verify that
        state is empty. Next, send the following pairs of commands,
        verifying that the state is as it should be after each:

        1. Send a batch of intkey 'set' txns and create an battleship game.

        2. Send a batch of valid intkey 'inc'/'dec' txns and attack an battleship space.

        3. Send an invalid batch of intkey 'inc'/'dec' txns (invalid because
        they target names that haven't been set) and attack the same battleship space.

        4. Send more valid intkey txns and attack a new battleship space.

        5. Send the same intkey 'set' txns (which are now invalid) and
        create the same battleship game (which has already been created).

        6. Send more valid intkey txns and attack a new battleship space.

        Besides verifying that the battleship and intkey commands act as expected,
        verify that there is nothing in the state that isn't battleship or intkey.
        '''

        self.intkey_verifier = IntkeyTestVerifier()
        self.battleship_verifier = BattleshipTestVerifier()

        _send_battleship_cmd('sawtooth keygen')

        self.verify_empty_state()

        commands = zip(
            self.intkey_verifier.intkey_cmds,
            self.battleship_verifier.battleship_cmds)

        how_many_updates = 0

        for intkey_cmd, battleship_cmd in commands:
            _send_intkey_cmd(intkey_cmd)
            _send_battleship_cmd('{} --url {} --wait {}'.format(
                battleship_cmd,
                'http://rest-api:8008',
                WAIT))

            if intkey_cmd == self.intkey_verifier.valid_txns:
                how_many_updates += 1

            self.verify_state_after_n_updates(how_many_updates)

    def verify_empty_state(self):
        LOGGER.debug('Verifying empty state')

        self.assertEqual(
            [],
            _get_intkey_state(),
            'Expected intkey state to be empty')

        self.assertEqual(
            [],
            _get_battleship_state(),
            'Expected battleship state to be empty')

    def verify_state_after_n_updates(self, num):
        LOGGER.debug('Verifying state after %s updates', num)

        intkey_state = _get_intkey_data()
        LOGGER.info('Current intkey state: %s', intkey_state)
        battleship_data = _get_battleship_data()
        LOGGER.info('Current battleship state: %s', battleship_data)

        self.assertEqual(
            intkey_state,
            self.intkey_verifier.state_after_n_updates(num),
            'Wrong intkey state')

        self.assertEqual(
            battleship_data,
            self.battleship_verifier.state_after_n_updates(num),
            'Wrong battleship state')


# sending commands

def _send_battleship_cmd(cmd_str):
    LOGGER.info('Sending battleship cmd')
    subprocess.run(
        shlex.split(cmd_str),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True)


def _send_intkey_cmd(txns):
    batch = IntkeyMessageFactory().create_batch(txns)
    LOGGER.info('Sending intkey txns')
    _post_batch(batch)

# rest_api calls


def _post_batch(batch):
    headers = {'Content-Type': 'application/octet-stream'}
    response = _query_rest_api(
        '/batches', data=batch, headers=headers, expected_code=202)
    return _submit_request('{}&wait={}'.format(response['link'], WAIT))


def _get_intkey_data():
    state = _get_intkey_state()
    # state is a list of dictionaries: { data: ..., address: ... }
    dicts = [cbor.loads(b64decode(entry['data'])) for entry in state]
    LOGGER.debug(dicts)
    data = {k: v for d in dicts for k, v in d.items()}  # merge dicts
    return data


def _get_battleship_data():
    state = _get_battleship_state()
    data = b64decode(state[0]['data']).decode().split('|')[0].split(',')
    game_name, board, turn, _, _ = data
    return board, turn, game_name


def _get_intkey_state():
    state = _get_state_prefix(INTKEY_PREFIX)
    return state


def _get_battleship_state():
    state = _get_state_prefix(BATTLESHIP_PREFIX)
    return state


def _get_state_prefix(prefix):
    response = _query_rest_api('/state?address=' + prefix)
    return response['data']


def _query_rest_api(suffix='', data=None, headers=None, expected_code=200):
    if headers is None:
        headers = {}
    url = 'http://rest-api:8008' + suffix
    return _submit_request(
        urllib.request.Request(url, data, headers),
        expected_code=expected_code)


def _submit_request(request, expected_code=200):
    conn = urllib.request.urlopen(request)
    assert expected_code == conn.getcode()

    response = conn.read().decode('utf-8')
    return json.loads(response)

# verifiers

## MODIFY to fit battleship layout and test
class BattleshipTestVerifier:
    def __init__(self):
        self.battleship_cmds = (
            'battleship create game --wait {}'.format(WAIT),
            'battleship shoot game 5 --wait {}'.format(WAIT),
            'battleship shoot game 5 --wait {}'.format(WAIT),
            'battleship shoot game 9 --wait {}'.format(WAIT),
            'battleship create game --wait {}'.format(WAIT),
            'battleship shoot game 4 --wait {}'.format(WAIT),
        )

    def state_after_n_updates(self, num):
        state = {
            0: ('---------', 'P1-NEXT', 'game'),
            1: ('----X----', 'P2-NEXT', 'game'),
            2: ('----X---O', 'P1-NEXT', 'game'),
            3: ('---XX---O', 'P2-NEXT', 'game')
        }

        try:
            return state[num]
        except KeyError:
            return ()


class IntkeyTestVerifier:
    def __init__(self):
        self.valid = 'ragdoll', 'sphynx', 'van'
        self.invalid = 'manx', 'persian', 'siamese'
        self.verbs = 'inc', 'dec', 'inc'
        self.sets = 'set', 'set', 'set'
        self.incdec = 11, 13, 10
        self.initial = 110, 143, 130

        self.populate = tuple(zip(self.sets, self.valid, self.initial))
        self.valid_txns = tuple(zip(self.verbs, self.valid, self.incdec))
        self.invalid_txns = tuple(zip(self.verbs, self.invalid, self.incdec))

        self.intkey_cmds = (
            self.populate,
            self.valid_txns,
            self.invalid_txns,
            self.valid_txns,
            self.populate,
            self.valid_txns,
        )

    def state_after_n_updates(self, num):
        ops = {
            'inc': operator.add,
            'dec': operator.sub
        }

        expected_values = [
            ops[verb](init, (val * num))
            for verb, init, val
            in zip(self.verbs, self.initial, self.incdec)
        ]

        return dict(zip(self.valid, expected_values))
