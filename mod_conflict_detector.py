#!/usr/bin/env python3
import os
import argparse
import csv
import time
from typing import Dict, List, Set, Tuple
from pathlib import Path

from package_parser import parse_package_file, ResourceKey
from scanner import scan_mods_directory


def detect_conflicts(mods_directory: str, output_file: str = None, verbose: bool = False) -> Dict[ResourceKey, List[str]]:
    """
    Main function to detect conflicts in Sims 4 mods.
    
    Args:
        mods_directory: Path to the Sims 4 Mods directory
        output_file: Path to save the conflict report (optional)
        verbose: Whether to print detailed progress
        
    Returns:
        Dictionary of conflicts found (resource keys mapping to lists of file paths)
    """
    start_time = time.time()
    
    if verbose:
        print(f"Scanning mods directory: {mods_directory}")
    
    # Scan the mods directory for package files
    package_files = scan_mods_directory(mods_directory, verbose=verbose)
    
    if verbose:
        print(f"Found {len(package_files)} package files.")
    
    # Dictionary to store resources and their containing files
    # Key: ResourceKey (type, group, instance)
    # Value: List of file paths containing the resource
    resource_map: Dict[ResourceKey, List[str]] = {}
    
    # Process each package file
    processed_count = 0
    error_count = 0
    
    for i, file_path in enumerate(package_files):
        if verbose and i % 100 == 0:
            print(f"Processing file {i+1}/{len(package_files)}: {os.path.basename(file_path)}")
        
        try:
            # Parse package file to extract resources
            resources = parse_package_file(file_path)
            processed_count += 1
            
            # Add each resource to the resource map
            for resource_key in resources:
                if resource_key not in resource_map:
                    resource_map[resource_key] = []
                resource_map[resource_key].append(file_path)
        except Exception as e:
            error_count += 1
            if verbose:
                print(f"Error processing {file_path}: {str(e)}")
    
    # Find conflicts (resources appearing in multiple files)
    conflicts = {key: paths for key, paths in resource_map.items() if len(paths) > 1}
    
    if verbose:
        print(f"Successfully processed {processed_count} files with {error_count} errors.")
        print(f"Found {len(conflicts)} potential conflicts across {len(resource_map)} unique resources.")
    
    # Generate report
    if conflicts:
        generate_report(conflicts, output_file, verbose)
    else:
        print("No conflicts detected.")
    
    elapsed_time = time.time() - start_time
    print(f"Conflict detection completed in {elapsed_time:.2f} seconds.")
    
    return conflicts


def get_relative_mod_path(file_path: str) -> str:
    """
    Convert an absolute file path to a path relative to its parent Mods directory.
    This makes the output more readable.
    
    Args:
        file_path: Absolute path to a mod file
        
    Returns:
        Path relative to the parent Mods directory
    """
    # The Mods directory is typically two levels up from the file
    # e.g., Mods/PackageName/file.package -> PackageName/file.package
    return os.path.relpath(file_path, os.path.dirname(os.path.dirname(file_path)))


def generate_report(conflicts: Dict[ResourceKey, List[str]], output_file: str = None, verbose: bool = False) -> None:
    """
    Generate a report of detected conflicts.
    
    Args:
        conflicts: Dictionary of conflicting resources
        output_file: Path to save the report (optional)
        verbose: Whether to print detailed information
    """
    # Group conflicts by files for easier reading
    file_conflicts: Dict[str, Set[str]] = {}
    
    # Build a map of which files conflict with which other files
    for resource_key, file_paths in conflicts.items():
        for file_path in file_paths:
            if file_path not in file_conflicts:
                file_conflicts[file_path] = set()
            
            # Add all conflicting files for this file
            for conflict_path in file_paths:
                if conflict_path != file_path:
                    file_conflicts[file_path].add(conflict_path)
    
    # Sort files by number of conflicts (most conflicts first)
    sorted_files = sorted(file_conflicts.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Output to console
    print(f"\nConflict Summary:")
    print(f"Found {len(conflicts)} resources with conflicts across {len(file_conflicts)} files.")
    
    if verbose:
        print("\nTop conflicts by file:")
        for file_path, conflicting_files in sorted_files[:10]:  # Show top 10
            rel_path = get_relative_mod_path(file_path)
            print(f"\n{rel_path} conflicts with {len(conflicting_files)} other files:")
            
            # Show top 5 conflicts
            for conflict in list(conflicting_files)[:5]:  
                rel_conflict = get_relative_mod_path(conflict)
                print(f"  - {rel_conflict}")
                
            if len(conflicting_files) > 5:
                print(f"  - ... and {len(conflicting_files) - 5} more files")
    
    # Write to file if specified
    if output_file:
        write_csv_report(sorted_files, output_file)
        print(f"\nDetailed conflict report saved to: {output_file}")


def write_csv_report(sorted_files: List[Tuple[str, Set[str]]], output_file: str) -> None:
    """
    Write the conflict report to a CSV file.
    
    Args:
        sorted_files: List of tuples containing (file_path, set of conflicting files)
        output_file: Path to save the report
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['File', 'Conflicts With', 'Conflict Type'])
        
        for file_path, conflicting_files in sorted_files:
            rel_path = get_relative_mod_path(file_path)
            for conflict_path in conflicting_files:
                rel_conflict = get_relative_mod_path(conflict_path)
                writer.writerow([rel_path, rel_conflict, "Resource Override"])


def main():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(
        description='Detect conflicts in Sims 4 mods.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('mods_dir', help='Path to the Sims 4 Mods directory')
    parser.add_argument('-o', '--output', help='Path to save the conflict report')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print detailed progress')
    
    args = parser.parse_args()
    
    # Run the conflict detector
    detect_conflicts(args.mods_dir, args.output, args.verbose)


if __name__ == "__main__":
    main()
