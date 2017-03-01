from .common import configmanager


def _get_dht_sensor():
    """Instantiate a DHTSensor

    Calls the configuration manager to get all the parameters required to instantiate
    a DHT sensor and return it

    Args:
        None

    Returns:
        DHTSensor. An instance of DHTSensor (a subclass of Sensor)
    """
    from .sensors import dhtsensor
    pin = configmanager.config.getint("dht", "gpio_pin")
    active_sensors = configmanager.config["dht"]["active_sensors"].split(",")
    model = configmanager.config["dht"]["model"]
    return dhtsensor.DHTSensor(active_sensors, model, pin)

def _get_bmp_sensor():
    """Instantiate a BMPSensor

    Calls the configuration manager to get all the parameters required to instantiate
    a BMP sensor and return it

    Args:
        None

    Returns:
        BMPSensor. An instance of BMPSensor (a subclass of Sensor)
    """
    from .sensors import bmpsensor
    active_sensors = configmanager.config["bmp"]["active_sensors"].split(",")
    return bmpsensor.BMPSensor(active_sensors)

def _get_sensors_builders():
    """Returns a dictionary to get the sensors' instantiators

    This function returns a dictionary where the keys are the name of the various sensors
    and the values are the functions instantiating the sensors.

    Args:
        None

    Returns:
        dict. A dictionary where the keys are sensors' name and the values are functions
        returning an instance of Sensor's subclasses. For example:

        {"dht": _get_dht_sensor}
    """
    sensors = {}
    sensors["dht"] = _get_dht_sensor
    sensors["bmp"] = _get_bmp_sensor
    return sensors

def _get_sensors():
    """Returns an array with all the available sensors

    The function returns an array of sensors using the configuration manager
    to determine which sensors to instantiate. The configuration manager reads
    the .ini config file to fetch the sensors list.

    Args:
        None

    Returns:
        [Sensor]. An array of Sensor's subclasses
    """
    available_sensors = _get_sensors_builders()
    sensors_list = configmanager.config["sensors"]["sensors_list"].split(",")
    return [available_sensors[sensor]() for sensor in sensors_list if sensor in available_sensors]

def _get_all_events():
    """Returns all the supported events

    The function return a dictionary of tuples where the keys are the name of the sensors
    rising the events and the values are tuples where the first element is the GPIO port
    to wich the sensor is connected and the second is the name of the event

    Args:
        None

    Returns:
        {str: (int, str)}. A dictionary where the key is the name of the sensor rising the event
        and the value is a tuple where the first element is a GPIO port number and the second
        is the name associated to the event detected on the port number.
        For example:

        {"pir": (26, "motion")} => The sensor pir (infrared motion sensor), connected to the gpio
        port 26 rises the event "motion"
    """
    events = {}
    pir_pin = configmanager.config.getint("pir", "gpio_pin")
    events["pir"] = (pir_pin, "motion")
    return events

def _get_events():
    """Returns a dictionary of the possible events

    The function uses the configuration manager to get the list of the events to monitor and returns
    a dictionary where the key is the gpio port to monitor and the value is the event name

    Args:
        None

    Returns:
        {int: str}. A dictionary where the key is the gpio port rising the event and the value
        is the event name
    """
    available_events = _get_all_events()
    event_generators = configmanager.config["sensors"]["event_generators"].split(",")
    return {available_events[generator][0] : available_events[generator][1]
            for generator in event_generators if generator in available_events}

def _get_mqtt_client():
    """Returns an instanc of MQTTClient

    The functions uses the configuration manager to get the parameters to initialize and
    then return an instance of MQTTClient

    Args:
        None

    Returns:
        MQTTClient
    """
    from .common.mqttclient import MQTTClient
    addr = configmanager.config["mqtt"]["host"]
    port = configmanager.config.getint("mqtt", "port")
    auth_info = {}
    auth_info["user"] = configmanager.config["mqtt"]["user"]
    auth_info["password"] = configmanager.config["mqtt"]["password"]
    #if user was empty let's set to None the auth_info parameter
    if not auth_info["user"]:
        auth_info = None
    base_topic = configmanager.config["mqtt"]["base_topic"]
    return MQTTClient(addr, port, auth_info, base_topic)

def get_sensors_manager():
    """Returns an instance of SensorsManager

    The function uses the configuration manager to get all the info required to be able to instantiate
    the SensorsManager and return it

    Args:
        None

    Returns:
        SensorsManager
    """
    from .agents.sensorsmanager import SensorsManager
    sensors = _get_sensors()
    events = _get_events()
    mqtt_client = _get_mqtt_client()
    return SensorsManager(sensors, events, mqtt_client)

def get_presence_detector():
    """Return an instance of NetworkPresenceDetector

    The function uses the configuration manager to get all the knowkn ips to monitor and the MQTT broker info
    to be able to instantiate the NetworkPresenceDetector and return it

    Args:
        None

    Returns:
        NetworkPresenceDetector
    """
    from .agents.presencedetector import NetworkPresenceDetector
    mqtt_client = _get_mqtt_client()
    persons = [(known_ip[0], known_ip[1]) for known_ip in configmanager.config["network_presence_detector"]["known_ips"].split(",")]
    return NetworkPresenceDetector(persons, mqtt_client)
