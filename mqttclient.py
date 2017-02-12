import paho.mqtt.client as mqtt

class MQTTClient(object):
    """A wrapper around the paho MQTT library

    This class wraps the mqtt client of the paho library helping with the configuration,
    the connection, starting the backround loop and publishing the samples and the notification
    to the broker

    Attributes:
        _addr (str): the address of the mqtt broker
        _port (int): the port where the mqtt broker is listening for connections
        _client (paho.mqtt.client.Client): the actuall mqtt client
        _connected (bool): values telling if currently connected or not to a MQTT broker
        _base_topic (str): the base topic to use when puplishing samples or notifications
                           (could be something like "home/living_room")

    """
    def __init__(self, addr, port, auth_info=None, base_topic=""):
        """Initialize the MQTTClient

        With the received parameters this class initializes the mqtt client and starts the backgroud loop

        Args:
            addr (str): the address of the mqtt broker
            port (int): the port where the mqtt broker is listening for connections
            auth_info ({str: str}, optional): a dictionary holding the authentication parameters
                                    (keys should be "user" and "password").
            base_topic (str, optional): the base topic to use when puplishing samples or notifications
                              (could be something like "home/living_room")
        """
        self._addr = addr
        self._port = port
        self._connected = False
        self._client = mqtt.Client(client_id="", clean_session=True, userdata=None, protocol=mqtt.MQTTv311)
        if auth_info is not None:
            self._client.username_pw_set(auth_info["user"], auth_info["password"])
        self._base_topic = base_topic

    def __del__(self):
        """Clenup when class is destructed

        When class is garbage collected this method perform sum clean-up such as stopping
        the background loop and disconnecting from the broker
        """
        self.stop()

    def start(self):
        """Starts the client

        The method connects the client to the MQTT broker and starts the network loop
        """
        if not self._connected:
            self._client.connect(self._addr, port=self._port, keepalive=60, bind_address="")
            self._client.loop_start()
            self._connected = True

    def stop(self):
        """Stop the client

        The method stops the network loop and disconnects from the MQTT broker
        """
        if self._connected:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    def is_connected(self):
        """Checks if the client is currently connected to a MQTT broker

        Returns:
            bool. Returns True if currently connected to a broker, False otherwise
        """
        return self._connected


    def publish(self, topic, payload):
        """Publish a payload on a subtopic

        The method publish the payload (whatever it is) received in input on a topic composed
        as the concatenation of the base topic provided to the client at init time and the
        topic parameter received in input

        Args:
            topic (str): subtopic on which publishing the payload. For instance if the _base_topic of the
                         client wer "home/living_room" and this parameter "temperature" the final topic
                         would be "home/living_room/temperature"
            payload (str): the payload to publish
        """
        complete_topic = "{}/{}".format(self._base_topic, topic)
        self._client.publish(complete_topic, payload, qos=2)

    def publish_sample(self, sample):
        """Publish a sample object on a subtopic

        The method publish a sample object, received in input (the final topic is the concatenation of
        the base topic provided to the client at init time and the topic parameter received in input).

        Args:
            sample (Sample): the sample object to publish. The topic on which the sample is published
                             is the concatenation of the _base_topic and the label attribute of the sample
                             whereas the payload is a json string in the format {"data": float, "unit": str},
                             for example the payload of a temperature sample would be: {"data": 22.5, "unit": "C"}
        """
        payload = "{{\"data\": {data}, \"unit\": \"{unit}\"}}".format(data=sample.data, unit=sample.unit)
        self.publish(sample.label, payload)

    def publish_event(self, topic):
        """Publish an event on a topic

        The method publish an event on the subtopic provided in input (the final topic is the concatenation of
        the base topic provided to the client at init time and the topic parameter received in input).

        Args:
            topic (str): subtopic on which publishing the payload. For instance if the _base_topic of the
                         client wer "home/living_room" and this parameter "movement" the final topic
                         would be "home/living_room/movement"
        """
        topic = "{}/{}".format(self._base_topic, topic)
        self._client.publish(topic, qos=2)
