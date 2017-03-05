class EventManager(object):

    def __init__(self, broker_client, topics_and_actions):
        self._broker_client = broker_client
        self._topics_and_actions = topics_and_actions
        self._listening = False

    def __del__(self):
        self.stop_listening()

    def start_listening(self):
        if not self._listening:
            self._broker_client.start()
            for topic, action in self._topics_and_actions:
                self._broker_client.register(topic, action)
            self._listening = True

    def stop_listening(self):
        if self._listening:
            for topic, _ in self._topics_and_actions:
                self._broker_client.unregister(topic)
            self._broker_client.stop()
            self._listening = False

    def is_listening(self):
        return self._listening
