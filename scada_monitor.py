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

# Load configuration
def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

# Initialize database
def initialize_database(db_name="scada_alerts.db"):
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

# Log alerts to the database
def log_alert(alert_message, db_name="scada_alerts.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO alerts (timestamp, alert_message) VALUES (?, ?)", (timestamp, alert_message))
    conn.commit()
    conn.close()
    print(f"ALERT LOGGED: {alert_message}")

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
    except Exception as e:
        print(f"EMAIL FAILED: {str(e)}")

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

# MQTT Callback Function
def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode("utf-8"))
    print(f"Received Data: {payload}")

    # Check for drift conditions
    drift_alerts = check_drift_conditions(payload, userdata["drift_conditions"])
    for alert in drift_alerts:
        log_alert(alert)
        send_email_alert(alert, userdata["email_config"])

# Main real-time monitoring function
def main(config_file):
    config = load_config(config_file)
    drift_conditions = config.get("failure_conditions", [])[1].get("drift_conditions", {})
    mqtt_config = config.get("mqtt", {})
    email_config = config.get("email", {})

    # Initialize database
    initialize_database()

    # MQTT Setup
    client = mqtt.Client()
    client.user_data_set({"drift_conditions": drift_conditions, "email_config": email_config})
    client.on_message = on_message

    client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
    client.subscribe(mqtt_config["topic"])
    print(f"Subscribed to MQTT topic: {mqtt_config['topic']}")

    # Start MQTT loop
    client.loop_forever()

if __name__ == "__main__":
    config_path = "config.json"
    main(config_path)

