import configparser
import os
import platform

CONFIG_FILE = "config.ini"
BLACKBOX_DECODE_PATH = None
DEFAULT_NOISE_BOUNDS = [[1., 10.1], [1., 100.], [1., 100.], [0., 4.]]


def strip_quotes(filepath: str) -> str:
    return filepath.strip().strip("'").strip('"')


def clean_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(strip_quotes(path)))


def get_default_blackbox_decode_path() -> str:
    cwd = os.path.dirname(os.path.dirname(__file__))
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
