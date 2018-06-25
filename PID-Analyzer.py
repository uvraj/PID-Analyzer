#!/usr/bin/env python3
# ----------------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <florian.melsheimer@gmx.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Florian Melsheimer
# ----------------------------------------------------------------------------------

import argparse
import configparser
import os
import platform
import sys
import time
from ast import literal_eval

from matplotlib import pyplot

from pidanalyzer import BANNER
from pidanalyzer.bb_log import BbLog
from pidanalyzer.logger import log
from pidanalyzer.utils import strip_quotes

CONFIG_FILE = "config.ini"
DEFAULT_NOISE_BOUNDS = [[1., 10.1], [1., 100.], [1., 100.], [0., 4.]]


def run_analysis(log_file_path, plot_name, blackbox_decode, show, noise_bounds):
    BbLog(log_file_path, plot_name, blackbox_decode, show, noise_bounds)
    log.info('Analysis complete, showing plot. (Close plot to exit.)')


def clean_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(strip_quotes(path)))


def get_default_blackbox_decode_path() -> str:
    cwd = os.path.dirname(__file__)
    config_file_path = os.path.join(cwd, CONFIG_FILE)
    if not os.path.exists(config_file_path):
        system = platform.system()
        if system == 'Windows':
            executable = 'Blackbox_decode.exe'
        else:
            executable = 'blackbox_decode'
        return os.path.join(cwd, executable)
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config['paths']['blackbox_decode']


def arguments_mode(args):
    for log_path in args.log_paths:
        run_analysis(clean_path(log_path), args.name, args.blackbox_decode, not args.hide, args.noise_bounds)
    if not args.hide:
        pyplot.show()
    else:
        pyplot.cla()
        pyplot.clf()
    return 0


def interactive_mode(args):
    while True:
        log.info('Interactive mode: Enter log file, or type close when done.')

        try:
            time.sleep(0.1)
            raw_path = input('Blackbox log file path (type or drop here): ')
            if raw_path == 'close':
                log.info('Goodbye!')
                break
            raw_paths = strip_quotes(raw_path).replace("''", '""').split('""')  # seperate multiple paths
            name = input('Optional plot name:') or args.name
            showpyplot = input('Show plot window when done? [Y]/N')
            if showpyplot:
                args.hide = 'N' == showpyplot.strip().upper()
            noise_bounds = input('Bounds on noise plot: [default/last] | copy and edit | "auto"\nCurrent: ' + str(
                args.noise_bounds) + '\n')
            if noise_bounds:
                args.noise_bounds = literal_eval(noise_bounds.strip())
        except (EOFError, KeyboardInterrupt):
            log.info('Goodbye!')
            break

        for path in raw_paths:
            if os.path.isfile(clean_path(path)):
                run_analysis(clean_path(path), name, args.blackbox_decode, args.show, args.noise_bounds)
            else:
                log.info('No valid input path!')
                return 1

        if not args.hide:
            pyplot.show()
        else:
            pyplot.cla()
            pyplot.clf()

    return 0


def main(args) -> int:
    blackbox_decode_path = clean_path(args.blackbox_decode)
    if not os.path.isfile(blackbox_decode_path):
        parser.error(
            ('Could not find blackbox_decode (used to generate CSVs from '
             'your BBL file) at %s. You may need to install it from '
             'https://github.com/cleanflight/blackbox-tools/releases.')
            % blackbox_decode_path)

    log.info('Decoding with %r' % blackbox_decode_path)
    log.info(BANNER)

    if args.log_paths:
        return arguments_mode(args)
    else:
        return interactive_mode(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-l', '--log', action='append', dest='log_paths',
                        help='Log file(s) to analyse; can be specified multiple times. Omit for interactive prompt.')
    parser.add_argument('-n', '--name', default='tmp', help='Plot name.')
    parser.add_argument('--blackbox_decode',
                        default=get_default_blackbox_decode_path(),
                        help='Path to Blackbox_decode.exe.')
    parser.add_argument('-d', '--hide', action='store_true',
                        help='hide plot window when done.')
    parser.add_argument('-b', '--noise-bounds',
                        default=''.join(repr(DEFAULT_NOISE_BOUNDS).split(' ')),
                        type=literal_eval,
                        help='bounds of plots in noise analysis. use "auto" for autoscaling.')

    cli_args = parser.parse_args()

    sys.exit(main(cli_args))
