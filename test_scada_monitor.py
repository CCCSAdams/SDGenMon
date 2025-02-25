import unittest
import json
import os
import tempfile
import sqlite3
import numpy as np
from unittest.mock import patch, MagicMock
from collections import deque

# Import functions to test
from scada_monitor import initialize_database, log_alert, check_drift_conditions
from scada_data_generator import generate_sensor_data, apply_sensor_dependencies
from utils import validate_config

class TestSCADAMonitoring(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary config file for testing
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.temp_config.write(json.dumps({
            "sensors": [
                {
                    "name": "test_temp",
                    "base_value": 100,
                    "drift_rate": 0.01,
                    "spike_frequency": 0.01,
                    "spike_magnitude": 15,
                    "noise_std": 0.5,
                    "threshold": 120,
                    "missing_data_rate": 0.01
                }
            ],
            "mqtt": {
                "broker": "test.mosquitto.org",
                "port": 1883,
                "topic": "test/scada"
            },
            "email": {
                "sender_email": "test@example.com",
                "receiver_email": "test@example.com",
                "smtp_server": "smtp.example.com",
                "smtp_port": 465,
                "sender_password": "testpassword"
            }
        }))
        self.temp_config.close()
        
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
    
    def tearDown(self):
        # Clean up temporary files
        os.unlink(self.temp_config.name)
        os.unlink(self.temp_db.name)
    
    def test_validate_config(self):
        """Test configuration validation"""
        # Valid config
        with open(self.temp_config.name, 'r') as f:
            config = json.load(f)
        
        self.assertTrue(validate_config(config))
        
        # Invalid config (missing MQTT broker)
        invalid_config = config.copy()
        invalid_config['mqtt'] = {}
        self.assertFalse(validate_config(invalid_config))
    
    def test_initialize_database(self):
        """Test database initialization"""
        initialize_database(self.temp_db.name)
        
        # Check if database was created with the correct table
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'")
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'alerts')
    
    def test_log_alert(self):
        """Test logging alerts to database"""
        initialize_database(self.temp_db.name)
        log_alert("Test alert message", self.temp_db.name)
        
        # Check if alert was added to database
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT alert_message FROM alerts")
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'Test alert message')
    
    @patch('numpy.random.normal')
    @patch('random.random')
    def test_generate_sensor_data(self, mock_random, mock_normal):
        """Test sensor data generation"""
        # Mock the random functions for consistent results
        mock_normal.return_value = np.array([0.1, 0.2, -0.1, -0.2, 0.3])
        mock_random.return_value = 0.1  # Always return 0.1 (below spike_frequency)
        
        time_points = np.array([0, 0.1, 0.2, 0.3, 0.4])
        sensor_config = {
            "name": "test_sensor",
            "base_value": 100,
            "drift_rate": 0.1,
            "spike_frequency": 0.2,  # Higher than mock_random.return_value (0.1)
            "spike_magnitude": 10,
            "noise_std": 1.0,
            "threshold": 120,
            "missing_data_rate": 0.5  # Higher than mock_random.return_value (0.1)
        }
        
        data = generate_sensor_data(sensor_config, time_points)
        
        # Check the shape of the resulting data
        self.assertEqual(len(data), len(time_points))
    
    def test_check_drift_conditions(self):
        """Test drift detection"""
        # Mock the global sensor_history dictionary
        import scada_monitor
        scada_monitor.sensor_history = {}
        
        # Set up test data
        drift_conditions = {
            "test_sensor": {
                "rate_of_change": 5.0,
                "deviation_factor": 1.5,
                "window_size": 3
            }
        }
        
        # Test with normal data (no drift)
        sensor_data = {"test_sensor": 100.0}
        alerts = check_drift_conditions(sensor_data, drift_conditions)
        self.assertEqual(len(alerts), 0)
        
        # Add more values within normal range
        sensor_data = {"test_sensor": 102.0}
        alerts = check_drift_conditions(sensor_data, drift_conditions)
        self.assertEqual(len(alerts), 0)
        
        sensor_data = {"test_sensor": 104.0}
        alerts = check_drift_conditions(sensor_data, drift_conditions)
        self.assertEqual(len(alerts), 0)
        
        # Test with a large deviation (should trigger drift alert)
        sensor_data = {"test_sensor": 200.0}  # Way above average of ~102
        alerts = check_drift_conditions(sensor_data, drift_conditions)
        self.assertEqual(len(alerts), 1)
        self.assertIn("drift detected", alerts[0])
        
        # Test with a large rate of change (should trigger rate alert)
        sensor_data = {"test_sensor": 210.0}  # Change of 10 > threshold of 5
        alerts = check_drift_conditions(sensor_data, drift_conditions)
        self.assertEqual(len(alerts), 1)
        self.assertIn("rate of change", alerts[0])
    
    def test_apply_sensor_dependencies(self):
        """Test applying sensor dependencies"""
        sensor_data = {
            "temperature": np.array([100, 102, 104]),
            "pressure": np.array([10, 10.5, 11]),
            "flow_rate": np.array([50, 52, 54])
        }
        
        dependencies = {
            "pressure": {
                "depends_on": "flow_rate",
                "correlation_factor": 0.1
            }
        }
        
        result = apply_sensor_dependencies(sensor_data, dependencies)
        
        # Check if the pressure values were increased by flow_rate * correlation_factor
        expected_pressure = np.array([10, 10.5, 11]) + np.array([50, 52, 54]) * 0.1
        np.testing.assert_array_equal(result["pressure"], expected_pressure)

if __name__ == '__main__':
    unittest.main()
