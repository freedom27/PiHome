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
        """Initialize an instance of StoppableProcess
        """
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
    """This is a generic class to be extended to implement a process performing a task repetedly over time.

    The class extends StoppableProcees to be able to be stopped in a clean way any moment. It basically
    execute a certein task repetedly over time till the process is terminated.
    It has 3 methods to override: _setup, _loop and _teardown.
        - _setup must perform all the operation to be done before starting the main loop
        - _loop must perform the core operation to be repeated over time. The execution frequency is configurable
        - _teardown must perform all the operation to be done before terminating the process after the loop is stopped

    Attributes:
        _stop_looping (threading.Event): this is the event used to perform an interruptible sleep. It mustn't be
                                         directly accessed.
        _loop_interval (int): the amount of time, in seconds, to wait between each loop iteration
    """

    def __init__(self, loop_interval):
        """Initialize an instance of StoppableLoopProcess

        This class initialize an instance of StoppableLoopProcess creating the internal wait event and setting
        the looping interval received in input. It is very important, when extending this class, remembering
        to call the super constructor to initialize the loo_interval and instatiate the wait event.

        Args:
            loop_interval (int): the amount of time, in seconds, to wait between each loop iteratio
        """
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
        """This method perform an interruptible sleep

        This metod has to be used whenether the process need to sleep for a certain amount of time. It waits
        on the _stop_looping event, this way if the process must be terminated it doesn't delay the halt

        Args:
            time_interval (int): the amount of time, in seconds, to sleep
        """
        self._stop_looping.wait(timeout=time_interval)

    def _setup(self):
        """Perform all the operations to be done before the main loop

        This method must be overridden performing all the operation that must be performed before starting
        the main loop
        """
        pass

    def _teardown(self):
        """Perform all the operation to be done before the process termination

        This method must be overridden performing all the operation that must be performed before the termination
        of the process (like closing connections and releasing resources)
        """
        pass

    def _loop(self):
        """This method is executed periodically

        This method has to be overridden with the operation that the user wants to be executed periodically.
        The execution interval is defined in the class attribute loop_interval
        """
        pass

    def run(self):
        """Method executed once the process is started

        This method calls the 3 methods that the user extending the class should override to properly have a task
        periodically executed. It callse the _setup, then it loop over the _loop method and once the process receive
        the order to terminate (a SIGTERM or SIGINT) it perform the _teardown
        """
        self._setup()

        while not self._stop_looping.is_set():
            self._loop()
            # to be able to gracefully stop sleeping in case of process temination we do use an event that is set to
            # true when the process has to terminate; therefore if the process is not terminated this wait will act
            # as a sleep for the timeout time
            self._wait(self._loop_interval)

        self._teardown()
