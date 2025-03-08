import unittest
import os
import tempfile
import struct
import io
from unittest.mock import patch, mock_open, MagicMock
import sys
from pathlib import Path

# Add parent directory to path so we can import the module under test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from package_parser import (
    parse_package_file, ResourceKey, 
    DBPF_HEADER_MAGIC, DBPF_VERSION_2,
    RESOURCE_KEY_SIZE, RESOURCE_METADATA_SIZE
)


class ResourceKeyTests(unittest.TestCase):
    """Tests for the ResourceKey dataclass"""
    
    def test_resource_key_creation(self):
        """Test that ResourceKey objects can be created correctly"""
        key = ResourceKey(0x00B2D882, 0x00000000, 0x0123456789ABCDEF)
        self.assertEqual(key.type_id, 0x00B2D882)
        self.assertEqual(key.group_id, 0x00000000)
        self.assertEqual(key.instance_id, 0x0123456789ABCDEF)
    
    def test_resource_key_equality(self):
        """Test that ResourceKey equality works correctly"""
        key1 = ResourceKey(0x00B2D882, 0x00000000, 0x0123456789ABCDEF)
        key2 = ResourceKey(0x00B2D882, 0x00000000, 0x0123456789ABCDEF)
        key3 = ResourceKey(0x00B2D882, 0x00000001, 0x0123456789ABCDEF)  # different group_id
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)
    
    def test_resource_key_string_representation(self):
        """Test the string representation of ResourceKey"""
        key = ResourceKey(0x00B2D882, 0x00000000, 0x0123456789ABCDEF)
        expected = "T:00b2d882 G:00000000 I:0123456789abcdef"
        self.assertEqual(str(key).lower(), expected.lower())
    
    def test_resource_key_hash(self):
        """Test that ResourceKey objects can be used in sets"""
        key1 = ResourceKey(0x00B2D882, 0x00000000, 0x0123456789ABCDEF)
        key2 = ResourceKey(0x00B2D882, 0x00000000, 0x0123456789ABCDEF)
        key3 = ResourceKey(0x00B2D882, 0x00000001, 0x0123456789ABCDEF)
        
        resource_set = {key1, key2, key3}
        self.assertEqual(len(resource_set), 2)  # key1 and key2 should be treated as the same


