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
import os
import sys

# Import utility functions
from utils import load_config, validate_config, connect_mqtt_with_retry, db_execute_with_retry

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Global variable to store latest sensor readings
latest_sensor_data = {}

# MQTT Callback - Updates sensor data
def on_message(client, userdata, message):
    try:
        global latest_sensor_data
        payload = json.loads(message.payload.decode("utf-8"))
        latest_sensor_data = payload  # Update global sensor data
        print(f"Updated Sensor Data: {payload}")
    except Exception as e:
        print(f"Error processing MQTT message: {str(e)}")

# Start MQTT Listener in a separate thread
def start_mqtt_listener(mqtt_config):
    try:
        client = connect_mqtt_with_retry(mqtt_config)
        client.on_message = on_message
        client.subscribe(mqtt_config["topic"])
        print(f"Subscribed to MQTT topic: {mqtt_config['topic']}")
        client.loop_forever()
    except Exception as e:
        print(f"MQTT listener error: {str(e)}")

# Read alerts from the database
def get_alerts(db_path="scada_alerts.db"):
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10", conn)
        conn.close()
        return df
    except sqlite3.Error as e:
        print(f"Database error when reading alerts: {str(e)}")
        return pd.DataFrame(columns=["timestamp", "alert_message"])

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

    dbc.Row([
        dbc.Col([
            html.H3("Sensor Values Over Time"),
            dcc.Graph(id='sensor-graph'),
            dcc.Interval(id='graph-update', interval=5000, n_intervals=0)
        ], width=12)
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

# Callback to update sensor graph
@app.callback(
    Output('sensor-graph', 'figure'),
    Input('graph-update', 'n_intervals')
)
def update_graph(n):
    try:
        # Read sensor data from database
        conn = sqlite3.connect("sensor_data.db")
        df = pd.read_sql("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()
        
        if df.empty:
            # Return empty figure if no data
            return {
                'data': [],
                'layout': {
                    'title': 'No sensor data available'
                }
            }
        
        # Prepare data for plotting
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Create traces for each sensor
        traces = []
        for column in df.columns:
            if column != 'timestamp' and column != 'id':
                traces.append({
                    'x': df['timestamp'],
                    'y': df[column],
                    'name': column,
                    'mode': 'lines+markers'
                })
        
        return {
            'data': traces,
            'layout': {
                'title': 'Sensor Values Over Time',
                'xaxis': {'title': 'Time'},
                'yaxis': {'title': 'Value'}
            }
        }
    except Exception as e:
        print(f"Error updating graph: {str(e)}")
        return {
            'data': [],
            'layout': {
                'title': 'Error loading sensor data'
            }
        }

# Run the app
if __name__ == "__main__":
    try:
        # Load configuration
        config = load_config("config.json")
        
        # Validate configuration
        if not validate_config(config):
            print("Configuration validation failed. Exiting.")
            sys.exit(1)
        
        # Start MQTT listener in a separate thread
        mqtt_thread = threading.Thread(
            target=start_mqtt_listener, 
            args=(config.get("mqtt", {}),),
            daemon=True
        )
        mqtt_thread.start()
        
        # Run Dash app
        app.run_server(debug=True, host='0.0.0.0', port=8050)
    except Exception as e:
        print(f"Error starting dashboard: {str(e)}")
        sys.exit(1)
