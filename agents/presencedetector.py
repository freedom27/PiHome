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

    def __init__(self, persons, mqtt_client, max_detection_attempts=7, notify_always=True, detection_frequency=10):
        """Initialize the network presence detector class

        Args:
            persons ([(str, str)]): an array of tuples (name, ip_address) containing the name
                                    of the person and it smartphone's ip address
            max_detection_attempts (int): the maximum number of attempts to detect a certein ip before
                                          considering it absent
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
        if is_present:
            status = "present"
        else:
            status = "absent"
        payload = {"name": name, "status": status}
        self._mqtt_client.publish("presence", json.dumps(payload))

    def _update_presence_status(self, name, is_present):
        status_changed = is_present != self._persons_status[name]
        if status_changed:
            logger.info("%s's status changed", name)
        self._persons_status[name] = is_present
        if self._notify_always or status_changed:
            self._notify_status(name, is_present)

    def _detect_person_presence(self, person_name, ip_addr):
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
        # starts the MQTT client
        self._mqtt_client.start()

    def _teardown(self):
        #disconnect from the mqtt broker
        self._mqtt_client.stop()


    def _loop(self):
        for name, ip_addr in self._persons_list:
            self._detect_person_presence(name, ip_addr)
