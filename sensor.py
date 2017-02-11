from abc import ABCMeta, abstractmethod


class Sensor(metaclass=ABCMeta):
    """Base sensor class

    Any sensor class must inherit from this one and implement the abstract method
    _fetch_data to be able to sample
    """

    @abstractmethod
    def _fetch_data(self, samples):
        """Abstract method to implement to have a proper sampling process

        Args:
            samples ([Sample]): an empty array to be filled with Sample objects
        """
        pass

    def sample(self):
        """Gather data from the sensor and return it

        Returns:
            [Sample]. An array of Sample objects containing the data sampled from the sensor
        """
        samples = []
        self._fetch_data(samples)
        return samples


class Sample(object):
    """A Sample object
    An object containing the data sampled by the sensor
    """
    def __init__(self, label, data, unit):
        """Initialiaze a Sample

        Args:
            label (str): a label describing the type of data (something like "temperature" or "pressure")
            data (float): a number describing the data sampled
            unit (str): the unit measure of the data (for temperature could be "C" whereas for pressure "mbar")
        """
        self.label = label
        self.data = data
        self.unit = unit
