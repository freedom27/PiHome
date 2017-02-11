from time import sleep
from gpiomanager import GPIO


class SensorsManager(object):
    """This class uses its sensor to sample data and publish it on a mqtt broker

    The class collect sensor data and publish it on a mqtt broker. The data comes
    either from sample operations or from event risen from sensors.
    To start listening for events just instantiating the class is enough whereas
    to begin collecting sensor's data the method "start_sampling" should be called.

    Attributes:
        _sensors ([Sensor]): the array of sensors to use
        _events ({int: str}): the dictionary of event to listen for
        _mqtt_client (MQTTClient): the mqtt client to use to puplish the sampled data and notify events
        _sampling_interval (int): the amount of time (in seconds) between each sampling

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
        # registering the events to detect
        GPIO.setmode(GPIO.BCM)
        for event_channel in self._events.keys():
            GPIO.setup(event_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(event_channel, GPIO.RISING, callback=self._post_event, bouncetime=300)
        self._sampling_interval = sampling_interval

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
        self._mqtt_client.publish_event(self._events[channel])

    def start_sampling(self):
        """Method to invoke to start sampling data using the sensors"""
        while True:
            samples = [sample for sublist in [sensor.sample() for sensor in self._sensors] for sample in sublist]
            self._post_samples(samples)
            sleep(self._sampling_interval)
