#!/usr/bin/env python3
"""
Debug script for the package parser.
This creates test package files and then reads them using the parser,
printing debug information along the way.
"""

import os
import struct
import sys
from package_parser import (
    ResourceKey, parse_package_file, DBPF_HEADER_MAGIC, 
    DBPF_VERSION_2, HEADER_SIZE
)

def create_test_package_v2(filename, debug=True):
    """Create a simple V2.0 test package with predictable values"""
    with open(filename, 'wb') as f:
        # Write DBPF header matching C struct layout exactly
        f.write(DBPF_HEADER_MAGIC)  # Magic 'DBPF'
        f.write(struct.pack('<I', DBPF_VERSION_2))  # Major version (32-bit)
        f.write(struct.pack('<I', 0))  # Minor version (32-bit)
        f.write(struct.pack('<I', 0))  # unknown1
        f.write(struct.pack('<I', 0))  # unknown2  
        f.write(struct.pack('<I', 0))  # unknown3
        f.write(struct.pack('<I', 0))  # dateCreated
        f.write(struct.pack('<I', 0))  # dateModified
        f.write(struct.pack('<I', 0))  # indexMajorVersion
        f.write(struct.pack('<I', 2))  # indexEntryCount
        f.write(struct.pack('<I', HEADER_SIZE))  # indexFirstEntryOffset
        f.write(struct.pack('<I', 68))  # indexSize (2 entries * 28 bytes + 4 byte type)
        f.write(struct.pack('<I', 0))  # holeEntryCount
        f.write(struct.pack('<I', 0))  # holeOffset
        f.write(struct.pack('<I', 0))  # holeSize
        f.write(struct.pack('<I', 0))  # indexMinorVersion
        f.write(struct.pack('<I', HEADER_SIZE))  # indexOffset
        f.write(struct.pack('<I', 0))  # unknown4
        f.write(b'\0' * 24)  # reserved bytes
        
        # Write index type
        f.write(struct.pack('<I', 0))
        
        # Resource 1
        type_id_1 = 0xAABBCCDD
        group_id_1 = 0x11223344
        instance_high_1 = 0x99AABBCC
        instance_low_1 = 0x55667788
        
        if debug:
            print(f"Writing Resource 1:")
            print(f"  Type ID: 0x{type_id_1:08x}")
            print(f"  Group ID: 0x{group_id_1:08x}")
            print(f"  Instance ID (high): 0x{instance_high_1:08x}")
            print(f"  Instance ID (low): 0x{instance_low_1:08x}")
            print(f"  Expected instance ID: 0x{(instance_high_1 << 32 | instance_low_1):016x}")
            
        # Write Resource 1 entry exactly matching C struct layout
        f.write(struct.pack('<IIII',
            type_id_1,        # Type ID
            group_id_1,       # Group ID
            instance_high_1,  # Instance high
            instance_low_1    # Instance low
        ))
        f.write(struct.pack('<III', 0, 0, 0))  # offset, fileSize, memSize
        f.write(struct.pack('<HH', 0, 0))  # compressed, unknown
        
        # Resource 2
        type_id_2 = 0xAABBCCDD
        group_id_2 = 0x55667788
        instance_high_2 = 0xDDEEFF00
        instance_low_2 = 0x99AABBCC
        
        if debug:
            print(f"Writing Resource 2:")
            print(f"  Type ID: 0x{type_id_2:08x}")
            print(f"  Group ID: 0x{group_id_2:08x}")
            print(f"  Instance ID (high): 0x{instance_high_2:08x}")
            print(f"  Instance ID (low): 0x{instance_low_2:08x}")
            print(f"  Expected instance ID: 0x{(instance_high_2 << 32 | instance_low_2):016x}")
            
        # Write Resource 2 entry exactly matching C struct layout
        f.write(struct.pack('<IIII',
            type_id_2,        # Type ID
            group_id_2,       # Group ID
            instance_high_2,  # Instance high
            instance_low_2    # Instance low
        ))
        f.write(struct.pack('<III', 0, 0, 0))  # offset, fileSize, memSize
        f.write(struct.pack('<HH', 0, 0))  # compressed, unknown
    
    print(f"\nCreated test package at {filename}")

def debug_parse_file(filename):
    """Parse a file with debug output"""
    print(f"\nParsing {filename}")
    try:
        resources = parse_package_file(filename)
        print(f"Found {len(resources)} resources:")
        for i, resource in enumerate(resources, 1):
            print(f"Resource {i}:")
            print(f"  Type ID: 0x{resource.type_id:08x}")
            print(f"  Group ID: 0x{resource.group_id:08x}")
            print(f"  Instance ID: 0x{resource.instance_id:016x}")
        return resources
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None

if __name__ == "__main__":
    test_file = os.path.join("tests", "test_data", "debug_test_v2.package")
    
    # Create the test package
    create_test_package_v2(test_file)
    
    # Parse it
    resources = debug_parse_file(test_file)
    
    # Check if parsing was successful
    if resources:
        print("\nVerifying results:")
        # Check for expected values
        found_res1 = False
        found_res2 = False
        
        for res in resources:
            if (res.type_id == 0xAABBCCDD and 
                res.group_id == 0x11223344 and 
                res.instance_id == (0x99AABBCC << 32 | 0x55667788)):
                found_res1 = True
            
            if (res.type_id == 0xAABBCCDD and 
                res.group_id == 0x55667788 and 
                res.instance_id == (0xDDEEFF00 << 32 | 0x99AABBCC)):
                found_res2 = True
        
        if found_res1:
            print("Resource 1: Found correctly!")
        else:
            print("Resource 1: NOT FOUND or incorrect values")
            
        if found_res2:
            print("Resource 2: Found correctly!")
        else:
            print("Resource 2: NOT FOUND or incorrect values")
            
        if not (found_res1 and found_res2):
            print("\nIMPORTANT: There appears to be an issue with the way the data is read or interpreted.")
            print("This could indicate a byte ordering issue or a problem in the parser implementation.")