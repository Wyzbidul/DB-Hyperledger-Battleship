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


def add_take_parser(subparsers, parent_parser):
    parser = subparsers.add_parser(
        'take',
        help='Takes a space in an battleship game',
        description='Sends a transaction to take a square in the battleship game '
        'with the identifier <name>. This transaction will fail if the '
        'specified game does not exist.',
        parents=[parent_parser])

    parser.add_argument(
        'name',
        type=str,
        help='identifier for the game')

    parser.add_argument(
        'space',
        type=int,
        help='number of the square to take (A1-J10); the upper-left space is '
        'A1, and the lower-right space is J10. It is a 10 by 10 grid '
        '(1-10 and A-J coordinates)')

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
        help='set time, in seconds, to wait for take transaction '
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
    add_take_parser(subparsers, parent_parser)
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

        board_str, game_state, player1, player2 = {
            name: (board, state, player_1, player_2)
            for name, board, state, player_1, player_2 in [
                game.split(',')
                for game in data.decode().split('|')
            ]
        }[name]

        board = list(board_str.replace("-", " "))


        ## To be revised for each player view /!\
        print("GAME:     : {}".format(name))
        print("PLAYER 1  : {}".format(player1[:6]))
        print("PLAYER 2  : {}".format(player2[:6]))
        print("STATE     : {}".format(game_state))
        print("Enemy board")
        print("")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[0], board[1], board[2], board[3], board[4], board[5], board[6], board[7], board[8], board[9]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[10], board[11], board[12], board[13], board[14], board[15], board[16], board[17], board[18], board[19]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[20], board[21], board[22], board[23], board[24], board[25], board[26], board[27], board[28], board[29]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[30], board[31], board[32], board[33], board[34], board[35], board[36], board[37], board[38], board[39]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[40], board[41], board[42], board[43], board[44], board[45], board[46], board[47], board[48], board[49]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[50], board[51], board[52], board[53], board[54], board[55], board[56], board[57], board[58], board[59]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[60], board[61], board[62], board[63], board[64], board[65], board[66], board[67], board[68], board[69]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[70], board[71], board[72], board[73], board[74], board[75], board[76], board[77], board[78], board[79]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[80], board[81], board[82], board[83], board[84], board[85], board[86], board[87], board[88], board[89]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[90], board[91], board[92], board[93], board[94], board[95], board[96], board[97], board[98], board[99]))
        print("")
        print("Your board")
        print("")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[100], board[101], board[102], board[103], board[104], board[105], board[106], board[107], board[108], board[109]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[110], board[111], board[112], board[113], board[114], board[115], board[116], board[117], board[118], board[119]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[120], board[121], board[122], board[123], board[124], board[125], board[126], board[127], board[128], board[129]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[130], board[131], board[132], board[133], board[134], board[135], board[136], board[137], board[138], board[139]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[140], board[141], board[142], board[143], board[144], board[145], board[146], board[147], board[148], board[149]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[150], board[151], board[152], board[153], board[154], board[155], board[156], board[157], board[158], board[159]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[160], board[161], board[162], board[163], board[164], board[165], board[166], board[167], board[168], board[169]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[170], board[171], board[172], board[173], board[174], board[175], board[176], board[177], board[178], board[179]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[180], board[181], board[182], board[183], board[184], board[185], board[186], board[187], board[188], board[189]))
        print(" ---|---|---|---|---|---|---|---|---|---")
        print("  {} | {} | {} | {} | {} | {} | {} | {} | {} | {}".format(board[190], board[191], board[192], board[193], board[194], board[195], board[196], board[197], board[198], board[199]))
        print("")

    else:
        raise BattleshipException("Game not found: {}".format(name))


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


def do_take(args):
    name = args.name
    space = args.space

    url = _get_url(args)
    keyfile = _get_keyfile(args)
    auth_user, auth_password = _get_auth_info(args)

    client = BattleshipClient(base_url=url, keyfile=keyfile)

    if args.wait and args.wait > 0:
        response = client.take(
            name, space, wait=args.wait,
            auth_user=auth_user,
            auth_password=auth_password)
    else:
        response = client.take(
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
    elif args.command == 'take':
        do_take(args)
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