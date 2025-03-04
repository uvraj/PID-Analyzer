#!/usr/bin/env python3
# ----------------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <florian.melsheimer@gmx.de> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Florian Melsheimer
# ----------------------------------------------------------------------------------

import argparse
import sys
import time
from ast import literal_eval

from matplotlib import pyplot, pyplot as plt

from pidanalyzer.common import *
from pidanalyzer import common, loaders, BANNER
from pidanalyzer.plotting import show_plots

# LaTeX-esque output

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": "cmr10",
    "mathtext.fontset": "cm",
    "axes.unicode_minus": False,
    "axes.linewidth": 0.5,
    "grid.linewidth": 0.3,
    "lines.linewidth": 0.7,
    # "text.usetex": True,
})

def analyze_file(path: str, plot_name: str, hide: bool, noise_bounds: list = DEFAULT_NOISE_BOUNDS):
    tmp_path = os.path.join(os.path.dirname(path), plot_name)
    if not os.path.isdir(tmp_path):
        os.makedirs(tmp_path)
    loader = loaders.resolve(path, plot_name)
    for i, header in enumerate(loader.headers):
        show_plots(plot_name, header, loader.data[i], noise_bounds)
        if hide:
            plt.cla()
            plt.clf()
    loader.clean_up()
    log.info('Analysis complete, showing plot. (Close plot to exit.)')


def arguments_mode(args) -> int:
    for log_path in args.log_paths:
        analyze_file(clean_path(log_path), args.name, args.hide, args.noise_bounds)
    if not args.hide:
        pyplot.show()
    else:
        pyplot.cla()
        pyplot.clf()
    return 0


def interactive_mode(args) -> int:
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
                analyze_file(clean_path(path), name, args.show, args.noise_bounds)
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
    common.BLACKBOX_DECODE_PATH = blackbox_decode_path
    log.info('Decoding with %r' % blackbox_decode_path)
    log.info(BANNER)

    if args.log_paths:
        return arguments_mode(args)
    else:
        return interactive_mode(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(action='append', dest='log_paths', metavar="LOG_PATHS",
                        help='log file(s) to analyze or omit for interactive prompt')
    parser.add_argument('-n', '--name', default='tmp', help='plot name')
    parser.add_argument('--blackbox_decode', metavar="PATH", default=get_blackbox_decode_path(),
                        help='path to blackbox_decode tool')
    parser.add_argument('-d', '--hide', action='store_true',
                        help='hide plot window when done')
    parser.add_argument('-b', '--noise-bounds', default=''.join(repr(DEFAULT_NOISE_BOUNDS).split(' ')),
                        type=literal_eval,
                        help='bounds of plots in noise analysis (use "auto" for autoscaling)')

    cli_args = parser.parse_args()

    sys.exit(main(cli_args))
