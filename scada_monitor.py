# Copyright (C) 2024 Carbon Capture LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

import json
import time
import sqlite3
import paho.mqtt.client as mqtt
import smtplib
import ssl
import pandas as pd
from collections import deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys

# Import utility functions
from utils import load_config, validate_config, connect_mqtt_with_retry, db_execute_with_retry

# Initialize database
def initialize_database(db_name="scada_alerts.db"):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                alert_message TEXT
            )
        """)
        conn.commit()
        conn.close()
        print(f"Database {db_name} initialized successfully")
    except sqlite3.Error as e:
        print(f"Error initializing database: {str(e)}")
        return False
    return True

# Log alerts to the database
def log_alert(alert_message, db_name="scada_alerts.db"):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    query = "INSERT INTO alerts (timestamp, alert_message) VALUES (?, ?)"
    if db_execute_with_retry(db_name, query, (timestamp, alert_message)):
        print(f"ALERT LOGGED: {alert_message}")
        return True
    return False

# Send email notifications
def send_email_alert(alert_message, email_config):
    sender_email = email_config["sender_email"]
    receiver_email = email_config["receiver_email"]
    smtp_server = email_config["smtp_server"]
    smtp_port = email_config["smtp_port"]
    sender_password = email_config["sender_password"]

    subject = "SCADA ALERT: Sensor Issue Detected"
    body = f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\nAlert: {alert_message}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"EMAIL SENT: {alert_message}")
        return True
    except Exception as e:
        print(f"EMAIL FAILED: {str(e)}")
        return False

# Track historical sensor data for drift detection
sensor_history = {}

# Check for drift conditions
def check_drift_conditions(sensor_data, drift_conditions):
    global sensor_history
    alerts = []

    for sensor, conditions in drift_conditions.items():
        value = sensor_data.get(sensor, None)
        if value is None:
            continue

        # Initialize rolling history
        if sensor not in sensor_history:
            sensor_history[sensor] = deque(maxlen=conditions["window_size"])

        # Add new value to history
        sensor_history[sensor].append(value)

        if len(sensor_history[sensor]) < conditions["window_size"]:
            continue  # Not enough data to evaluate drift

        # Compute rolling average
        rolling_avg = sum(sensor_history[sensor]) / len(sensor_history[sensor])

        # Check for deviation
        if abs(value) > conditions["deviation_factor"] * rolling_avg:
            alerts.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - WARNING: {sensor} sensor drift detected! (Value: {value}, Avg: {rolling_avg})")

        # Check for abnormal rate of change
        if len(sensor_history[sensor]) > 1:
            rate_of_change = abs(sensor_history[sensor][-1] - sensor_history[sensor][-2])
            if rate_of_change > conditions["rate_of_change"]:
                alerts.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - WARNING: {sensor} abnormal rate of change detected! (Rate: {rate_of_change})")

    return alerts

# Store sensor data in database
def store_sensor_data(sensor_data, db_name="sensor_data.db"):
    try:
        # Add timestamp
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        data_with_timestamp = {"timestamp": timestamp, **sensor_data}
        
        # Connect to database
        conn = sqlite3.connect(db_name)
        
        # Create table if it doesn't exist
        cursor = conn.cursor()
        columns = ["timestamp TEXT"] + [f"{key} REAL" for key in sensor_data.keys()]
        create_table_sql = f"CREATE TABLE IF NOT EXISTS sensor_data (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(columns)})"
        cursor.execute(create_table_sql)
        
        # Insert data
        columns = list(data_with_timestamp.keys())
        placeholders = ", ".join(["?"] * len(columns))
        values = [data_with_timestamp[col] for col in columns]
        
        insert_sql = f"INSERT INTO sensor_data ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(insert_sql, values)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error storing sensor data: {str(e)}")
        return False

# MQTT Callback Function
def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        print(f"Received Data: {payload}")
        
        # Store sensor data in database
        store_sensor_data(payload)
        
        # Check for drift conditions
        drift_alerts = check_drift_conditions(payload, userdata["drift_conditions"])
        for alert in drift_alerts:
            log_alert(alert)
            if userdata.get("email_config"):
                send_email_alert(alert, userdata["email_config"])
    except Exception as e:
        print(f"Error processing message: {str(e)}")

# Main real-time monitoring function
def main(config_file="config.json"):
    try:
        # Load configuration
        config = load_config(config_file)
        
        # Validate configuration
        if not validate_config(config):
            print("Configuration validation failed. Exiting.")
            return 1
        
        drift_conditions = {}
        # Extract drift conditions from failure conditions
        for failure in config.get("failure_conditions", []):
            if "drift_conditions" in failure:
                drift_conditions = failure["drift_conditions"]
                break
        
        mqtt_config = config.get("mqtt", {})
        email_config = config.get("email", {})

        # Initialize database
        if not initialize_database():
            print("Failed to initialize database. Exiting.")
            return 1

        # MQTT Setup
        try:
            client = connect_mqtt_with_retry(mqtt_config)
            client.user_data_set({"drift_conditions": drift_conditions, "email_config": email_config})
            client.on_message = on_message

            client.subscribe(mqtt_config["topic"])
            print(f"Subscribed to MQTT topic: {mqtt_config['topic']}")

            # Start MQTT loop
            client.loop_forever()
        except KeyboardInterrupt:
            print("MQTT monitoring stopped by user")
            return 0
        except Exception as e:
            print(f"MQTT error: {str(e)}")
            return 1
            
    except Exception as e:
        print(f"Error in main function: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
