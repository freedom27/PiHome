import multiprocessing
from ..common.logger import logger
from ..common.gpiomanager import GPIO
from ..common.stoppableprocess import StoppableLoopProcess


class SensorsManager(StoppableLoopProcess):
    """This class is a Process that uses its sensor to sample data and publish it on a mqtt broker

    The class, which is a subclass of multiprocessing.Process, collect sensor data and
    publish it on a mqtt broker. The data comes either from sample operations or
    from event risen from sensors.
    To start listening for events just instantiating the class is enough whereas
    to begin collecting sensor's data the method "start_sampling" should be called.

    Attributes:
        _sensors ([Sensor]): the array of sensors to use
        _events ({int: str}): the dictionary of event to listen for
        _mqtt_client (MQTTClient): the mqtt client to use to puplish the sampled data and notify events
        _sampling_interval (int): the amount of time (in seconds) between each sampling
        _lock (multiprocessing.Lock): a lock use to prevent process termination while publishing data
        _stop_sampling (threading.Event): event to detect when the process should be interrupted; as long
                                          as the internal flag is set to False the process keeps running

    """

    def __init__(self, sensors, events, mqtt_client, sampling_interval=60):
        """Initialize the SensorsManager class

        Init the SensorManager class with a list of sensors, a list of event to listen to,
        the mqtt client to use and a sampling interval

        Args:
            sensors ([Sensor]): the array of sensors to use
            events ({int: str}): the dictionary of event to listen for
            mqtt_client (MQTTClient): the mqtt client to use to puplish the sampled data and notify events
            sampling_interval (int): the amount of time (in seconds) between each sampling,
                                     the default value is 60 seconds
        """
        self._sensors = sensors
        self._events = events
        self._mqtt_client = mqtt_client
        self._lock = multiprocessing.Lock()
        super(SensorsManager, self).__init__(sampling_interval)

    def _post_samples(self, samples):
        """Publish samples on the mqtt broker

        Args:
            samples ([{str: float}]): an array of samples, each sample is a dictionary that must have at
                                      least a key "type" (will be used to generate the topic)
        """
        logger.info("Publishing samples")
        if self._lock.acquire(block=True, timeout=5):
            for sample in samples:
                self._mqtt_client.publish_sample(sample)
            self._lock.release()

    def _post_event(self, channel):
        """Notify events on the mqtt broker

        Args:
            channel (int): the number of the gpio port rising the event
        """
        # to avoid the disconnection of the client let's acquire the lock,
        # in this case the timeout is 20 seconds because if the lock is acquired
        # by the sampling method it could take a while since some sensors may require
        # time to acquire the data
        logger.info("Publishing event")
        if self._lock.acquire(block=True, timeout=20):
            self._mqtt_client.publish_event(self._events[channel])
            self._lock.release()

    def _sample(self):
        """Use the sensors to sample data and publish it on the MQTT broker

        The method collect data from all its sensor and then publish it all on the MQTT broker
        """
        logger.info("Collecting samples from sensors.")
        samples = [sample for sublist in [sensor.sample() for sensor in self._sensors] for sample in sublist]
        self._post_samples(samples)

    def _setup(self):
        """ Setting up the process for execution

        The method estabilishes the connection with the broker and registers the callbacks for the GPIO events
        """
        # starts the MQTT client
        self._mqtt_client.start()
        # registering the events to detect
        for event_channel in self._events.keys():
            GPIO.setup(event_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            # we start listening for events on the event_chnnel port, a bouncetime of 10000 means that
            # after an event is detected a minimum of 10 seconds has to pass before another event could be detected
            GPIO.add_event_detect(event_channel, GPIO.RISING, callback=self._post_event, bouncetime=10000)
            logger.info("Listening for events on GPIO #%d", event_channel)
        logger.info("Sampling started")

    def _teardown(self):
        """ Prepare the process for temination

        The method closes the connection to the broker and unregisters the callbacks for the GPIO events
        """
        logger.info("Sampling stopped")
        # perform clean-up befor exiting
        if self._lock.acquire(block=True, timeout=10):
            #unregistering the events' detection
            for event_channel in self._events.keys():
                GPIO.remove_event_detect(event_channel)
                logger.info("Stopped listening for events on GPIO #%d", event_channel)
            #disconnect from the mqtt broker
            self._mqtt_client.stop()

    def _loop(self):
        """ Collects data from sensors and publishes them on the broker"""
        self._sample()
