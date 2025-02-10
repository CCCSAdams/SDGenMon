# Copyright (C) 2024 Carbon Capture LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

import json
import numpy as np
import pandas as pd
import sqlite3
from timesynth import TimeSampler, signals, noise
import random

# Function to load configuration file
def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

# Function to generate synthetic sensor data
def generate_sensor_data(sensor_config, time_points):
    name = sensor_config["name"]
    base_value = sensor_config["base_value"]
    drift_rate = sensor_config["drift_rate"]
    spike_freq = sensor_config["spike_frequency"]
    spike_mag = sensor_config["spike_magnitude"]
    noise_std = sensor_config["noise_std"]
    threshold = sensor_config["threshold"]
    missing_rate = sensor_config["missing_data_rate"]

    # Generate base signal with drift
    signal = base_value + drift_rate * np.arange(len(time_points))
    
    # Add sinusoidal pattern
    sine_signal = signals.Sinusoidal(frequency=0.1, amplitude=5)
    sine_wave, _, _ = sine_signal.generate(time_points)
    signal += sine_wave

    # Add Gaussian noise
    signal += np.random.normal(0, noise_std, len(signal))

    # Inject spikes
    for i in range(len(signal)):
        if random.random() < spike_freq:
            signal[i] += spike_mag * (1 if random.random() > 0.5 else -1)

    # Inject threshold violations
    signal = np.clip(signal, None, threshold + spike_mag)

    # Inject missing/corrupted data
    for i in range(len(signal)):
        if random.random() < missing_rate:
            signal[i] = np.nan if random.random() > 0.5 else 9999  

    return signal

# Function to apply dependencies between sensors
def apply_sensor_dependencies(sensor_data, dependencies):
    for dependent, info in dependencies.items():
        base_sensor = info["depends_on"]
        factor = info["correlation_factor"]
        if base_sensor in sensor_data and dependent in sensor_data:
            sensor_data[dependent] += sensor_data[base_sensor] * factor  # Apply correlation
    return sensor_data

# Function to check failure conditions
def check_failures(sensor_data, failure_conditions):
    alerts = []
    for condition in failure_conditions:
        name = condition["name"]
        conditions = condition["conditions"]
        alert_message = condition["alert_message"]

        # Check if all conditions match
        condition_met = all(
            (sensor_data[sensor] > conditions[sensor]["above"]).any()
            if "above" in conditions[sensor] else True
            for sensor in conditions
        )

        if condition_met:
            alerts.append({"Time": sensor_data["Time"].iloc[-1], "Alert": alert_message})
    
    return alerts

# Function to save data in the requested format
def save_data(df, alerts, output_config):
    file_name = output_config["file_name"]
    output_format = output_config["format"]

    if output_format == "csv":
        df.to_csv(f"{file_name}.csv", index=False)
        print(f"Data saved to {file_name}.csv")
    elif output_format == "json":
        df.to_json(f"{file_name}.json", orient="records")
        print(f"Data saved to {file_name}.json")
    elif output_format == "database":
        conn = sqlite3.connect(f"{file_name}.db")
        df.to_sql("sensor_data", conn, if_exists="replace", index=False)
        pd.DataFrame(alerts).to_sql("alerts", conn, if_exists="replace", index=False)
        conn.close()
        print(f"Data saved to {file_name}.db (SQLite)")

# Main function
def main(config_file):
    # Load configuration
    config = load_config(config_file)

    # Time sampling
    num_points = config["sampling"]["num_points"]
    time_interval = config["sampling"]["time_interval"]
    time_sampler = TimeSampler(stop_time=num_points * time_interval)
    time_points = time_sampler.sample_regular_time(num_points=num_points)

    # Generate sensor data
    sensor_data = {"Time": time_points}
    for sensor in config["sensors"]:
        sensor_data[sensor["name"]] = generate_sensor_data(sensor, time_points)

    # Apply sensor dependencies
    sensor_data = apply_sensor_dependencies(sensor_data, config.get("sensor_dependencies", {}))

    # Convert to DataFrame
    df = pd.DataFrame(sensor_data)

    # Check for failure conditions
    alerts = check_failures(df, config.get("failure_conditions", []))

    # Save output
    save_data(df, alerts, config["output"])

# Run the program
if __name__ == "__main__":
    config_path = "config.json"  # Path to your JSON config file
    main(config_path)
