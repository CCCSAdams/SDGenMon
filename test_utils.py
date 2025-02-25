import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import sqlite3

from utils import load_config, validate_config, db_execute_with_retry

class TestUtils(unittest.TestCase):
    
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
    
    def test_load_config(self):
        """Test loading configuration from file"""
        config = load_config(self.temp_config.name)
        
        # Check if the config was loaded correctly
        self.assertIn("sensors", config)
        self.assertIn("mqtt", config)
        self.assertIn("email", config)
        
        # Check if it has the required fields
        self.assertEqual(config["mqtt"]["broker"], "test.mosquitto.org")
        self.assertEqual(config["mqtt"]["port"], 1883)
    
    @patch.dict('os.environ', {
        'MQTT_BROKER': 'env.mosquitto.org',
        'SMTP_PASSWORD': 'env_password'
    })
    def test_load_config_with_env_vars(self):
        """Test loading configuration with environment variables"""
        config = load_config(self.temp_config.name)
        
        # Check if environment variables override the config file
        self.assertEqual(config["mqtt"]["broker"], "env.mosquitto.org")
        self.assertEqual(config["email"]["sender_password"], "env_password")
    
    def test_validate_config_valid(self):
        """Test validating a valid configuration"""
        with open(self.temp_config.name, 'r') as f:
            config = json.load(f)
        
        self.assertTrue(validate_config(config))
    
    def test_validate_config_invalid(self):
        """Test validating an invalid configuration"""
        # Test missing sensors
        invalid_config = {"mqtt": {"broker": "test", "port": 1883, "topic": "test"}}
        self.assertFalse(validate_config(invalid_config))
        
        # Test missing MQTT
        invalid_config = {"sensors": [{"name": "test"}]}
        self.assertFalse(validate_config(invalid_config))
        
        # Test incomplete MQTT config
        invalid_config = {
            "sensors": [{"name": "test"}],
            "mqtt": {"broker": "test"}
        }
        self.assertFalse(validate_config(invalid_config))
    
    def test_db_execute_with_retry_success(self):
        """Test database execution with retry - success case"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        conn.commit()
        conn.close()
        
        # This should succeed
        result = db_execute_with_retry(
            self.temp_db.name, 
            "INSERT INTO test (value) VALUES (?)", 
            ("test value",)
        )
        
        # Check if execution was successful
        self.assertTrue(result)
        
        # Verify the data was inserted
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM test")
        data = cursor.fetchone()
        conn.close()
        
        self.assertEqual(data[0], "test value")
    
    def test_db_execute_with_retry_failure(self):
        """Test database execution with retry - failure case"""
        # This should fail (table doesn't exist)
        result = db_execute_with_retry(
            self.temp_db.name, 
            "INSERT INTO nonexistent_table (value) VALUES (?)", 
            ("test value",),
            max_retries=2,
            retry_delay=0.1
        )
        
        # Check if execution failed
        self.assertFalse(result)
    
    @patch('sqlite3.connect')
    def test_db_execute_with_retry_multiple_attempts(self, mock_connect):
        """Test database execution with multiple retry attempts"""
        # Mock the sqlite3.connect to fail the first time, then succeed
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # First call raises an exception, second call succeeds
        mock_connect.side_effect = [
            sqlite3.Error("Test error"),
            mock_conn
        ]
        
        result = db_execute_with_retry(
            "test.db", 
            "INSERT INTO test (value) VALUES (?)", 
            ("test value",),
            max_retries=2,
            retry_delay=0.1
        )
        
        # Check if execution was successful after retry
        self.assertTrue(result)
        
        # Check that connect was called twice
        self.assertEqual(mock_connect.call_count, 2)
        
        # Check that execute was called once (on the second connection)
        mock_cursor.execute.assert_called_once()

if __name__ == '__main__':
    unittest.main()
