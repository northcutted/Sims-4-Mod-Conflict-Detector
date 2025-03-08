import os
from typing import List, Optional
from pathlib import Path


def scan_mods_directory(directory: str, verbose: bool = False, 
                        include_script_mods: bool = False) -> List[str]:
    """
    Recursively scan the provided directory for Sims 4 package files.
    
    Args:
        directory: Path to the directory to scan
        verbose: Whether to print detailed progress
        include_script_mods: Whether to include .ts4script files (currently unsupported)
        
    Returns:
        List of absolute paths to package files
        
    Raises:
        NotADirectoryError: If the provided path is not a valid directory
        PermissionError: If there are permission issues accessing the directory
    """
    directory_path = Path(directory)
    
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Invalid directory: {directory}")
    
    if verbose:
        print(f"Scanning directory: {directory}")
    
    package_files: List[str] = []
    script_files: List[str] = []
    skipped_dirs: List[str] = []
    
    try:
        # Walk through the directory tree
        for root, dirs, files in os.walk(directory):
            # Process each file in the current directory
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if the file is a package file
                if file.lower().endswith('.package'):
                    package_files.append(file_path)
                # Handle script mods if requested
                elif include_script_mods and file.lower().endswith('.ts4script'):
                    script_files.append(file_path)
            
            # Skip specific directories if needed
            # For example, if we wanted to skip certain directories:
            # dirs[:] = [d for d in dirs if d.lower() not in ["backup", "_backup"]]
    
    except PermissionError as e:
        if verbose:
            print(f"Permission error: {e}")
        raise
    except Exception as e:
        if verbose:
            print(f"Error scanning directory: {e}")
        raise
    
    if verbose:
        print(f"Found {len(package_files)} package files")
        if include_script_mods:
            print(f"Found {len(script_files)} script mod files")
            if script_files:
                print("Note: Script mod analysis is not yet supported")
    
    # Currently, we only return package files
    # In the future, we could return both types
    return package_files
