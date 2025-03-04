from typing import List, Tuple

from .common import log
from .figures import noise_figure, response_figure, small_response_figure
from .trace import Trace


def show_plots(name: str, header: dict, data: dict, noise_bounds: list):
    path = header["tempFile"]
    log.info("CSV file: " + path)
    log.info('Processing:')
    traces_header, traces = _create_traces(header, data)
    small_response_figure.create(path, name, traces_header, traces)
    response_figure.create(path, name, traces_header, traces)
    noise_figure.create(path, name, traces_header, traces, noise_bounds)


def _create_traces(header: dict, data: dict) -> Tuple[dict, List[Trace]]:
    time = data['time_us']
    throttle = ((data['throttle'] - 1000.) / (float(header['maxThrottle']) - 1000.)) * 100.
    tracesdata = [{'name': 'roll'}, {'name': 'pitch'}, {'name': 'yaw'}]
    traces_header = dict(header)
    traces = []

    for i, axisdata in enumerate(tracesdata):
        axisdata.update({'time': time})
        si = str(i)
        axisdata.update({'p_err': data['PID loop in' + si]})
        axisdata.update({'rcinput': data['rcCommand' + si]})
        axisdata.update({'gyro': data['gyroData' + si]})
        axisdata.update({'PIDsum': data['PID sum' + si]})
        axisdata.update({'d_err': data['d_err' + si]})
        axisdata.update({'debug': data['debug' + si]})
        if 'KISS' in header['fwType']:
            axisdata.update({'P': 1.})
            traces_header.update({'tpa_percent': 0.})
        elif 'Raceflight' in header['fwType']:
            axisdata.update({'P': 1.})
            traces_header.update({'tpa_percent': 0.})
        else:
            axisdata.update({'P': float((header[axisdata['name'] + 'PID']).split(',')[0])})
            traces_header.update({'tpa_percent': (float(header['tpa_breakpoint']) - 1000.) / 10.})
        axisdata.update({'throttle': throttle})
        log.info(axisdata['name'] + '...   ')
        traces.append(Trace(axisdata))

    return traces_header, traces
