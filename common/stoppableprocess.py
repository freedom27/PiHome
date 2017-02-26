import multiprocessing
import threading
import signal
from ..common.logger import logger


class StoppableProcess(multiprocessing.Process):
    """This is a generic class to be extendend to implement Processes that terminate in a controlled way

    The class register its internal method _shutdown as a callback when receiving the SIGTERM and SIGINT
    signals, this way cleanup operations can be performed before terminating the process.
    It is important to remember that the operations performed within the _shutdown method MUST lead to the
    termination of the process in a finite amount of time (in fact since the SIGTERM and SIGINT signals are
    intercepted they are not terminating the process anymore)

    """

    def __init__(self):
        # register the shutdown method when a SIGTERM is detected to perform a clean process termination
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)
        super(StoppableProcess, self).__init__()

    def _shutdown(self, signum, frame):
        """Stop internal operations

        Method to call to trigger termination of the process (to be used registering it as a SIGNAL handler);
        This method should be extended to perform proper cleanup operations.

        Args:
            signum (int): the number associated to the signal received
            frame (obj): current stack frame object
        """
        pass


class StoppableLoopProcess(StoppableProcess):

    def __init__(self, loop_interval):
        self._stop_looping = threading.Event()
        self._loop_interval = loop_interval
        super(StoppableLoopProcess, self).__init__()

    def _shutdown(self, signum, frame):
        """Stop internal operations

        Method to call to trigger termination of the process (to be used registering it as a SIGNAL handler);
        it sets the internal stop_looping event to True causing the halt of the loop as soon as the ongoing
        operation are completed (effectively causing the end of the process)

        Args:
            signum (int): the number associated to the signal received
            frame (obj): current stack frame object
        """
        logger.warning("Terminatin process. Signal %d received while in frame %s", signum, frame)
        self._stop_looping.set()

    def _wait(self, time_interval):
        self._stop_looping.wait(timeout=time_interval)

    def _setup(self):
        pass

    def _teardown(self):
        pass

    def _loop(self):
        pass

    def run(self):
        self._setup()

        while not self._stop_looping.is_set():
            self._loop()
            # to be able to gracefully stop sleeping in case of process temination we do use an event that is set to
            # true when the process has to terminate; therefore if the process is not terminated this wait will act
            # as a sleep for the timeout time
            self._wait(self._loop_interval)

        self._teardown()
