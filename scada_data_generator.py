# Copyright (C) 2024 Carbon Capture LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

import json
import numpy as np
import pandas as pd
import sqlite3
import os
import sys
from timesynth import TimeSampler, signals, noise
import random

# Import utility functions
from utils import load_config, validate_config

# Function to generate synthetic sensor data
def generate_sensor_data(sensor_config, time_points):
    try:
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
    except Exception as e:
        print(f"Error generating sensor data for {sensor_config.get('name', 'unknown')}: {str(e)}")
        # Return zero-filled array as fallback
        return np.zeros(len(time_points))

# Function to apply dependencies between sensors
def apply_sensor_dependencies(sensor_data, dependencies):
    try:
        for dependent, info in dependencies.items():
            base_sensor = info["depends_on"]
            factor = info["correlation_factor"]
            if base_sensor in sensor_data and dependent in sensor_data:
                sensor_data[dependent] += sensor_data[base_sensor] * factor  # Apply correlation
        return sensor_data
    except Exception as e:
        print(f"Error applying sensor dependencies: {str(e)}")
        return sensor_data

# Function to check failure conditions
def check_failures(sensor_data, failure_conditions):
    alerts = []
    try:
        for condition in failure_conditions:
            if "conditions" not in condition:
                continue
                
            name = condition["name"]
            conditions = condition["conditions"]
            alert_message = condition["alert_message"]

            # Check if all conditions match
            condition_met = True
            for sensor, criteria in conditions.items():
                if sensor not in sensor_data:
                    condition_met = False
                    break
                
                if "above" in criteria:
                    # Check if any value is above the threshold
                    above_threshold = (sensor_data[sensor] > criteria["above"]).any()
                    if not above_threshold:
                        condition_met = False
                        break

            if condition_met:
                alerts.append({"Time": sensor_data["Time"].iloc[-1], "Alert": alert_message})
    except Exception as e:
        print(f"Error checking failure conditions: {str(e)}")
    
    return alerts

# Function to save data in the requested format
def save_data(df, alerts, output_config):
    try:
        file_name = output_config["file_name"]
        output_format = output_config["format"]

        if output_format == "csv":
            df.to_csv(f"{file_name}.csv", index=False)
            print(f"Data saved to {file_name}.csv")
            
            # Save alerts to a separate CSV if there are any
            if alerts:
                pd.DataFrame(alerts).to_csv(f"{file_name}_alerts.csv", index=False)
                print(f"Alerts saved to {file_name}_alerts.csv")
                
        elif output_format == "json":
            df.to_json(f"{file_name}.json", orient="records")
            print(f"Data saved to {file_name}.json")
            
            # Save alerts to a separate JSON if there are any
            if alerts:
                pd.DataFrame(alerts).to_json(f"{file_name}_alerts.json", orient="records")
                print(f"Alerts saved to {file_name}_alerts.json")
                
        elif output_format == "database":
            conn = sqlite3.connect(f"{file_name}.db")
            df.to_sql("sensor_data", conn, if_exists="replace", index=False)
            
            if alerts:
                pd.DataFrame(alerts).to_sql("alerts", conn, if_exists="replace", index=False)
                
            conn.close()
            print(f"Data saved to {file_name}.db (SQLite)")
        else:
            print(f"Unsupported output format: {output_format}")
            return False
            
        return True
    except Exception as e:
        print(f"Error saving data: {str(e)}")
        return False

# Main function
def main(config_file="config.json"):
    # Allow override via environment variable
    config_file = os.getenv("CONFIG_PATH", config_file)
    
    try:
        # Load configuration
        config = load_config(config_file)
        
        # Validate configuration
        if not validate_config(config):
            print("Configuration validation failed. Exiting.")
            return 1

        # Time sampling
        sampling_config = config.get("sampling", {"num_points": 1000, "time_interval": 0.1})
        num_points = sampling_config["num_points"]
        time_interval = sampling_config["time_interval"]
        
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
        output_config = config.get("output", {"format": "csv", "file_name": "synthetic_scada_data"})
        if not save_data(df, alerts, output_config):
            print("Failed to save data")
            return 1
        
        return 0
    except Exception as e:
        print(f"Error in data generator: {str(e)}")
        return 1

# Run the program
if __name__ == "__main__":
    sys.exit(main())
