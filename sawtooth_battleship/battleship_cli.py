from __future__ import print_function

import argparse
import getpass
import logging
import os
import traceback
import sys
import pkg_resources

from colorlog import ColoredFormatter

from sawtooth_battleship.battleship_client import BattleshipClient
from sawtooth_battleship.battleship_exceptions import BattleshipException
from sawtooth_battleship.processor.handler import ID_BOAT


DISTRIBUTION_NAME = 'sawtooth-battleship'


DEFAULT_URL = 'http://127.0.0.1:8008'


def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)

    if verbose_level == 0:
        clog.setLevel(logging.WARN)
    elif verbose_level == 1:
        clog.setLevel(logging.INFO)
    else:
        clog.setLevel(logging.DEBUG)

    return clog


def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))


def add_create_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'create',
        help='Creates a new battleship game',
        description='Sends a transaction to start an battleship game with the '
        'identifier <name>. This transaction will fail if the specified '
        'game already exists.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='unique identifier for the new game')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--disable-client-validation',
        action='store_true',
        default=False,
        help='disable client validation')

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for game to commit')


def add_list_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'list',
        help='Displays information for all battleship games',
        description='Displays information for all battleship games in state, showing '
        'the players, the game state, and the board for each game.',
        parents=[parent_parser])

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')


def add_show_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'show',
        help='Displays information about an battleship game',
        description='Displays the battleship game <name>, showing the players, '
        'the game state, and the board',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='identifier for the game')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

def correct_space_row (string): 
    row = string 
    rowlist = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    if row not in rowlist: 
        raise argparse.ArgumentTypeError('Row has to be between A and J')
    return row 
    
def correct_space_col (int): 
    col = int 
    if col < 0 or col > 10: 
        raise argparse.ArgumentTypeError('Column has to be between 1 and 10')
    return col 

def add_shoot_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'shoot',
        help='Shoots a space in an battleship game',
        description='Sends a transaction to shoot an enemy square in the '
        'battleship game with the identifier <name>. This transaction will fail if the '
        'specified game does not exist.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='identifier for the game')

    parser.add_argument(
        'row', 
        type=correct_space_row, 
        help='row of the square to shoot (A-J)'
    )

    parser.add_argument(
        'col', 
        type=correct_space_col, 
        help='column of the square to shoot (1-10)'
    )

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for shoot transaction '
        'to commit')


def add_delete_parser(subparsers, parent_parser):
    parser = subparsers.add_parser('delete', parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='name of the game to be deleted')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--username',
        type=str,
        help="identify name of user's private key file")

    parser.add_argument(
        '--key-dir',
        type=str,
        help="identify directory of user's private key file")

    parser.add_argument(
        '--auth-user',
        type=str,
        help='specify username for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--auth-password',
        type=str,
        help='specify password for authentication if REST API '
        'is using Basic Auth')

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for delete transaction to commit')


def create_parent_parser(prog_name):
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)
    parent_parser.add_argument(
        '-v', '--verbose',
        action='count',
        help='enable more verbose output')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        description='Provides subcommands to play Battleship (also known as '
        'Sea Battle) by sending Battleship transactions.',
        parents=[parent_parser])

    subparsers = parser.add_subparsers(title='subcommands', dest='command')

    subparsers.required = True

    add_create_parser(subparsers, parent_parser)
    add_list_parser(subparsers, parent_parser)
    add_show_parser(subparsers, parent_parser)
    add_shoot_parser(subparsers, parent_parser)
    add_delete_parser(subparsers, parent_parser)

    return parser


def do_list(args):
    url = _get_url(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=None)

    game_list = [
        game.split(',')
        for games in client.list(auth_user=auth_user,
                                 auth_password=auth_password)
        for game in games.decode().split('|')
    ]

    if game_list is not None:
        fmt = "%-15s %-15.15s %-15.15s %-9s %s"
        print(fmt % ('GAME', 'PLAYER 1', 'PLAYER 2', 'BOARD', 'STATE'))
        for game_data in game_list:

            name, board, game_state, player1, player2 = game_data

            print(fmt % (name, player1[:6], player2[:6], board, game_state))
    else:
        raise BattleshipException("Could not retrieve game listing.")


