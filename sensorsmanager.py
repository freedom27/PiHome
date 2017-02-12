from time import sleep
import multiprocessing
from gpiomanager import GPIO


class SensorsManager(multiprocessing.Process):
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
        self._sampling_interval = sampling_interval
        self._lock = multiprocessing.Lock()
        super(SensorsManager, self).__init__()

    def _post_samples(self, samples):
        """Publish samples on the mqtt broker

        Args:
            samples ([{str: float}]): an array of samples, each sample is a dictionary that must have at
                                      least a key "type" (will be used to generate the topic)
        """
        for sample in samples:
            self._mqtt_client.publish_sample(sample)

    def _post_event(self, channel):
        """Notify events on the mqtt broker

        Args:
            channel (int): the number of the gpio port rising the event
        """
        # to avoid the disconnection of the client let's acquire the lock,
        # in this case the timeout is 20 seconds because if the lock is acquired
        # by the sampling method it could take a while since some sensors may require
        # time to acquire the data
        if self._lock.acquire(block=True, timeout=20):
            self._mqtt_client.publish_event(self._events[channel])
            self._lock.release()

    def _start_sampling(self):
        """Method to invoke to start sampling data using the sensors"""
        while self._lock.acquire(block=True, timeout=3):
            samples = [sample for sublist in [sensor.sample() for sensor in self._sensors] for sample in sublist]
            self._post_samples(samples)
            # releasing the lock... it is safe to terminate the process while sleeping
            self._lock.release()
            sleep(self._sampling_interval)

    def run(self):
        """Start the process

        Register the GPIO events to listen and start sampling
        """
        # starts the MQTT client
        self._mqtt_client.start()
        # registering the events to detect
        for event_channel in self._events.keys():
            GPIO.setup(event_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            # we start listening for events on the event_chnnel port, a bouncetime of 10000 means that
            # after an event is detected a minimum of 10 seconds has to pass before another event could be detected
            GPIO.add_event_detect(event_channel, GPIO.RISING, callback=self._post_event, bouncetime=10000)
        self._start_sampling()

    def terminate(self):
        """Terminate the process

        This method proforms some clean-up (disconnection from the MQTT broker and unregistration of GPIO events)
        befor terminating the process
        """
        if self._lock.acquire(block=True, timeout=10):
            #unregistering the events' detection
            for event_channel in self._events.keys():
                GPIO.remove_event_detect(event_channel)
            #disconnect from the mqtt broker
            self._mqtt_client.stop()
        super(SensorsManager, self).terminate()
