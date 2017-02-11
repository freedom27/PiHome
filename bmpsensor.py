from sensor import Sensor, Sample
import MyPyBMP180


class BMPSensor(Sensor):
    """The class for sensor type BMP180

    The class is basically a wrapper around the driver for the athmospheric pressure and
    temperature BMP180, it's only configuration parameter is an array stating with kind
    of data it should sample (possible values are: "pressure" and "temperature"); if for
    instance the sensors list were ["pressure"] then the returned samples list would only
    contain pressure data, if, on the other hand, the liste were ["pressure", "temperature"]
    the samples list would contain both pressure and temperature data.

    Attributes:
        _sensors ([str]): the list of data we want to sample (elements can be: "temerature" and "pressure")
    """
    def __init__(self, active_sensors: [str]):
        """Initialize the BMPSensor class

        Args:
            active_sensors ([str]): the list of data we want to sample (elements can be: "temerature" and "pressure")
        """
        self._sensors = active_sensors

    def _fetch_data(self, samples):
        """Collect sensor's data

        This method access the sensor and read both the temperature and the pressure, then it checks what data
        should be returned (listed in the array _sensor) and add it to the returned samples list.
        The method is an implementation of an abstract method defined in the Sensor abstract class
        (from which BMPSensor inherit)

        Args:
            samples ([Sample]): an empty array to be filled with Sample objects
        """
        try:
            pressure, temperature = MyPyBMP180.sensor_read()
            if "pressure" in self._sensors:
                samples.append(Sample("pressure", pressure, "mbar"))
            if "temperature" in self._sensors:
                samples.append(Sample("temperature", temperature, "C"))
        except MyPyBMP180.BMP180Exception as error:
            print(error.message)
