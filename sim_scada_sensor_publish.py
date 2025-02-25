# Copyright (C) 2024 Carbon Capture LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

import paho.mqtt.client as mqtt
import json
import time
import random
import os
import sys

# Import utility functions
from utils import load_config, validate_config, connect_mqtt_with_retry

def main(config_file="config.json"):
    try:
        # Load configuration
        config = load_config(config_file)
        
        # Validate configuration
        if not validate_config(config):
            print("Configuration validation failed. Exiting.")
            return 1
        
        mqtt_config = config.get("mqtt", {})
        
        # Connect to MQTT broker
        client = connect_mqtt_with_retry(mqtt_config)
        
        # Get topic from config
        topic = mqtt_config.get("topic", "scada/sensors")
        print(f"Publishing to topic: {topic}")
        
        # Get sensors from config
        sensors = config.get("sensors", [
            {"name": "temperature", "base_value": 100},
            {"name": "pressure", "base_value": 10}
        ])
        
        # Create a map of sensor names to their base values
        sensor_map = {sensor["name"]: sensor["base_value"] for sensor in sensors}
        
        # Main publishing loop
        try:
            while True:
                sensor_data = {}
                for name, base_value in sensor_map.items():
                    # Generate random value around base_value
                    value = base_value + random.uniform(-base_value * 0.05, base_value * 0.05)
                    sensor_data[name] = round(value, 2)
                
                # Publish data
                client.publish(topic, json.dumps(sensor_data))
                print(f"Published: {sensor_data}")
                
                # Wait before next update
                time.sleep(2)
        except KeyboardInterrupt:
            print("Publisher stopped by user")
            return 0
            
    except Exception as e:
        print(f"Error in publisher: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
