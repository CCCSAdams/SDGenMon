#!/usr/bin/env python3
# Copyright (C) 2024 Carbon Capture LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

import unittest
import os
import sys
import subprocess

def run_tests():
    """Run all test suites and generate coverage report"""
    print("=== Running SCADA Monitoring System Tests ===")
    
    # Set test environment variables
    os.environ["CONFIG_PATH"] = "test_config.json"
    
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(".", pattern="test_*.py")
    
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Generate coverage report if pytest-cov is available
    try:
        print("\n=== Generating Coverage Report ===")
        subprocess.run(["pytest", "--cov=.", "--cov-report=term-missing", "test_*.py"], check=True)
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Warning: Could not generate coverage report: {e}")
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
