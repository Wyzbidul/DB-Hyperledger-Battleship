import logging

from sawtooth_battleship.processor.battleship_payload import BattleshipPayload
from sawtooth_battleship.processor.battleship_state import Game
from sawtooth_battleship.processor.battleship_state import BattleshipState
from sawtooth_battleship.processor.battleship_state import BATTLESHIP_NAMESPACE

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError


LOGGER = logging.getLogger(__name__)
ID_BOAT = ['A', 'B', 'C', 'D', 'E']
BOAT_CASES = [[5, 4, 3, 3, 2],[5, 4, 3, 3, 2]]

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
                        board_P1="-" * 100,
                        board_P2="-" * 100,
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
            
            if game.state == "P1-NEXT":

                if game.board_P2[battleship_payload.space - 1] == 'X' or game.board_P2[battleship_payload.space - 1] == 'O':
                    raise InvalidTransaction(
                        'Invalid Action: space {} already attacked'.format(
                            battleship_payload))
                else :
                    print("HIT/SUNK/MISS")   #TBD add X to the board

                if game.player1 == '':
                    game.player1 = signer

                elif game.player2 == '':
                    game.player2 = signer

                upd_board = _update_board(game.board_P2,
                                        battleship_payload.space,
                                        game.state)

                upd_game_state = _update_game_state(game.state)

                game.board_P2 = upd_board
                game.state = upd_game_state

            if game.state == "P2-NEXT":

                if game.board_P1[battleship_payload.space - 1] == 'X' or game.board_P1[battleship_payload.space - 1] == 'O':
                    raise InvalidTransaction(
                        'Invalid Action: space {} already attacked'.format(
                            battleship_payload))
                else :
                    print("HIT/SUNK/MISS")   #TBD add X to the board

                if game.player1 == '':
                    game.player1 = signer

                elif game.player2 == '':
                    game.player2 = signer

                upd_board = _update_board(game.board_P1,
                                        battleship_payload.space,
                                        game.state)

                upd_game_state = _update_game_state(game.state)

                game.board_P1 = upd_board
                game.state = upd_game_state


            battleship_state.set_game(battleship_payload.name, game)
            _display(
                "Player {} attacks space: {}\n\n".format(
                    signer[:6],
                    battleship_payload.space)
                + _game_data_to_str(
                    game.board_P1,
                    game.board_P2,
                    game.state,
                    game.player1,
                    game.player2,
                    battleship_payload.name))

        else:
            raise InvalidTransaction('Unhandled action: {}'.format(
                battleship_payload.action))

def _update_board(board, space, state):
    index = space - 1
    if board[index] == '-':
        print('MISS')
        mark = 'X'
    elif board[index] in ID_BOAT:
        mark = 'O'
        if state == 'P1-NEXT' :
            id = 1
        else :
            id = 0
        if BOAT_CASES[id][ID_BOAT.index(board[index])] == 0:
            print('SUNK')
        else :
            print('HIT')

    # replace the index-th space with mark, leave everything else the same
    return ''.join([
        current if square != index else mark
        for square, current in enumerate(board)
    ])

def _update_game_state(game_state):
    P1_wins = _is_win(0)
    P2_wins = _is_win(1)

    if P1_wins and P2_wins:
        raise InternalError('Two winners (there can be only one)')

    if P1_wins:
        return 'P1-WIN'

    if P2_wins:
        return 'P2-WIN'

    if game_state == 'P1-NEXT':
        return 'P2-NEXT'

    if game_state == 'P2-NEXT':
        return 'P1-NEXT'

    if game_state in ('P1-WINS', 'P2-WINS'):
        return game_state

    raise InternalError('Unhandled state: {}'.format(game_state))

def _is_win(id):
    for k in BOAT_CASES[id]:
        if k != 0:
            return False
    return True

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