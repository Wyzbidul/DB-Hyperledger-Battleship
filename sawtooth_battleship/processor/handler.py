import logging

from sawtooth_battleship.processor.battleship_payload import BattleshipPayload
from sawtooth_battleship.processor.battleship_state import Game
from sawtooth_battleship.processor.battleship_state import BattleshipState
from sawtooth_battleship.processor.battleship_state import BATTLESHIP_NAMESPACE

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError


LOGGER = logging.getLogger(__name__)


class BattleshipTransactionHandler(TransactionHandler):
    # Disable invalid-overridden-method. The sawtooth-sdk expects these to be
    # properties.
    # pylint: disable=invalid-overridden-method
    @property
    def family_name(self):
        return 'battleship'

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [BATTLESHIP_NAMESPACE]

    def apply(self, transaction, context):

        header = transaction.header
        signer = header.signer_public_key

        battleship_payload = BattleshipPayload.from_bytes(transaction.payload)

        battleship_state = BattleshipState(context)

        if battleship_payload.action == 'delete':
            game = battleship_state.get_game(battleship_payload.name)

            if game is None:
                raise InvalidTransaction(
                    'Invalid action: game does not exist')

            battleship_state.delete_game(battleship_payload.name)

        elif battleship_payload.action == 'create':

            if battleship_state.get_game(battleship_payload.name) is not None:
                raise InvalidTransaction(
                    'Invalid action: Game already exists: {}'.format(
                        battleship_payload.name))

            ## ADAPT board shape //!\\
            game = Game(name=battleship_payload.name,
                        board="-" * 9,
                        state="P1-NEXT",
                        player1="",
                        player2="")

            battleship_state.set_game(battleship_payload.name, game)
            _display("Player {} created a game.".format(signer[:6]))

        elif battleship_payload.action == 'take':
            game = battleship_state.get_game(battleship_payload.name)

            if game is None:
                raise InvalidTransaction(
                    'Invalid action: Take requires an existing game')

            ## ADAPT to battleship game state
            if game.state in ('P1-WIN', 'P2-WIN', 'TIE'):
                raise InvalidTransaction('Invalid Action: Game has ended')

            if (game.player1 and game.state == 'P1-NEXT'
                and game.player1 != signer) or \
                    (game.player2 and game.state == 'P2-NEXT'
                     and game.player2 != signer):
                raise InvalidTransaction(
                    "Not this player's turn: {}".format(signer[:6]))

            if game.board[battleship_payload.space - 1] != '-':
                raise InvalidTransaction(
                    'Invalid Action: space {} already taken'.format(
                        battleship_payload))

            if game.player1 == '':
                game.player1 = signer

            elif game.player2 == '':
                game.player2 = signer

            upd_board = _update_board(game.board,
                                      battleship_payload.space,
                                      game.state)

            upd_game_state = _update_game_state(game.state, upd_board)

            game.board = upd_board
            game.state = upd_game_state

            ## ADAPT /!\
            battleship_state.set_game(battleship_payload.name, game)
            _display(
                "Player {} attacks space: {}\n\n".format(
                    signer[:6],
                    battleship_payload.space)
                + _game_data_to_str(
                    game.board,
                    game.state,
                    game.player1,
                    game.player2,
                    battleship_payload.name))

        else:
            raise InvalidTransaction('Unhandled action: {}'.format(
                battleship_payload.action))

## MODIFY ACTIONS /!\
def _update_board(board, space, state):
    if state == 'P1-NEXT':
        mark = 'X'
    elif state == 'P2-NEXT':
        mark = 'O'

    index = space - 1

    # replace the index-th space with mark, leave everything else the same
    return ''.join([
        current if square != index else mark
        for square, current in enumerate(board)
    ])

## MODIFY win_state & _is_win /!\
def _update_game_state(game_state, board):
    P1_wins = _is_win(board, 'X')
    P2_wins = _is_win(board, 'O')

    if P1_wins and P2_wins:
        raise InternalError('Two winners (there can be only one)')

    if P1_wins:
        return 'P1-WIN'

    if P2_wins:
        return 'P2-WIN'

    if '-' not in board:
        return 'TIE'

    if game_state == 'P1-NEXT':
        return 'P2-NEXT'

    if game_state == 'P2-NEXT':
        return 'P1-NEXT'

    if game_state in ('P1-WINS', 'P2-WINS', 'TIE'):
        return game_state

    raise InternalError('Unhandled state: {}'.format(game_state))

## MODIFY /!\ Check le nb de bateau restant
def _is_win(board, letter):
    wins = ((1, 2, 3), (4, 5, 6), (7, 8, 9),
            (1, 4, 7), (2, 5, 8), (3, 6, 9),
            (1, 5, 9), (3, 5, 7))

    for win in wins:
        if (board[win[0] - 1] == letter
                and board[win[1] - 1] == letter
                and board[win[2] - 1] == letter):
            return True
    return False

## MODIFY BOARD LAYOUT /!\
def _game_data_to_str(board, game_state, player1, player2, name):
    board = list(board.replace("-", " "))
    out = ""
    out += "GAME: {}\n".format(name)
    out += "PLAYER 1: {}\n".format(player1[:6])
    out += "PLAYER 2: {}\n".format(player2[:6])
    out += "STATE: {}\n".format(game_state)
    out += "\n"
    out += "{} | {} | {}\n".format(board[0], board[1], board[2])
    out += "---|---|---\n"
    out += "{} | {} | {}\n".format(board[3], board[4], board[5])
    out += "---|---|---\n"
    out += "{} | {} | {}".format(board[6], board[7], board[8])
    return out


def _display(msg):
    n = msg.count("\n")

    if n > 0:
        msg = msg.split("\n")
        length = max(len(line) for line in msg)
    else:
        length = len(msg)
        msg = [msg]

    # pylint: disable=logging-not-lazy
    LOGGER.debug("+" + (length + 2) * "-" + "+")
    for line in msg:
        LOGGER.debug("+ " + line.center(length) + " +")
    LOGGER.debug("+" + (length + 2) * "-" + "+")