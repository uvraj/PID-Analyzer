class PidAnalyzerException(BaseException):
    pass


class LoaderNotFoundError(PidAnalyzerException):
    """Raised when an appropriate Loader cannot be found for a file.
    """

    def __init__(self, path: str, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self._path = path

    def __str__(self):
        return "Unknown format: '%s'" % self._path


class InvalidDataError(PidAnalyzerException):
    """Raised when an error occurs during loading data.
    """

    def __init__(self, path: str, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self._path = path
        self._message = kwargs.get("message")

    def __str__(self):
        s = "Invalid data: '%s'" % self._path
        if self._message is not None:
            s += " (%s)" % str(self._message)
        return s
