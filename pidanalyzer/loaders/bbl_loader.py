import subprocess
from typing import Tuple

from .blackbox_decode_csv_loader import BlackboxDecodeCsvLoader
from .loader import Loader
from ..common import *

# minimum size of a log to parse in bytes
LOG_MIN_BYTES = 500000


class BblLoader(Loader):
    """Loads Betaflight blackbox log files.
    """

    def __init__(self, path: str, tmp_subdir: str = "tmp"):
        self.tmp_subdir = tmp_subdir
        super().__init__(path, tmp_subdir)

    @staticmethod
    def is_applicable(path: str) -> bool:
        # simply check file extension
        return ".bbl" == os.path.splitext(path)[1].lower() or ".bfl" == os.path.splitext(path)[1].lower()

    def _read_headers(self, path: str) -> Tuple[dict]:
        result = []
        csvfiles = self._bbl_to_csv()
        for i, csvpath in enumerate(csvfiles):
            _, ext = os.path.splitext(csvpath)
            headers = headerdict(csvpath.replace(ext, ".01.csv"), i)
            with open(csvpath, 'rb') as f:
                lines = f.readlines()
            # check for known keys and translate to useful ones.
            for raw_line in lines:
                line = raw_line.decode('latin-1')
                for key in FIELDS_MAP.keys():
                    if key in line:
                        val = line.split(':')[-1]
                        headers.update({FIELDS_MAP[key]: val[:-1]})
            result.append(headers)
        return tuple(result)

    def _read_data(self, path: str) -> Tuple[dict]:
        # load decoded CSV using the dedicated loader
        result = []
        for headers in self.headers:
            result.append(BlackboxDecodeCsvLoader(headers["tempFile"], self.tmp_subdir).data[0])
        return tuple(result)

    def _bbl_to_csv(self) -> list:
        """Splits out one BBL per recorded session and converts each to CSV.

        :return: a list containing paths of the resulting CSV files
        """
        with open(self.path, 'rb') as binary_log_view:
            content = binary_log_view.read()

        # The first line of the overall BBL file re-appears at the beginning
        # of each recorded session.
        try:
            first_newline_index = content.index(str('\n').encode('utf8'))
        except ValueError as e:
            raise ValueError('No newline in %dB of log data from %r.'
                             % (len(content), self.path), e)
        firstline = content[:first_newline_index + 1]

        split = content.split(firstline)
        bbl_sessions = []
        for i in range(len(split)):
            path_root, path_ext = os.path.splitext(os.path.basename(self.path))
            temp_path = os.path.join(self.tmp_path, '%s_temp%d%s' % (path_root, i, path_ext))
            with open(temp_path, 'wb') as newfile:
                newfile.write(firstline + split[i])
            bbl_sessions.append(temp_path)

        from ..common import BLACKBOX_DECODE_PATH
        loglist = []
        for bbl_session in bbl_sessions:
            size_bytes = os.path.getsize(os.path.join(self.tmp_path, bbl_session))
            if size_bytes > LOG_MIN_BYTES:
                try:
                    subprocess.check_call([BLACKBOX_DECODE_PATH, bbl_session])
                    output_path = os.path.join(self.tmp_path, bbl_session)
                    loglist.append(output_path)
                except subprocess.CalledProcessError:
                    log.error('Error in blackbox_decode of %r' % bbl_session, exc_info=True)
            else:
                # There is often a small bogus session at the start of the file.
                log.warning('Ignoring BBL session %r, %dB < %dB.'
                            % (bbl_session, size_bytes, LOG_MIN_BYTES))
                os.remove(bbl_session)

        return loglist
