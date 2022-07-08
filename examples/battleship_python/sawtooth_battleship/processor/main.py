import sys
import os
import argparse
import pkg_resources

from sawtooth_battleship.processor.handler import BattleshipTransactionHandler
from sawtooth_battleship.processor.config.battleship import BattleshipConfig
from sawtooth_battleship.processor.config.battleship import \
    load_default_battleship_config
from sawtooth_battleship.processor.config.battleship import \
    load_toml_battleship_config
from sawtooth_battleship.processor.config.battleship import \
    merge_battleship_config

from sawtooth_sdk.processor.core import TransactionProcessor
from sawtooth_sdk.processor.log import init_console_logging
from sawtooth_sdk.processor.log import log_configuration
from sawtooth_sdk.processor.config import get_log_config
from sawtooth_sdk.processor.config import get_log_dir
from sawtooth_sdk.processor.config import get_config_dir


DISTRIBUTION_NAME = 'sawtooth-battleship'


def parse_args(args):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '-C', '--connect',
        help='Endpoint for the validator connection')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Increase output sent to stderr')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='print version information')

    return parser.parse_args(args)


def load_battleship_config(first_config):
    default_battleship_config = \
        load_default_battleship_config()
    conf_file = os.path.join(get_config_dir(), 'battleship.toml')

    toml_config = load_toml_battleship_config(conf_file)

    return merge_battleship_config(
        configs=[first_config, toml_config, default_battleship_config])


def create_battleship_config(args):
    return BattleshipConfig(connect=args.connect)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = parse_args(args)
    processor = None
    try:
        arg_config = create_battleship_config(opts)
        battleship_config = load_battleship_config(arg_config)
        processor = TransactionProcessor(url=battleship_config.connect)
        log_config = get_log_config(filename="battleship_log_config.toml")

        # If no toml, try loading yaml
        if log_config is None:
            log_config = get_log_config(filename="battleship_log_config.yaml")

        if log_config is not None:
            log_configuration(log_config=log_config)
        else:
            log_dir = get_log_dir()
            # use the transaction processor zmq identity for filename
            log_configuration(
                log_dir=log_dir,
                name="battleship-" + str(processor.zmq_id)[2:-1])

        init_console_logging(verbose_level=opts.verbose)

        handler = BattleshipTransactionHandler()

        processor.add_handler(handler)

        processor.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:  # pylint: disable=broad-except
        print("Error: {}".format(e))
    finally:
        if processor is not None:
            processor.stop()