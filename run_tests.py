#!/usr/bin/env python3
"""
Test runner for mod_conflict_detector
This script will run all the unit tests for the package.
"""

import unittest
import sys
import os

def run_all_tests():
    """Run all tests and return True if all tests pass, False otherwise"""
    # Find the test directory
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir)
    
    # Run tests with text test runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return True if tests succeeded
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)