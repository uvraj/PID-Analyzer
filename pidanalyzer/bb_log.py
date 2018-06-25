import os
import subprocess

from matplotlib import pyplot as plt

from pidanalyzer.csv_log import CsvLog
from pidanalyzer.logger import log
from pidanalyzer.utils import strip_quotes

LOG_MIN_BYTES = 500000
# string fragment for identifying the main fields header row in CSV file
CSV_HEADER_ROW_FRAGMENT = "loopIteration"

# different versions of fw have different names for the same thing.
FIELDS_MAP = {'dynThrPID': 'dynThrottle',
              'Craft name': 'craftName',
              'Firmware type': 'fwType',
              'Firmware revision': 'version',
              'Firmware date': 'fwDate',
              'rcRate': 'rcRate', 'rc_rate': 'rcRate',
              'rcExpo': 'rcExpo', 'rc_expo': 'rcExpo',
              'rcYawExpo': 'rcYawExpo', 'rc_expo_yaw': 'rcYawExpo',
              'rcYawRate': 'rcYawRate', 'rc_rate_yaw': 'rcYawRate',
              'rates': 'rates',
              'rollPID': 'rollPID',
              'pitchPID': 'pitchPID',
              'yawPID': 'yawPID',
              ' deadband': 'deadBand',
              'yaw_deadband': 'yawDeadBand',
              'tpa_breakpoint': 'tpa_breakpoint',
              'minthrottle': 'minThrottle',
              'maxthrottle': 'maxThrottle',
              'dtermSetpointWeight': 'dTermSetPoint', 'dterm_setpoint_weight': 'dTermSetPoint',
              'vbat_pid_compensation': 'vbatComp', 'vbat_pid_gain': 'vbatComp',
              'gyro_lpf': 'gyro_lpf',
              'gyro_lowpass_type': 'gyro_lowpass_type',
              'gyro_lowpass_hz': 'gyro_lowpass_hz', 'gyro_lpf_hz': 'gyro_lowpass_hz',
              'gyro_notch_hz': 'gyro_notch_hz',
              'gyro_notch_cutoff': 'gyro_notch_cutoff',
              'dterm_filter_type': 'dterm_filter_type',
              'dterm_lpf_hz': 'dterm_lpf_hz',
              'yaw_lpf_hz': 'yaw_lpf_hz',
              'dterm_notch_hz': 'dterm_notch_hz',
              'dterm_notch_cutoff': 'dterm_notch_cutoff',
              'debug_mode': 'debug_mode',
              }


def deletejunk(loglist: list):
    for logfile in loglist:
        try:
            os.remove(logfile)
            os.remove(logfile[:-3] + '01.csv')
            os.remove(logfile[:-3] + '01.event')
        except FileNotFoundError:
            pass  # ignore


def make_headsdict(log_file: str, log_number: int) -> dict:
    # in case info is not provided by log, empty str is printed in plot
    return {'tempFile': log_file, 'dynThrottle': '', 'craftName': '', 'fwType': '', 'version': '', 'date': '',
            'rcRate': '', 'rcExpo': '', 'rcYawExpo': '', 'rcYawRate': '', 'rates': '', 'rollPID': '',
            'pitchPID': '', 'yawPID': '', 'deadBand': '', 'yawDeadBand': '', 'logNum': str(log_number),
            'tpa_breakpoint': '0', 'minThrottle': '', 'maxThrottle': '', 'tpa_percent': '',
            'dTermSetPoint': '', 'vbatComp': '', 'gyro_lpf': '', 'gyro_lowpass_type': '',
            'gyro_lowpass_hz': '', 'gyro_notch_hz': '', 'gyro_notch_cutoff': '', 'dterm_filter_type': '',
            'dterm_lpf_hz': '', 'yaw_lpf_hz': '', 'dterm_notch_hz': '', 'dterm_notch_cutoff': '',
            'debug_mode': ''}


def read_bbl_headers(loglist: list) -> list:
    heads = []
    for i, bblog in enumerate(loglist):
        headsdict = make_headsdict(bblog.replace(".bbl", ".01.csv"), i)
        with open(bblog, 'rb') as f:
            lines = f.readlines()
        # check for known keys and translate to useful ones.
        for raw_line in lines:
            line = raw_line.decode('latin-1')
            for key in FIELDS_MAP.keys():
                if key in line:
                    val = line.split(':')[-1]
                    headsdict.update({FIELDS_MAP[key]: val[:-1]})
        heads.append(headsdict)
    return heads


