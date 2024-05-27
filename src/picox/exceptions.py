class RemotePicoException(Exception):
    """An exception raised by a Pico device, raised through"""
    
    def __init__(self, message: str, remote_exception: str):
        """
        Initialize the exception with an error message and the remote traceback.

        Args:
            message (str): A human-readable message describing the error.
            remote_traceback (str): The exception string from the remote device.
        """
        super().__init__(message)
        self.remote_exception = remote_exception

    def __str__(self):
        """
        Return the string representation of the exception,
        """
        return f"{self.args[0]}\nRemote Exception:\n{self.remote_exception}"
