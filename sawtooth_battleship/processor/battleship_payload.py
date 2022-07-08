from sawtooth_sdk.processor.exceptions import InvalidTransaction


class BattleshipPayload:

    def __init__(self, payload):
        try:
            # The payload is csv utf-8 encoded string
            name, action, space = payload.decode().split(",")
        except ValueError as e:
            raise InvalidTransaction("Invalid payload serialization") from e

        if not name:
            raise InvalidTransaction('Name is required')

        if '|' in name:
            raise InvalidTransaction('Name cannot contain "|"')

        if not action:
            raise InvalidTransaction('Action is required')

        if action not in ('create', 'shoot', 'delete'):
            raise InvalidTransaction('Invalid action: {}'.format(action))

        if action == 'shoot':
            try:
                ## MODIFY: case name for position as an index 
                if int(space) not in range(1, 10):
                    raise InvalidTransaction(
                        "Space must be an integer from 0 to 99")
            except ValueError:
                raise InvalidTransaction(
                    'Space must be an integer from 0 to 99') from ValueError

        if action == 'shoot':
            space = int(space)

        self._name = name
        self._action = action
        self._space = space

    @staticmethod
    def from_bytes(payload):
        return BattleshipPayload(payload=payload)

    @property
    def name(self):
        return self._name

    @property
    def action(self):
        return self._action

    @property
    def space(self):
        return self._space