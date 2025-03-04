from typing import List

import numpy as np
from matplotlib import pyplot as plt, rcParams
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from . import TEXTSIZE
from .. import BANNER
from ..common import log
from ..trace import Trace


def create(path: str, name: str, header: dict, traces: List[Trace]) -> Figure:
    log.info('Making small PID plot...')

    fig = plt.figure('Small response plot: Log number: ' + header['logNum'] + '          ' + path,
                     figsize=(7, 12))
    
    colors = ['tab:red', 'tab:green', 'tab:blue']
    contourcolors = ['Reds', 'Greens', 'Blues']

    for i, trace in enumerate(traces):
        cmap = plt.cm.get_cmap(contourcolors[i])
        cmap._init()
        alphas = np.abs(np.linspace(0., 0.2, cmap.N, dtype=np.float64))
        cmap._lut[:-3, -1] = alphas
        ax3 = plt.subplot(3, 1, i + 1)
        plt.contourf(*trace.resp_low[2], cmap=cmap, linestyles=None, antialiased=True,
                     levels=np.linspace(0, 1, 20, dtype=np.float64))
        plt.plot(trace.time_resp, trace.resp_low[0],
                 label=trace.name + ' step response ' + '($<' + str(int(Trace.threshold)) + '$) '
                       + ' PIDFF ' + header[trace.name + 'PID'], color = colors[i])

        if trace.high_mask.sum() > 0:
            cmap = plt.cm.get_cmap('Oranges')
            cmap._init()
            alphas = np.abs(np.linspace(0., 0.5, cmap.N, dtype=np.float64))
            cmap._lut[:-3, -1] = alphas
            plt.contourf(*trace.resp_high[2], cmap=cmap, linestyles=None, antialiased=True,
                         levels=np.linspace(0, 1, 20, dtype=np.float64))
            plt.plot(trace.time_resp, trace.resp_high[0],
                     label=trace.name + ' step response ' + '($>' + str(int(Trace.threshold)) + '$) '
                           + ' PIDFF ' + header[trace.name + 'PID'])
        plt.xlim([-0.001, 0.501])

        plt.legend(loc=1)
        plt.ylim([0., 2])
        plt.ylabel('strength')
        ax3.get_yaxis().set_label_coords(-0.1, 0.5)
        plt.xlabel('response time in s')

        plt.grid()
        
    log.info('Saving as image...')
    plt.savefig(path[:-13] + name + '_' + str(header['logNum']) + '_response.pdf', bbox_inches="tight")
    return fig