class PackageParserTests(unittest.TestCase):
    """Tests for package file parsing functions"""
    
    def setUp(self):
        """Create test data directory if it doesn't exist"""
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_data_dir, exist_ok=True)
    
    def tearDown(self):
        """Clean up test files after tests run"""
        # Optional cleanup code
        pass

    def _create_test_package_file(self, data, filename):
        """Write test data to a file in the test data directory"""
        file_path = os.path.join(self.test_data_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(data)
        return file_path

    def test_parse_package_file_v1(self):
        """Test parsing a DBPF v1 package file"""
        # Create a mock V1 package file
        data = bytearray()
        # Header
        data.extend(DBPF_HEADER_MAGIC)  # Magic 'DBPF'
        data.extend(struct.pack('<HH', 1, 0))  # Version 1.0
        data.extend(b'\0' * (36 - len(data)))  # Skip to index count
        data.extend(struct.pack('<I', 2))  # Index count (2 entries)
        data.extend(b'\0' * (84 - len(data)))  # Skip to index table

        # Resource 1
        data.extend(struct.pack('<I', 0x00B2D882))  # Type ID
        data.extend(struct.pack('<I', 0x00000000))  # Group ID
        data.extend(struct.pack('<I', 0x12345678))  # Instance ID (low)
        data.extend(struct.pack('<I', 0x00000000))  # Instance ID (high)
        data.extend(b'\0' * RESOURCE_KEY_SIZE)  # Skip the rest

        # Resource 2
        data.extend(struct.pack('<I', 0x00B2D882))  # Type ID
        data.extend(struct.pack('<I', 0x00000001))  # Group ID
        data.extend(struct.pack('<I', 0x87654321))  # Instance ID (low)
        data.extend(struct.pack('<I', 0x00000000))  # Instance ID (high)
        data.extend(b'\0' * RESOURCE_KEY_SIZE)  # Skip the rest

        # Write the test file
        test_file = self._create_test_package_file(data, 'test_v1.package')
        
        # Parse it
        resources = parse_package_file(test_file)
        print(f"Resources found in V1 test: {resources}")
        
        # Check contents
        self.assertEqual(len(resources), 2)
        self.assertTrue(any(r.type_id == 0x00B2D882 and r.group_id == 0 for r in resources))
        self.assertTrue(any(r.type_id == 0x00B2D882 and r.group_id == 1 for r in resources))
        
    def test_parse_package_file_v2_0(self):
        """Test parsing a DBPF v2.0 package file with correctly structured data"""
        v2_0_test_file = os.path.join(self.test_data_dir, 'test_v2_0_corrected.package')
        
        try:
            # Delete existing file if it exists
            os.remove(v2_0_test_file)
        except:
            pass
            
        # Create a new test file with a specific memory layout for V2.0
        with open(v2_0_test_file, 'wb') as f:
            # Write DBPF header
            f.write(DBPF_HEADER_MAGIC)  # Magic 'DBPF'
            f.write(struct.pack('<HH', DBPF_VERSION_2, 0))  # Version 2.0
            
            # User version + flags (8 bytes)
            f.write(struct.pack('<II', 0, 0))
            
            # Unknown3 (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Date fields (8 bytes)
            f.write(struct.pack('<II', 0, 0))
            
            # Index version (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Index entry count (4 bytes)
            f.write(struct.pack('<I', 2))
            
            # Index first entry (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Index size (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Hole fields (12 bytes)
            f.write(struct.pack('<III', 0, 0, 0))
            
            # Index minor version (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Index offset (4 bytes)
            index_offset = 96  # Right after the header
            f.write(struct.pack('<I', index_offset))
            
            # Unknown4 (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Reserved bytes (24 bytes)
            f.write(b'\0' * 24)
            
            # Write index type (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Resource 1 - with the exact IDs expected in the test assertions
            type_id_1 = 0x11223344
            group_id_1 = 0xAAAA0000
            instance_high_1 = 0x99AABBCC
            instance_low_1 = 0x12345678
            
            f.write(struct.pack('<I', type_id_1))      # Type ID
            f.write(struct.pack('<I', group_id_1))     # Group ID
            f.write(struct.pack('<I', instance_high_1)) # Instance ID high
            f.write(struct.pack('<I', instance_low_1))  # Instance ID low
            f.write(struct.pack('<III', 0, 0, 0))      # Metadata
            f.write(struct.pack('<HH', 0, 0))          # Compression flags
            
            # Resource 2 - with the exact IDs expected in the test assertions
            type_id_2 = 0x11223344
            group_id_2 = 0xAAAA0001
            instance_high_2 = 0xFEDCBA09
            instance_low_2 = 0x87654321
            
            f.write(struct.pack('<I', type_id_2))      # Type ID
            f.write(struct.pack('<I', group_id_2))     # Group ID
            f.write(struct.pack('<I', instance_high_2)) # Instance ID high
            f.write(struct.pack('<I', instance_low_2))  # Instance ID low
            f.write(struct.pack('<III', 0, 0, 0))      # Metadata
            f.write(struct.pack('<HH', 0, 0))          # Compression flags
        
        # Parse the package
        resources = parse_package_file(v2_0_test_file)
        
        # Print the actual resources found for debugging
        print(f"Resources found in V2.0 corrected test: {resources}")
        
        # Check contents - we expect the same type ID (0x11223344) with two different group IDs
        type0_found = False
        type1_found = False
        
        for resource in resources:
            if resource.type_id == 0x11223344 and resource.group_id == 0xAAAA0000:
                type0_found = True
                # Confirm instance ID is correctly calculated: (high << 32) | low
                expected_instance = (0x99AABBCC << 32) | 0x12345678
                self.assertEqual(resource.instance_id, expected_instance)
            elif resource.type_id == 0x11223344 and resource.group_id == 0xAAAA0001:
                type1_found = True
                expected_instance = (0xFEDCBA09 << 32) | 0x87654321
                self.assertEqual(resource.instance_id, expected_instance)
        
        self.assertTrue(type0_found, "Resource with type=0x11223344, group=0xAAAA0000 not found")
        self.assertTrue(type1_found, "Resource with type=0x11223344, group=0xAAAA0001 not found")
        
    def test_parse_package_file_v2_1(self):
        """Test parsing a DBPF v2.1 package file with correctly structured data"""
        v2_1_test_file = os.path.join(self.test_data_dir, 'test_v2_1_corrected.package')
        
        try:
            # Delete existing file if it exists
            os.remove(v2_1_test_file)
        except:
            pass
            
        # Create a new test file with a specific memory layout for V2.1
        with open(v2_1_test_file, 'wb') as f:
            # Write DBPF header
            f.write(DBPF_HEADER_MAGIC)  # Magic 'DBPF'
            f.write(struct.pack('<HH', DBPF_VERSION_2, 1))  # Version 2.1
            
            # User version + flags (8 bytes)
            f.write(struct.pack('<II', 0, 0))
            
            # Unknown3 (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Date fields (8 bytes)
            f.write(struct.pack('<II', 0, 0))
            
            # Index version (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Index entry count (4 bytes)
            f.write(struct.pack('<I', 2))
            
            # Index first entry (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Index size (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Hole fields (12 bytes)
            f.write(struct.pack('<III', 0, 0, 0))
            
            # Index minor version (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Index offset (4 bytes)
            index_offset = 96  # Right after the header
            f.write(struct.pack('<I', index_offset))
            
            # Unknown4 (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Reserved bytes (24 bytes)
            f.write(b'\0' * 24)
            
            # Write index type (4 bytes)
            f.write(struct.pack('<I', 0))
            
            # Resource 1 - with the exact IDs expected in the test assertions
            type_id_1 = 0x55667788
            group_id_1 = 0xBBBB0000
            instance_high_1 = 0x23456789
            instance_low_1 = 0xABCDEF01
            
            f.write(struct.pack('<I', type_id_1))      # Type ID
            f.write(struct.pack('<I', group_id_1))     # Group ID
            f.write(struct.pack('<I', instance_high_1)) # Instance ID high
            f.write(struct.pack('<I', instance_low_1))  # Instance ID low
            f.write(struct.pack('<III', 0, 0, 0))      # Metadata
            f.write(struct.pack('<HH', 0, 0))          # Compression flags
            
            # Resource 2 - with the exact IDs expected in the test assertions
            type_id_2 = 0x55667788
            group_id_2 = 0xBBBB0001
            instance_high_2 = 0x76543210
            instance_low_2 = 0xFEDCBA98
            
            f.write(struct.pack('<I', type_id_2))      # Type ID
            f.write(struct.pack('<I', group_id_2))     # Group ID
            f.write(struct.pack('<I', instance_high_2)) # Instance ID high
            f.write(struct.pack('<I', instance_low_2))  # Instance ID low
            f.write(struct.pack('<III', 0, 0, 0))      # Metadata
            f.write(struct.pack('<HH', 0, 0))          # Compression flags
        
        # Parse the package
        resources = parse_package_file(v2_1_test_file)
        
        # Print the actual resources found for debugging
        print(f"Resources found in V2.1 corrected test: {resources}")
        
        # Check contents - we expect the same type ID (0x55667788) with two different group IDs
        type0_found = False
        type1_found = False
        
        for resource in resources:
            if resource.type_id == 0x55667788 and resource.group_id == 0xBBBB0000:
                type0_found = True
                # Confirm instance ID is correctly calculated: (high << 32) | low
                expected_instance = (0x23456789 << 32) | 0xABCDEF01
                self.assertEqual(resource.instance_id, expected_instance)
            elif resource.type_id == 0x55667788 and resource.group_id == 0xBBBB0001:
                type1_found = True
                expected_instance = (0x76543210 << 32) | 0xFEDCBA98
                self.assertEqual(resource.instance_id, expected_instance)
        
        self.assertTrue(type0_found, "Resource with type=0x55667788, group=0xBBBB0000 not found")
        self.assertTrue(type1_found, "Resource with type=0x55667788, group=0xBBBB0001 not found")

    def test_file_not_found(self):
        """Test handling of non-existent files"""
        with self.assertRaises(FileNotFoundError):
            parse_package_file('/non/existent/file.package')
    
    def test_invalid_extension(self):
        """Test handling of files with wrong extension"""
        # Create a temporary file with wrong extension
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            with self.assertRaises(ValueError):
                parse_package_file(tmp.name)
    
    def test_invalid_magic(self):
        """Test handling of files with invalid magic numbers"""
        # Create a file with incorrect DBPF header
        invalid_data = bytearray(b'XDBF')  # Wrong magic
        invalid_data.extend(b'\0' * 20)  # Padding
        
        test_file = self._create_test_package_file(invalid_data, 'invalid_magic.package')
        
        with self.assertRaises(ValueError) as context:
            parse_package_file(test_file)
        self.assertIn('Invalid package file format', str(context.exception))
    
    def test_malformed_package(self):
        """Test handling of malformed package files"""
        # Create a file that's too short
        invalid_data = bytearray(DBPF_HEADER_MAGIC)
        invalid_data.extend(struct.pack('<HH', DBPF_VERSION_2, 0))  # Version
        invalid_data.extend(b'\0' * 4)  # Too short, missing required data
        
        test_file = self._create_test_package_file(invalid_data, 'malformed.package')
        
        with self.assertRaises(ValueError) as context:
            parse_package_file(test_file)
        self.assertIn('Malformed package structure', str(context.exception))


class PackageParserMockTests(unittest.TestCase):
    """Tests for package file parsing using mocks"""
    
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_parse_package_with_mock_v2(self, mock_exists, mock_open):
        """Test parsing a DBPF v2 package using mocks"""
        # Mock that file exists
        mock_exists.return_value = True
        
        # Create a mock file object
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Configure the mock to return the proper data for each read request
        mock_reads = [
            DBPF_HEADER_MAGIC,               # Magic number
            struct.pack('<HH', DBPF_VERSION_2, 0),  # Version
            struct.pack('<II', 0, 0),        # User version + flags (8 bytes)
            struct.pack('<I', 0),            # Unknown3 (4 bytes)
            struct.pack('<II', 0, 0),        # Date fields (8 bytes)
            struct.pack('<I', 0),            # Index major version (4 bytes)
            struct.pack('<I', 1),            # Index entry count (4 bytes)
            struct.pack('<I', 0),            # First entry offset (4 bytes)
            struct.pack('<I', 0),            # Index size (4 bytes)
            struct.pack('<III', 0, 0, 0),    # Hole entry fields (12 bytes)
            struct.pack('<I', 0),            # Index minor version (4 bytes)
            struct.pack('<I', 96),           # Index offset (4 bytes)
            struct.pack('<I', 0),            # Index type (4 bytes)
            
            # Resource Key
            struct.pack('<I', 0x00B2D882),   # Type ID
            struct.pack('<I', 0x00000000),   # Group ID
            struct.pack('<I', 0x00000000),   # Instance high
            struct.pack('<I', 0x12345678),   # Instance low
            
            # Metadata
            struct.pack('<III', 0, 0, 0),    # Offset, fileSize, memSize (12 bytes)
            struct.pack('<HH', 0, 0),        # Compressed, unknown (4 bytes)
        ]
        
        # Set up the mock's read method to return values from mock_reads sequentially
        mock_file.read.side_effect = mock_reads
        
        # Set up the seek method to do nothing
        mock_file.seek = MagicMock()
        
        # Call function under test
        resources = parse_package_file('dummy.package')
        
        # Print the actual resources found for debugging
        print(f"Resources found in mock test: {resources}")
        
        # Expect one resource
        self.assertEqual(len(resources), 1)
        
        # Check resource properties
        resource = next(iter(resources))
        self.assertEqual(resource.type_id, 0x00B2D882)
        self.assertEqual(resource.group_id, 0)
        self.assertEqual(resource.instance_id, 0x12345678)
        
        # Ensure the file was opened with 'rb' mode
        mock_open.assert_called_once_with('dummy.package', 'rb')


if __name__ == '__main__':
    unittest.main()