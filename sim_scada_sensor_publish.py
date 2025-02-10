import paho.mqtt.client as mqtt
import json
import time
import random

broker = "mqtt.eclipseprojects.io"
topic = "scada/sensors"
client = mqtt.Client()
client.connect(broker, 1883, 60)

while True:
    sensor_data = {
        "temperature": 100 + random.uniform(-2, 5),
        "pressure": 10 + random.uniform(-1, 2)
    }
    client.publish(topic, json.dumps(sensor_data))
    print(f"Sent: {sensor_data}")
    time.sleep(2)
