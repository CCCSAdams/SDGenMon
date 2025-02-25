#!/usr/bin/env python3
# Copyright (C) 2024 Carbon Capture LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

import os
import sys
import time
import signal
import subprocess
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global variables to track processes
processes = []

def signal_handler(sig, frame):
    """Handle interrupt signals to gracefully stop all processes"""
    print("\nShutting down all processes...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            process.terminate()
    
    # Wait for all processes to terminate
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    
    print("All processes stopped.")
    sys.exit(0)

def start_process(name, command):
    """Start a process and add it to the global tracking list"""
    print(f"Starting {name}...")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    processes.append(process)
    return process

def monitor_output(process, prefix):
    """Non-blocking monitoring of process output with prefix"""
    line = process.stdout.readline()
    if line:
        print(f"[{prefix}] {line.strip()}")
    return bool(line)

def check_processes():
    """Check if any processes have stopped unexpectedly"""
    for i, process in enumerate(processes):
        if process.poll() is not None:
            print(f"Process {i+1} exited with code {process.returncode}")
            return False
    return True

def main():
    """Main function to run the complete SCADA monitoring system"""
    parser = argparse.ArgumentParser(description="Run the SCADA monitoring system")
    parser.add_argument('--generate-data', action='store_true', help='Generate synthetic data')
    parser.add_argument('--simulate-sensors', action='store_true', help='Simulate sensor publishing')
    parser.add_argument('--monitor', action='store_true', help='Run the SCADA monitor')
    parser.add_argument('--dashboard', action='store_true', help='Run the dashboard')
    parser.add_argument('--all', action='store_true', help='Run all components')
    
    args = parser.parse_args()
    
    # Default to --all if no args specified
    if not any(vars(args).values()):
        args.all = True
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start requested components
        if args.all or args.generate_data:
            data_gen = start_process("Data Generator", [sys.executable, "scada_data_generator.py"])
        
        if args.all or args.simulate_sensors:
            # Wait a moment to ensure data is generated
            if args.all or args.generate_data:
                time.sleep(2)
            
            sensor_pub = start_process("Sensor Publisher", [sys.executable, "sim_scada_sensor_publish.py"])
        
        if args.all or args.monitor:
            monitor = start_process("SCADA Monitor", [sys.executable, "scada_monitor.py"])
        
        if args.all or args.dashboard:
            dashboard = start_process("Dashboard", [sys.executable, "scada_dashboard.py"])
            print(f"Dashboard running at http://localhost:{os.getenv('DASH_PORT', '8050')}")
        
        # Monitor outputs and process health
        print("All processes started. Press Ctrl+C to exit.")
        while check_processes():
            for i, process in enumerate(processes):
                if process.poll() is None:  # If process is still running
                    monitor_output(process, f"Process {i+1}")
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        signal_handler(None, None)  # Stop all processes on exception
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
