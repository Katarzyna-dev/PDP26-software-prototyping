import threading
import paho.mqtt.client as mqtt


class UltrasonicSensor:

    def __init__(self, broker="localhost", topic="distance"):
        self.distance = None
        self.lock = threading.Lock()

        self.client = mqtt.Client()
        self.client.on_message = self._on_message
        self.client.connect(broker)
        self.client.subscribe(topic)

        self.thread = threading.Thread(target=self.client.loop_forever)
        self.thread.daemon = True
        self.thread.start()

    def _on_message(self, client, userdata, msg):
        value = float(msg.payload.decode())
        with self.lock:
            self.distance = value

    def get_distance(self):
        with self.lock:
            return self.distance