def do_show(args):
    name = args.name

    url = _get_url(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=None)

    data = client.show(name, auth_user=auth_user, auth_password=auth_password)

    if data is not None:

        board_str_P1, board_str_P2, game_state, player1, player2 = {
            name: (board_P1, board_P2, state, player_1, player_2)
            for name, board_P1, board_P2, state, player_1, player_2 in [
                game.split(',')
                for game in data.decode().split('|')
            ]
        }[name]

        board_P1 = list(board_str_P1.replace("-", " "))
        board_P2 = list(board_str_P2.replace("-", " "))

        ## ERROR IN TEST only works when you can only display when it's your turn
        
        # battleship_state.set_game(battleship_payload.name, game)
        # game = battleship_state.get_game(battleship_payload.name)
        # if (game.player1 and game_state == 'P1-NEXT'
        #         and game.player1 != signer) or \
        #             (game.player2 and game.state == 'P2-NEXT'
        #              and game.player2 != signer):
        #         raise InvalidTransaction(
        #             "Not this player's turn: {}".format(signer[:6]))

        if game_state == 'P1-NEXT': #P1-NEXT = P1 turn 
        
            board_enemy = display_enemy(board_P2)
            board_perso = board_P1
        else :
            board_enemy = display_enemy(board_P1)
            board_perso = board_P2

        print("GAME:     : {}".format(name))
        print("PLAYER 1  : {}".format(player1[:6]))
        print("PLAYER 2  : {}".format(player2[:6]))
        print("STATE     : {}".format(game_state))
        print("Enemy board")
        print("")
        print("   | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 ")
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" A | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[0], board_enemy[1], board_enemy[2], board_enemy[3], board_enemy[4], board_enemy[5], board_enemy[6], board_enemy[7], board_enemy[8], board_enemy[9]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" B | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[10], board_enemy[11], board_enemy[12], board_enemy[13], board_enemy[14], board_enemy[15], board_enemy[16], board_enemy[17], board_enemy[18], board_enemy[19]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" C | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[20], board_enemy[21], board_enemy[22], board_enemy[23], board_enemy[24], board_enemy[25], board_enemy[26], board_enemy[27], board_enemy[28], board_enemy[29]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" D | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[30], board_enemy[31], board_enemy[32], board_enemy[33], board_enemy[34], board_enemy[35], board_enemy[36], board_enemy[37], board_enemy[38], board_enemy[39]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" E | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[40], board_enemy[41], board_enemy[42], board_enemy[43], board_enemy[44], board_enemy[45], board_enemy[46], board_enemy[47], board_enemy[48], board_enemy[49]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" F | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[50], board_enemy[51], board_enemy[52], board_enemy[53], board_enemy[54], board_enemy[55], board_enemy[56], board_enemy[57], board_enemy[58], board_enemy[59]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" G | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[60], board_enemy[61], board_enemy[62], board_enemy[63], board_enemy[64], board_enemy[65], board_enemy[66], board_enemy[67], board_enemy[68], board_enemy[69]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" H | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[70], board_enemy[71], board_enemy[72], board_enemy[73], board_enemy[74], board_enemy[75], board_enemy[76], board_enemy[77], board_enemy[78], board_enemy[79]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" I | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[80], board_enemy[81], board_enemy[82], board_enemy[83], board_enemy[84], board_enemy[85], board_enemy[86], board_enemy[87], board_enemy[88], board_enemy[89]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" J | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_enemy[90], board_enemy[91], board_enemy[92], board_enemy[93], board_enemy[94], board_enemy[95], board_enemy[96], board_enemy[97], board_enemy[98], board_enemy[99]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print("")
        print("Your board")
        print("   | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 ")
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" A | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[0], board_perso[1], board_perso[2], board_perso[3], board_perso[4], board_perso[5], board_perso[6], board_perso[7], board_perso[8], board_perso[9]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" B | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[10], board_perso[11], board_perso[12], board_perso[13], board_perso[14], board_perso[15], board_perso[16], board_perso[17], board_perso[18], board_perso[19]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" C | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[20], board_perso[21], board_perso[22], board_perso[23], board_perso[24], board_perso[25], board_perso[26], board_perso[27], board_perso[28], board_perso[29]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" D | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[30], board_perso[31], board_perso[32], board_perso[33], board_perso[34], board_perso[35], board_perso[36], board_perso[37], board_perso[38], board_perso[39]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" E | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[40], board_perso[41], board_perso[42], board_perso[43], board_perso[44], board_perso[45], board_perso[46], board_perso[47], board_perso[48], board_perso[49]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" F | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[50], board_perso[51], board_perso[52], board_perso[53], board_perso[54], board_perso[55], board_perso[56], board_perso[57], board_perso[58], board_perso[59]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" G | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[60], board_perso[61], board_perso[62], board_perso[63], board_perso[64], board_perso[65], board_perso[66], board_perso[67], board_perso[68], board_perso[69]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" H | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[70], board_perso[71], board_perso[72], board_perso[73], board_perso[74], board_perso[75], board_perso[76], board_perso[77], board_perso[78], board_perso[79]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" I | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[80], board_perso[81], board_perso[82], board_perso[83], board_perso[84], board_perso[85], board_perso[86], board_perso[87], board_perso[88], board_perso[89]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print(" J | {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board_perso[90], board_perso[91], board_perso[92], board_perso[93], board_perso[94], board_perso[95], board_perso[96], board_perso[97], board_perso[98], board_perso[99]))
        print("---|---|---|---|---|---|---|---|---|---|---")
        print("")

    else:
        raise BattleshipException("Game not found: {}".format(name))

