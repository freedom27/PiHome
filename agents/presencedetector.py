import json
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException
from ..common.stoppableprocess import StoppableLoopProcess
from ..common.logger import logger


def is_ip_online(ip_addr):
    """A function that checks if a certain IP is currently connected to the network

    The function leverege the NMAP service to verify if the IP received in input is currently
    connected to the network. The nmac scan process is not always super accurate and multiple
    invocation of the function might be necessary to have accurate results (NMAP infact might
    not detect something that is actually conected at its first attempt)

    Args:
        ip_addr (str): the IP address to look-up

    Returns:
        bool. It returns True if the IP is detected on the network and False if not or if an
        error occurred
    """
    nmap_process = NmapProcess(ip_addr, "-sn")
    scan_result = nmap_process.run()
    if scan_result != 0: #scan failed
        logger.error("nmap scan failed: %s", nmap_process.stderr)

    try:
        report = NmapParser.parse(nmap_process.stdout)
        host = report.hosts[0]
        if host.status == "up":
            return True
    except NmapParserException as e:
        logger.error("Exception raised while parsing scan: %s", e.msg)

    return False


class NetworkPresenceDetector(StoppableLoopProcess):
    """This class is a process that tries to detect if a list of known persons is currently connected to the network
    and publishes its findings on a Broker

    The class, which is a subclass of multiprocessing.Process, uses the tool NMAP to detect if the IP of a device
    of a known person is connected to the local network and publishes its finding (person present or absent) on a
    Broker

    Attributes:
        _persons_list ([(str, str)]): an array of tuples (name, ip_address) containing the name
                                      of the person and it smartphone's ip address
        _persons_status {str: bool}: a dictionary where the key is the name of a person and the value
                                     is a boolean that is true if the person is present and false otherwise
        _mqtt_client (MQTTClient): the broker client to use to puplish the outcome of the presence detection
        _max_detection_attempts (int): the maximum number of attempts to detect a certein ip before
                                       considering it absent
        _notify_always (bool): a boolean that states if the result of every detection attempt must be published
                               or only in case of status change
        _sampling_interval (int): the number expressing how often (in seconds) the process must perform
                                  a presence detection for all the known persons

    """

    def __init__(self, persons, mqtt_client, max_detection_attempts=7, notify_always=True, detection_frequency=10):
        """Initialize the network presence detector class

        Args:
            persons ([(str, str)]): an array of tuples (name, ip_address) containing the name
                                    of the person and it smartphone's ip address
            mqtt_client (MQTTClient): the broker client to use to puplish the outcome of the presence detection
            max_detection_attempts (int): the maximum number of attempts to detect a certein ip before
                                          considering it absent
            notify_always (bool): a boolean that states if the result of every detection attempt must be published
                                  or only in case of status change
            detection_frequency (int): the number expressing how often (in minutes) the process must perform
                                       a presence detection for all the known persons
        """
        self._persons_list = persons
        self._persons_status = {person[0]: False for person in persons}
        self._max_detection_attempts = max_detection_attempts
        self._notify_always = notify_always
        self._mqtt_client = mqtt_client
        # since the loop interval of StoppableLoopProcess is expressed in seconds and the detection_frequency
        # is in minutes I have to muliply by 60
        super(NetworkPresenceDetector, self).__init__(detection_frequency*60)

    def _notify_status(self, name, is_present):
        """Publish on the broker a persons' status

        The method takes the name and the status received in input to build a payload in the format:
        {"name": "person name", "status": "present/absent"}

        Args:
            name (str): the name of the person
            is_present (bool): a boolean that is true if the person is currently present and false otherwise
        """
        if is_present:
            status = "present"
        else:
            status = "absent"
        payload = {"name": name, "status": status}
        self._mqtt_client.publish("presence", json.dumps(payload))

    def _update_presence_status(self, name, is_present):
        """Update the status of a person within the internal register

        Args:
            name (str): the name of the person
            is_present (bool): a boolean that is true if the person is currently present and false otherwise
        """
        status_changed = is_present != self._persons_status[name]
        if status_changed:
            logger.info("%s's status changed", name)
        self._persons_status[name] = is_present
        if self._notify_always or status_changed:
            self._notify_status(name, is_present)

    def _detect_person_presence(self, person_name, ip_addr):
        """Check if a person is currently connected to the local network

        Args:
            person_name (str): the name of the person
            ip_addr (str): the ip of a device beloging to the person whose presence must be detected

        """
        logger.info("Detection of %s started using %s", person_name, ip_addr)
        attempts = 0
        presence_detected = False
        while attempts < self._max_detection_attempts:
            attempts += 1
            logger.debug("Detection attempt #%d ongoing...", attempts)
            if is_ip_online(ip_addr):
                presence_detected = True
                break
            self._wait(3)

        if presence_detected:
            logger.info("%s present", person_name)
        else:
            logger.info("%s absent", person_name)

        self._update_presence_status(person_name, presence_detected)

    def _setup(self):
        """Preparing the process to start

        The method estabilishes a connection to the broker
        """
        # starts the MQTT client
        self._mqtt_client.start()

    def _teardown(self):
        """Prepares the process for termination

        The method closes the connection with the broker
        """
        #disconnect from the mqtt broker
        self._mqtt_client.stop()


    def _loop(self):
        """Check if any known person is currently connected to the network"""
        for name, ip_addr in self._persons_list:
            self._detect_person_presence(name, ip_addr)
