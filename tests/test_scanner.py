import unittest
import os
import sys
import tempfile
from unittest.mock import patch, Mock
from pathlib import Path

# Add parent directory to path so we can import the module under test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scanner import scan_mods_directory


class ScannerTests(unittest.TestCase):
    """Tests for the mod directory scanner functions"""
    
    def setUp(self):
        """Set up test data directory"""
        self.test_data_dir = tempfile.TemporaryDirectory()
        self.test_dir_path = self.test_data_dir.name
        
    def tearDown(self):
        """Clean up after tests"""
        self.test_data_dir.cleanup()
        
    def _create_test_file(self, rel_path, content=b''):
        """Create a test file in the temporary directory"""
        file_path = os.path.join(self.test_dir_path, rel_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    
    def test_scan_empty_directory(self):
        """Test scanning an empty directory"""
        # Directory exists but is empty
        result = scan_mods_directory(self.test_dir_path)
        self.assertEqual(len(result), 0)
        
    def test_scan_with_package_files(self):
        """Test scanning a directory with package files"""
        # Create mock package files
        self._create_test_file('file1.package')
        self._create_test_file('subfolder/file2.package')
        self._create_test_file('subfolder/nested/file3.package')
        self._create_test_file('not_a_package.txt')
        
        # Scan the directory
        result = scan_mods_directory(self.test_dir_path)
        
        # Check that only package files were found
        self.assertEqual(len(result), 3)
        self.assertTrue(any(p.endswith('file1.package') for p in result))
        self.assertTrue(any(p.endswith('file2.package') for p in result))
        self.assertTrue(any(p.endswith('file3.package') for p in result))
        
    def test_scan_include_script_mods(self):
        """Test scanning with script mods included"""
        # Create mock package and script files
        self._create_test_file('file1.package')
        self._create_test_file('script1.ts4script')
        
        # Scan with script mods enabled
        result = scan_mods_directory(self.test_dir_path, include_script_mods=True)
        
        # Only package files should be returned (script mods not supported yet)
        self.assertEqual(len(result), 1)
        self.assertTrue(any(p.endswith('file1.package') for p in result))
        
    def test_directory_not_found(self):
        """Test handling of non-existent directory"""
        with self.assertRaises(NotADirectoryError):
            scan_mods_directory('/this/directory/does/not/exist')
    
    def test_not_a_directory(self):
        """Test handling when path is not a directory"""
        # Create a file
        file_path = self._create_test_file('testfile.txt')
        
        # Try to scan it as a directory
        with self.assertRaises(NotADirectoryError):
            scan_mods_directory(file_path)
    
    @patch('os.walk')
    def test_permission_error(self, mock_walk):
        """Test handling of permission errors"""
        # Mock os.walk to raise a PermissionError
        mock_walk.side_effect = PermissionError("Access denied")
        
        with self.assertRaises(PermissionError):
            scan_mods_directory(self.test_dir_path, verbose=True)
    
    @patch('os.walk')
    def test_general_exception(self, mock_walk):
        """Test handling of general errors"""
        # Mock os.walk to raise a generic exception
        mock_walk.side_effect = Exception("Unexpected error")
        
        with self.assertRaises(Exception):
            scan_mods_directory(self.test_dir_path)
    
    @patch('os.walk')
    def test_verbose_output(self, mock_walk):
        """Test that verbose output doesn't affect functionality"""
        # Set up mock to return test data
        mock_walk.return_value = [
            (self.test_dir_path, [], ['file1.package', 'file2.txt'])
        ]
        
        # Scan with verbose output
        result = scan_mods_directory(self.test_dir_path, verbose=True)
        
        # Should return one package file
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].endswith('file1.package'))


if __name__ == '__main__':
    unittest.main()