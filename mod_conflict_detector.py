#!/usr/bin/env python3
import os
import argparse
import csv
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys
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


class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string)
        self.text_widget.configure(state=tk.DISABLED)
        self.text_widget.see(tk.END)

    def flush(self):
        pass


class ModConflictDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sims 4 Mod Conflict Detector")
        self.root.geometry("800x600")
        
        # Create frame for inputs
        input_frame = ttk.Frame(root, padding="10")
        input_frame.pack(fill=tk.X)
        
        # Mods directory selection
        ttk.Label(input_frame, text="Mods Directory:").grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        self.mods_dir_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.mods_dir_var, width=50).grid(column=1, row=0, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse...", command=self.browse_mods_dir).grid(column=2, row=0, padx=5, pady=5)
        
        # Output file selection
        ttk.Label(input_frame, text="Output File:").grid(column=0, row=1, sticky=tk.W, padx=5, pady=5)
        self.output_file_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.output_file_var, width=50).grid(column=1, row=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse...", command=self.browse_output_file).grid(column=2, row=1, padx=5, pady=5)
        
        # Verbose option
        self.verbose_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(input_frame, text="Show detailed progress", variable=self.verbose_var).grid(column=1, row=2, sticky=tk.W, padx=5, pady=5)
        
        # Run button
        ttk.Button(input_frame, text="Run Conflict Detection", command=self.run_detection).grid(column=1, row=3, pady=10)
        
        # Create frame for output text
        output_frame = ttk.Frame(root, padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollable text widget for output
        ttk.Label(output_frame, text="Output:").pack(anchor=tk.W)
        
        # Create a scrollbar
        scrollbar = ttk.Scrollbar(output_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget with scrollbar
        self.output_text = tk.Text(output_frame, wrap=tk.WORD, height=20, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Attach scrollbar to text widget
        self.output_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_text.yview)
        
        # Set default mods directory if on Windows
        if os.name == 'nt':
            default_mods_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'Electronic Arts', 'The Sims 4', 'Mods')
            if os.path.exists(default_mods_dir):
                self.mods_dir_var.set(default_mods_dir)
        
        # Set default output file in the same directory as the executable
        try:
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            self.output_file_var.set(os.path.join(base_dir, "conflict_report.csv"))
        except:
            self.output_file_var.set(os.path.join(os.path.expanduser('~'), "conflict_report.csv"))
    
    def browse_mods_dir(self):
        directory = filedialog.askdirectory(title="Select Sims 4 Mods Directory")
        if directory:
            self.mods_dir_var.set(directory)
    
    def browse_output_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if file_path:
            self.output_file_var.set(file_path)
    
    def run_detection(self):
        mods_dir = self.mods_dir_var.get()
        output_file = self.output_file_var.get()
        verbose = self.verbose_var.get()
        
        if not mods_dir:
            messagebox.showerror("Error", "Please select the Mods directory.")
            return
        
        if not os.path.exists(mods_dir):
            messagebox.showerror("Error", f"The selected directory does not exist: {mods_dir}")
            return
        
        # Clear output text
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state=tk.DISABLED)
        
        # Redirect stdout to the text widget
        old_stdout = sys.stdout
        sys.stdout = RedirectText(self.output_text)
        
        try:
            # Run in a separate thread to keep the GUI responsive
            self.root.after(100, lambda: self._execute_detection(mods_dir, output_file, verbose, old_stdout))
        except Exception as e:
            sys.stdout = old_stdout
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def _execute_detection(self, mods_dir, output_file, verbose, old_stdout):
        try:
            detect_conflicts(mods_dir, output_file, verbose)
            # Show success message
            if output_file:
                messagebox.showinfo("Success", f"Conflict detection completed. Report saved to:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Restore stdout
            sys.stdout = old_stdout


def main():
    # Check if we have command line arguments
    if len(sys.argv) > 1:
        # Command-line mode
        parser = argparse.ArgumentParser(
            description='Detect conflicts in Sims 4 mods.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument('mods_dir', help='Path to the Sims 4 Mods directory')
        parser.add_argument('-o', '--output', help='Path to save the conflict report')
        parser.add_argument('-v', '--verbose', action='store_true', help='Print detailed progress')
        
        args = parser.parse_args()
        
        # Run the conflict detector in command-line mode
        detect_conflicts(args.mods_dir, args.output, args.verbose)
    else:
        # GUI mode
        root = tk.Tk()
        app = ModConflictDetectorGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()
