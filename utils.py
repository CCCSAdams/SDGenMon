# Copyright (C) 2024 Carbon Capture LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

import json
import os
import time
import sqlite3
import paho.mqtt.client as mqtt

def load_config(config_file):
    """Load configuration from file and override with environment variables"""
    try:
        # Allow override via environment variable
        config_file = os.getenv("CONFIG_PATH", config_file)
        
        # Load base config from file
        with open(config_file, 'r') as file:
            config = json.load(file)
        
        # Override with environment variables
        if 'email' in config:
            config['email']['sender_email'] = os.getenv('SMTP_EMAIL', config['email']['sender_email'])
            config['email']['sender_password'] = os.getenv('SMTP_PASSWORD', config['email']['sender_password'])
            config['email']['smtp_server'] = os.getenv('SMTP_SERVER', config['email']['smtp_server'])
            config['email']['smtp_port'] = int(os.getenv('SMTP_PORT', str(config['email']['smtp_port'])))
        
        if 'mqtt' in config:
            config['mqtt']['broker'] = os.getenv('MQTT_BROKER', config['mqtt']['broker'])
            config['mqtt']['port'] = int(os.getenv('MQTT_PORT', str(config['mqtt']['port'])))
            config['mqtt']['username'] = os.getenv('MQTT_USERNAME', config['mqtt'].get('username', ''))
            config['mqtt']['password'] = os.getenv('MQTT_PASSWORD', config['mqtt'].get('password', ''))
            
        return config
    except FileNotFoundError:
        print(f"ERROR: Configuration file '{config_file}' not found")
        return {}
    except json.JSONDecodeError:
        print(f"ERROR: Configuration file '{config_file}' is not valid JSON")
        return {}

def validate_config(config):
    """Validate configuration structure and values"""
    errors = []
    
    # Validate sensors configuration
    if 'sensors' not in config:
        errors.append("Missing 'sensors' section in configuration")
    else:
        for i, sensor in enumerate(config['sensors']):
            if 'name' not in sensor:
                errors.append(f"Sensor at index {i} is missing 'name'")
    
    # Validate MQTT configuration
    if 'mqtt' not in config:
        errors.append("Missing 'mqtt' section in configuration")
    else:
        mqtt = config['mqtt']
        if 'broker' not in mqtt:
            errors.append("Missing 'broker' in MQTT configuration")
        if 'port' not in mqtt:
            errors.append("Missing 'port' in MQTT configuration")
        if 'topic' not in mqtt:
            errors.append("Missing 'topic' in MQTT configuration")
    
    # Validate email configuration
    if 'email' in config:
        email = config['email']
        for field in ['sender_email', 'receiver_email', 'smtp_server', 'smtp_port']:
            if field not in email:
                errors.append(f"Missing '{field}' in email configuration")
    
    # Report all errors
    if errors:
        for error in errors:
            print(f"CONFIG ERROR: {error}")
        return False
    
    return True

def connect_mqtt_with_retry(mqtt_config, max_retries=5, retry_delay=5):
    """Connect to MQTT broker with retry logic"""
    client = mqtt.Client()
    
    # Set up authentication if configured
    if 'username' in mqtt_config and mqtt_config['username']:
        client.username_pw_set(mqtt_config['username'], mqtt_config['password'])
    
    retries = 0
    while retries < max_retries:
        try:
            print(f"Connecting to MQTT broker {mqtt_config['broker']}:{mqtt_config['port']}...")
            client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
            print("MQTT connection successful")
            return client
        except Exception as e:
            retries += 1
            print(f"MQTT connection failed: {str(e)}")
            if retries < max_retries:
                print(f"Retrying in {retry_delay} seconds... ({retries}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print("Maximum retry attempts reached")
    
    raise ConnectionError(f"Failed to connect to MQTT broker after {max_retries} attempts")

def db_execute_with_retry(db_name, query, params=(), max_retries=3, retry_delay=1):
    """Execute a database query with retry logic"""
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            last_error = e
            retries += 1
            print(f"Database error: {str(e)}")
            if retries < max_retries:
                print(f"Retrying in {retry_delay} seconds... ({retries}/{max_retries})")
                time.sleep(retry_delay)
    
    print(f"Failed to execute query after {max_retries} attempts: {last_error}")
    return False