def display_enemy(board):
    board_disp = []
    for k in board :
        if k in ID_BOAT :
            board_disp.append(" ")
        else :
            board_disp.append(k)
    return board_disp


def do_create(args):
    name = args.name

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.create(
            name, wait=args.wait,
            auth_user=auth_user,
            auth_password=auth_password)
    else:
        response = client.create(
            name, auth_user=auth_user,
            auth_password=auth_password)

    print("Response: {}".format(response))


def do_shoot(args):
    name = args.name
    column = args.col
    row = args.row 

    # Conversion of the COL ROW format to INT of the space 
    rownames = {
        "A": 0, 
        "B": 1, 
        "C": 2, 
        "D": 3, 
        "E": 4, 
        "F": 5, 
        "G": 6, 
        "H": 7, 
        "I": 8, 
        "J": 9, 
    }
    space = rownames[row]*10+column 

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.shoot(
            name, space, wait=args.wait,
            auth_user=auth_user,
            auth_password=auth_password)
    else:
        response = client.shoot(
            name, space,
            auth_user=auth_user,
            auth_password=auth_password)

    print("Response: {}".format(response))


def do_delete(args):
    name = args.name

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.delete(
            name, wait=args.wait,
            auth_user=auth_user,
            auth_password=auth_password)
    else:
        response = client.delete(
            name, auth_user=auth_user,
            auth_password=auth_password)

    print("Response: {}".format(response))


def _get_url(args):
    return DEFAULT_URL if args.url is None else args.url


def _get_keyfile(args):
    username = getpass.getuser() if args.username is None else args.username
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, username)


def _get_auth_info(args):
    auth_user = args.auth_user
    auth_password = args.auth_password
    if auth_user is not None and auth_password is None:
        auth_password = getpass.getpass(prompt="Auth Password: ")

    return auth_user, auth_password


def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    if args.verbose is None:
        verbose_level = 0
    else:
        verbose_level = args.verbose

    setup_loggers(verbose_level=verbose_level)

    if args.command == 'create':
        do_create(args)
    elif args.command == 'list':
        do_list(args)
    elif args.command == 'show':
        do_show(args)
    elif args.command == 'shoot':
        do_shoot(args)
    elif args.command == 'delete':
        do_delete(args)
    else:
        raise BattleshipException("invalid command: {}".format(args.command))


def main_wrapper():
    try:
        main()
    except BattleshipException as err:
        print("Error: {}".format(err), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)