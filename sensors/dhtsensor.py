import MyPyDHT
from .sensor import Sensor, Sample
from ..common.logger import logger


class DHTSensor(Sensor):
    """Class for sensors of type DHT11, DHT22, AM2302

    The class is a wrapper around the driver of the DHT sensor
    (supported modelse: DHT11, DHT22 and AM2302). It holds the configuration
    to use while the application run (such as which data to sample, the sensor model
    and the pin on which the sensor is connected). Being a subclass os Sensor
    it implements the method "semple" which returns a dictionary with the data sampled
    by the sensor.

    Attributes:
        _sensors ([str]): the list of data we want to sample (elements can be: "temerature" and "humidity").
                         DHT sensors can sample both temperature and humidity, in this array we list which
                         of the two should be returned in the sample.
        _pin (int): the GPIO pin number to which the sensor is connected
        _model (:enum: MyPyDHT.Sensor): an enum of the sensor driver defining the model of the sensor
                                        (the possible values are DHT11 and DHT22)
    """

    def __init__(self, active_sensors, model, gpio_pin):
        """Initialize the DHTSensor class

        Args:
            active_sensors ([str]): the list of data we want to sample (elements can be: "temerature" and "humidity").
            model (str): a string describing the model of the sensor, if it is equal to "DHT11" then the model used
                         will indeed be the DHT11 whereas with any other string DHT22 will be used
            gpio_pin (int): the gpio pin to which the sensor is connected
        """
        self._sensors = active_sensors
        self._pin = gpio_pin
        if model == "DHT11":
            self._model = MyPyDHT.Sensor.DHT11
        else:
            self._model = MyPyDHT.Sensor.DHT22

    def _fetch_data(self, samples):
        """Collect sensor's data

        This method access the sensor and read both the temperature and the humidity, then it checks what data
        should be returned (listed in the array _sensor) and add it to the returned samples list.
        The method is an implementation of an abstract method defined in the Sensor abstract class
        (from which DHTSensor inherit)

        Args:
            samples ([Sample]): an empty array to be filled with Sample objects
        """
        try:
            humidity, temperature = MyPyDHT.sensor_read(self._model, self._pin, reading_attempts=10, use_cache=True)
            if "temperature" in self._sensors:
                samples.append(Sample("temperature", round(temperature, 2), "C"))
            if "humidity" in self._sensors:
                samples.append(Sample("humidity", round(humidity, 2), "%"))
        except MyPyDHT.DHTException as error:
            logger.error(error.message)
