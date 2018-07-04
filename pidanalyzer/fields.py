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

# string fragment for identifying the main fields header row in CSV file
CSV_HEADER_ROW_FRAGMENT = "loopIteration"


def headerdict(log_file: str, log_number: int = 0) -> dict:
    # in case info is not provided by log, empty str is printed in plot
    return {'tempFile': log_file, 'dynThrottle': '', 'craftName': '', 'fwType': '', 'version': '', 'date': '',
            'rcRate': '', 'rcExpo': '', 'rcYawExpo': '', 'rcYawRate': '', 'rates': '', 'rollPID': '',
            'pitchPID': '', 'yawPID': '', 'deadBand': '', 'yawDeadBand': '', 'logNum': str(log_number),
            'tpa_breakpoint': '0', 'minThrottle': '', 'maxThrottle': '', 'tpa_percent': '',
            'dTermSetPoint': '', 'vbatComp': '', 'gyro_lpf': '', 'gyro_lowpass_type': '',
            'gyro_lowpass_hz': '', 'gyro_notch_hz': '', 'gyro_notch_cutoff': '', 'dterm_filter_type': '',
            'dterm_lpf_hz': '', 'yaw_lpf_hz': '', 'dterm_notch_hz': '', 'dterm_notch_cutoff': '',
            'debug_mode': ''}
