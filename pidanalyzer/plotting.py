from typing import List

from .common import log
from .figures import noise_figure, response_figure
from .trace import Trace


def show_plots(name: str, header: dict, data: dict, noise_bounds: list):
    path = header["tempFile"]
    log.info("CSV file: " + path)

    log.info('Processing:')
    traces = _create_traces(header, data)
    response_figure.create(path, name, header, traces)
    noise_figure.create(path, name, header, traces, noise_bounds)


def _create_traces(header: dict, data: dict) -> List[Trace]:
    time = data['time_us']
    throttle = ((data['throttle'] - 1000.) / (float(header['maxThrottle']) - 1000.)) * 100.
    tracesdata = [{'name': 'roll'}, {'name': 'pitch'}, {'name': 'yaw'}]

    for i, axisdata in enumerate(tracesdata):
        axisdata.update({'time': time})
        axisdata.update({'p_err': data['PID loop in' + str(i)]})
        axisdata.update({'rcinput': data['rcCommand' + str(i)]})
        axisdata.update({'gyro': data['gyroData' + str(i)]})
        axisdata.update({'PIDsum': data['PID sum' + str(i)]})
        axisdata.update({'d_err': data['d_err' + str(i)]})
        axisdata.update({'debug': data['debug' + str(i)]})
        if 'KISS' in header['fwType']:
            axisdata.update({'P': 1.})
            header.update({'tpa_percent': 0.})
        elif 'Raceflight' in header['fwType']:
            axisdata.update({'P': 1.})
            header.update({'tpa_percent': 0.})
        else:
            axisdata.update({'P': float((header[axisdata['name'] + 'PID']).split(',')[0])})
            header.update({'tpa_percent': (float(header['tpa_breakpoint']) - 1000.) / 10.})

        axisdata.update({'throttle': throttle})

    traces = []
    for t in tracesdata:
        log.info(t['name'] + '...   ')
        traces.append(Trace(t))
    return traces
