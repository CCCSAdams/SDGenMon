# Copyright (C) 2024 Carbon Capture LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

import json
import sqlite3
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import paho.mqtt.client as mqtt
import threading

# Load configuration
def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Global variable to store latest sensor readings
latest_sensor_data = {}

# MQTT Callback - Updates sensor data
def on_message(client, userdata, message):
    global latest_sensor_data
    payload = json.loads(message.payload.decode("utf-8"))
    latest_sensor_data = payload  # Update global sensor data
    print(f"Updated Sensor Data: {latest_sensor_data}")

# Start MQTT Listener in a separate thread
def start_mqtt_listener(mqtt_config):
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(mqtt_config["broker"], mqtt_config["port"], 60)
    client.subscribe(mqtt_config["topic"])
    client.loop_forever()

# Read alerts from the database
def get_alerts():
    conn = sqlite3.connect("scada_alerts.db")
    df = pd.read_sql("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10", conn)
    conn.close()
    return df

# Layout of the dashboard
app.layout = dbc.Container([
    html.H1("SCADA Real-Time Dashboard", className="text-center mt-4 mb-2"),
    
    dbc.Row([
        dbc.Col([
            html.H3("Live Sensor Data"),
            html.Div(id="sensor-display", className="alert alert-primary")
        ], width=6),
        
        dbc.Col([
            html.H3("Active Alerts"),
            html.Div(id="alerts-display", className="alert alert-danger", style={"height": "300px", "overflow-y": "scroll"})
        ], width=6)
    ], className="mb-4"),

    dcc.Interval(id="update-interval", interval=2000, n_intervals=0)  # Auto-refresh every 2 sec
], fluid=True)

# Callback to update the sensor values
@app.callback(
    Output("sensor-display", "children"),
    Input("update-interval", "n_intervals")
)
def update_sensor_display(n):
    global latest_sensor_data
    if latest_sensor_data:
        return html.Ul([html.Li(f"{key}: {value}") for key, value in latest_sensor_data.items()])
    return "Waiting for sensor data..."

# Callback to update alerts
@app.callback(
    Output("alerts-display", "children"),
    Input("update-interval", "n_intervals")
)
def update_alerts(n):
    df = get_alerts()
    if df.empty:
        return "No recent alerts."
    return html.Ul([html.Li(f"{row['timestamp']} - {row['alert_message']}") for _, row in df.iterrows()])

# Run the app
if __name__ 