def process_csv_headers(loglist: list, tmp_dir: str) -> list:
    heads = []
    for i, csvlog in enumerate(loglist):
        temp_csv_name = os.path.basename(csvlog).replace(".csv", ".main.csv")
        temp_csv_path = os.path.join(tmp_dir, temp_csv_name)
        headsdict = make_headsdict(temp_csv_path, i)
        main_fields_start_line = 0
        with open(csvlog) as f:
            lines = f.readlines()
            for line_num, line in enumerate(lines):
                if CSV_HEADER_ROW_FRAGMENT in line:
                    main_fields_start_line = line_num
                    break
            with open(temp_csv_path, 'w') as tmpf:
                tmpf.writelines(lines[main_fields_start_line:])
        # check for known keys and translate to useful ones.
        for line in lines[:main_fields_start_line]:
            for key in FIELDS_MAP.keys():
                if key in line:
                    val = strip_quotes(line.split(',', 1)[1])
                    headsdict.update({FIELDS_MAP[key]: val})
        heads.append(headsdict)
    return heads


class BbLog:

    def __init__(self, log_file_path, plot_name, blackbox_decode, show, noise_bounds):
        self.blackbox_decode_bin_path = blackbox_decode
        self.tmp_dir = os.path.join(os.path.dirname(log_file_path), plot_name)
        self.name = plot_name
        self.hide = not show
        self.noise_bounds = noise_bounds

        if not os.path.isdir(self.tmp_dir):
            os.makedirs(self.tmp_dir)

        root, ext = os.path.splitext(log_file_path)
        is_csv = ext.upper() == ".CSV"
        if is_csv:
            # skip the call to blackbox_decode if input file is CSV
            self.loglist = [log_file_path]
            self.heads = process_csv_headers(self.loglist, self.tmp_dir)
        else:
            self.loglist = self.decode(log_file_path)
            self.heads = read_bbl_headers(self.loglist)
        self.figs = self._csv_iter(self.heads)

        if not is_csv:
            deletejunk(self.loglist)

    def _csv_iter(self, heads: list) -> list:
        figs = []
        for head in heads:
            CsvLog(head['tempFile'], self.name, head, self.noise_bounds)
            if self.hide:
                plt.cla()
                plt.clf()
        return figs

    def decode(self, path: str) -> list:
        """Splits out one BBL per recorded session and converts each to CSV."""
        with open(path, 'rb') as binary_log_view:
            content = binary_log_view.read()

        # The first line of the overall BBL file re-appears at the beginning
        # of each recorded session.
        try:
            first_newline_index = content.index(str('\n').encode('utf8'))
        except ValueError as e:
            raise ValueError('No newline in %dB of log data from %r.'
                             % (len(content), path), e)
        firstline = content[:first_newline_index + 1]

        split = content.split(firstline)
        bbl_sessions = []
        for i in range(len(split)):
            path_root, path_ext = os.path.splitext(os.path.basename(path))
            temp_path = os.path.join(self.tmp_dir, '%s_temp%d%s' % (path_root, i, path_ext))
            with open(temp_path, 'wb') as newfile:
                newfile.write(firstline + split[i])
            bbl_sessions.append(temp_path)

        loglist = []
        for bbl_session in bbl_sessions:
            size_bytes = os.path.getsize(os.path.join(self.tmp_dir, bbl_session))
            if size_bytes > LOG_MIN_BYTES:
                try:
                    subprocess.check_call([self.blackbox_decode_bin_path, bbl_session])
                    output_path = os.path.join(self.tmp_dir, bbl_session)
                    loglist.append(output_path)
                except subprocess.CalledProcessError:
                    log.error('Error in blackbox_decode of %r' % bbl_session, exc_info=True)
            else:
                # There is often a small bogus session at the start of the file.
                log.warning('Ignoring BBL session %r, %dB < %dB.'
                            % (bbl_session, size_bytes, LOG_MIN_BYTES))
                os.remove(bbl_session)

        return loglist
