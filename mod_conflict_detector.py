#!/usr/bin/env python3
import os
import argparse
import csv
import time
import tkinter as tk
from ttkthemes import ThemedTk
from tkinter import filedialog, messagebox, ttk
import sys
import logging
from typing import Dict, List, Set, Tuple
from pathlib import Path

from package_parser import parse_package_file, ResourceKey, find_conflicts
from scanner import scan_mods_directory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Enable detailed debug logging for package parser
logging.getLogger('package_parser').setLevel(logging.INFO)


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
    resource_count = 0
    
    for i, file_path in enumerate(package_files):
        if verbose and i % 100 == 0:
            print(f"Processing file {i+1}/{len(package_files)}: {os.path.basename(file_path)}")
        
        try:
            # Parse package file to extract resources
            resources = parse_package_file(file_path)
            processed_count += 1
            
            # Add each resource to the resource map
            for resource_key in resources:
                resource_count += 1
                if resource_key not in resource_map:
                    resource_map[resource_key] = []
                resource_map[resource_key].append(file_path)
                
            if verbose and i % 1000 == 999:
                print(f"Progress update: {resource_count} total resources found so far")
                
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
    file_conflicts: Dict[str, Dict[str, Set[ResourceKey]]] = {}
    
    # Build a map of which files conflict with which other files and their shared resources
    for resource_key, file_paths in conflicts.items():
        for file_path in file_paths:
            if file_path not in file_conflicts:
                file_conflicts[file_path] = {}
            
            # Add all conflicting files for this file and track the conflicting resources
            for conflict_path in file_paths:
                if conflict_path != file_path:
                    if conflict_path not in file_conflicts[file_path]:
                        file_conflicts[file_path][conflict_path] = set()
                    file_conflicts[file_path][conflict_path].add(resource_key)
    
    # Sort files by number of conflicts (most conflicts first)
    sorted_files = sorted(file_conflicts.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Output to console
    total_conflicts = len(conflicts)
    total_files = len(file_conflicts)
    
    print(f"\n{'='*80}")
    print(f"MOD CONFLICT ANALYSIS REPORT")
    print(f"{'='*80}")
    print(f"\nSummary:")
    print(f"• Found {total_conflicts:,} conflicting resources across {total_files:,} mod files")
    print(f"• This means multiple mods are trying to modify the same game elements")
    print("\nConflict Severity Guide:")
    print("🔴 High: >100 shared resources - Mods likely incompatible, remove one")
    print("🟡 Medium: 10-100 shared resources - Mods may have issues, test in game")
    print("🟢 Low: <10 shared resources - Minor conflicts, probably safe")
    
    # Show top conflicts with more detail
    print("\nDetailed Analysis:")
    shown_files = set()  # Track which files we've shown to avoid duplication
    
    for file_path, conflicts_dict in sorted_files[:10]:  # Show top 10 most conflicting mods
        if file_path in shown_files:
            continue
            
        rel_path = get_relative_mod_path(file_path)
        total_conflicts = sum(len(resources) for resources in conflicts_dict.values())
        severity = "🔴" if total_conflicts > 100 else "🟡" if total_conflicts > 10 else "🟢"
        
        print(f"\n{severity} {rel_path}")
        print(f"   Conflicts with {len(conflicts_dict):,} other mods, sharing {total_conflicts:,} resources")
        
        # Show top 3 most significant conflicts
        significant_conflicts = sorted(conflicts_dict.items(), key=lambda x: len(x[1]), reverse=True)[:3]
        for conflict_path, shared_resources in significant_conflicts:
            shown_files.add(conflict_path)  # Mark this file as shown
            rel_conflict = get_relative_mod_path(conflict_path)
            resource_types = classify_resource_types(shared_resources)
            print(f"   • Conflicts with: {rel_conflict}")
            print(f"     - Shares {len(shared_resources):,} resources: {', '.join(resource_types)}")
        
        if len(conflicts_dict) > 3:
            print(f"   • ...and {len(conflicts_dict) - 3:,} other mods")
    
    if len(sorted_files) > 10:
        print(f"\n...and {len(sorted_files) - 10:,} other mods with conflicts")
    
    print("\nRecommended Actions:")
    print("1. Check mods marked 🔴 first - these have the most conflicts")
    print("2. For conflicting mods, keep only one version of each mod")
    print("3. Ensure you have the latest version of each mod")
    print("4. Some mods (like merged CC) are designed to work together")
    print("5. Test your game after removing any mods")
    
    # Write to file if specified
    if output_file:
        write_detailed_csv_report(sorted_files, output_file)
        print(f"\nDetailed conflict report saved to: {output_file}")

def classify_resource_types(resources: Set[ResourceKey]) -> List[str]:
    """
    Classify resources into user-friendly categories based on their type IDs.
    Returns a list of unique resource type descriptions.
    """
    type_categories = {
        0x00B2D882: "Model Data",
        0x0333406C: "Catalog Definition",
        0x025C90C6: "Material Definition",
        0x736E6578: "Texture",
        0x8EAF13DE: "Tuning Data",
        0x02D5DF13: "Footprint",
        0x0166038C: "Object Definition",
    }
    
    types = set()
    for resource in resources:
        if resource.type_id in type_categories:
            types.add(type_categories[resource.type_id])
        else:
            types.add(f"Type 0x{resource.type_id:08x}")
    
    return list(types)

def write_detailed_csv_report(sorted_files: List[Tuple[str, Dict[str, Set[ResourceKey]]]], output_file: str) -> None:
    """
    Write a detailed conflict report to a CSV file.
    
    Args:
        sorted_files: List of tuples containing (file_path, dict of conflicting files and their resources)
        output_file: Path to save the report
    """
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:  # Use UTF-8 with BOM for Excel
        writer = csv.writer(csvfile)
        
        # Write headers with descriptions
        writer.writerow([
            'Mod File',
            'Conflicts With',
            'Resource Count',
            'Resource Types',
            'Severity',
            'Action Required'
        ])
        
        # Add a guide row
        writer.writerow([
            'The mod file being analyzed',
            'The mod it conflicts with',
            'Number of shared resources',
            'Types of resources in conflict',
            'How serious the conflict is',
            'Recommended action to take'
        ])
        
        # Add a separator row
        writer.writerow(['---'] * 6)
        
        for file_path, conflicts_dict in sorted_files:
            rel_path = get_relative_mod_path(file_path)
            
            for conflict_path, shared_resources in conflicts_dict.items():
                rel_conflict = get_relative_mod_path(conflict_path)
                resource_types = classify_resource_types(shared_resources)
                resource_count = len(shared_resources)
                
                # Determine severity and action
                if resource_count > 100:
                    severity = "High"
                    action = "Remove one of the conflicting mods"
                elif resource_count > 10:
                    severity = "Medium"
                    action = "Test in game and monitor for issues"
                else:
                    severity = "Low"
                    action = "Likely safe, but test to be sure"
                
                writer.writerow([
                    rel_path,
                    rel_conflict,
                    resource_count,
                    ", ".join(resource_types),
                    severity,
                    action
                ])
        
        # Add footer with summary info
        writer.writerow([])  # Blank row
        writer.writerow(['Severity Guide', '', '', '', '', ''])
        writer.writerow(['High', '> 100 shared resources', 'Mods likely incompatible', '', '', ''])
        writer.writerow(['Medium', '10-100 shared resources', 'Potential issues', '', '', ''])
        writer.writerow(['Low', '< 10 shared resources', 'Probably compatible', '', '', ''])


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
        self.root.geometry("1000x700")
        
        # Set application icon
        try:
            # Handle both bundled and development paths
            if getattr(sys, 'frozen', False):
                # If we're running as a bundle
                if sys.platform == 'darwin':
                    # On macOS, resources are in the bundle
                    bundle_dir = os.path.dirname(sys.executable)
                    icon_path = os.path.join(bundle_dir, '..', 'Resources', 'icon.png')
                else:
                    # On other platforms
                    icon_path = os.path.join(sys._MEIPASS, 'icon.png')
            else:
                # If we're running from source
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
            
            if os.path.exists(icon_path):
                icon_img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon_img)
                self.app_icon = icon_img  # Store reference
        except Exception as e:
            logger.warning(f"Could not load application icon: {e}")
        
        # Configure custom styles
        # style = ttk.Style()
  
        
        # # Configure modern looking theme
        # if os.name == 'nt':  # Windows
        #     style.theme_use('vista')
        # else:  # macOS and others
        #     style.theme_use('clam')
        
        # Modern color scheme
        self.colors = {
            'primary': '#2980b9',      # Blue
            'secondary': '#27ae60',    # Green
            'background': '#f5f6fa',   # Light gray
            'surface': '#ffffff',      # White
            'text': '#2c3e50',        # Dark gray
            'error': '#e74c3c',       # Red
            'warning': '#f1c40f'      # Yellow
        }
        
        # Override dialog colors
        self.root.option_add('*Dialog.msg.font', 'Helvetica 12')
        self.root.option_add('*Dialog.msg.background', self.colors['surface'])
        self.root.option_add('*Dialog.msg.foreground', self.colors['text'])
        self.root.option_add('*Dialog.background', self.colors['surface'])
        self.root.option_add('*Dialog.foreground', self.colors['text'])
        self.root.option_add('*Dialog.Button.background', self.colors['primary'])
        self.root.option_add('*Dialog.Button.foreground', self.colors['surface'])
        
        # Configure field colors for both themes
        # style.configure('TEntry', 
        #     fieldbackground=self.colors['surface'],
        #     selectbackground=self.colors['primary'],
        #     selectforeground=self.colors['surface']
        # )
        
        # # Title style
        # style.configure(
        #     'Title.TLabel',
        #     font=('Helvetica', 24, 'bold'),
        #     foreground=self.colors['primary'],
        #     background=self.colors['background']
        # )
        
        # # Header style
        # style.configure(
        #     'Header.TLabel',
        #     font=('Helvetica', 14, 'bold'),
        #     foreground=self.colors['text'],
        #     background=self.colors['background']
        # )
        
        # # Info label style
        # style.configure(
        #     'Info.TLabel',
        #     font=('Helvetica', 12),
        #     foreground=self.colors['text'],
        #     background=self.colors['background']
        # )
        
        # # Custom button style
        # style.configure(
        #     'Action.TButton',
        #     font=('Helvetica', 12, 'bold'),
        #     padding=10,
        #     background=self.colors['primary']
        # )
        # style.map('Action.TButton',
        #     background=[('pressed', self.colors['primary']), ('active', self.colors['secondary'])]
        # )
        
        # # Progress bar style
        # style.configure(
        #     "Horizontal.TProgressbar",
        #     troughcolor=self.colors['background'],
        #     background=self.colors['secondary'],
        #     bordercolor=self.colors['background'],
        #     lightcolor=self.colors['secondary'],
        #     darkcolor=self.colors['secondary']
        # )
        
        # # Frame style
        # style.configure(
        #     'Card.TFrame',
        #     background=self.colors['surface']
        # )
        
        # # LabelFrame style
        # style.configure(
        #     'Card.TLabelframe',
        #     background=self.colors['surface']
        # )
        # style.configure(
        #     'Card.TLabelframe.Label',
        #     font=('Helvetica', 12, 'bold'),
        #     foreground=self.colors['text'],
        #     background=self.colors['surface']
        # )
        
        # Configure root background
        self.root.configure(bg=self.colors['background'])
        
        # Store icon references to prevent garbage collection
        self.icons = {
            'mods': "📁",
            'output': "💾",
            'progress': "⏳",
            'files': "📂",
            'resources': "🔧",
            'conflicts': "⚠️",
            'search': "🔍",
            'completed': "✅"
        }
        
        # Main container with padding and rounded corners
        main_frame = ttk.Frame(root, padding="20", style='Card.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title with icon
        title_frame = ttk.Frame(main_frame, style='Card.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        try:
            # Load and display icon in title
            icon_size = 32
            title_icon = tk.PhotoImage(file=icon_path).subsample(
                max(1, int(512/icon_size)),  # Assuming original is 512x512
                max(1, int(512/icon_size))
            )
            icon_label = ttk.Label(title_frame, image=title_icon, style='Title.TLabel')
            icon_label.image = title_icon  # Keep reference
            icon_label.pack(side=tk.LEFT, padx=(0, 10))
        except Exception as e:
            logger.warning(f"Could not load title icon: {e}")
        
        title_label = ttk.Label(
            title_frame, 
            text="Sims 4 Mod Conflict Detector",
            style='Title.TLabel'
        )
        title_label.pack(side=tk.LEFT)

        # Settings frame with better visual hierarchy
        settings_frame = ttk.LabelFrame(
            main_frame,
            text="Settings",
            padding="15",
            style='Card.TLabelframe'
        )
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Mods directory selection with icon
        mods_dir_frame = ttk.Frame(settings_frame)
        mods_dir_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            mods_dir_frame,
            text=f"{self.icons['mods']} Mods Directory:",
            style='Info.TLabel'
        ).pack(side=tk.LEFT, padx=5)
        
        self.mods_dir_var = tk.StringVar()
        mods_entry = ttk.Entry(
            mods_dir_frame,
            textvariable=self.mods_dir_var,
            width=60
        )
        mods_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            mods_dir_frame,
            text="Browse...",
            command=self.browse_mods_dir,
            style='Action.TButton'
        )
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Output file selection with icon
        output_frame = ttk.Frame(settings_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            output_frame,
            text=f"{self.icons['output']} Output File:",
            style='Info.TLabel'
        ).pack(side=tk.LEFT, padx=5)
        
        self.output_file_var = tk.StringVar()
        output_entry = ttk.Entry(
            output_frame,
            textvariable=self.output_file_var,
            width=60
        )
        output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            output_frame,
            text="Browse...",
            command=self.browse_output_file,
            style='Action.TButton'
        )
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # Options with icons
        options_frame = ttk.Frame(settings_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.verbose_var = tk.BooleanVar(value=True)
        verbose_cb = ttk.Checkbutton(
            options_frame,
            text="🔍 Show detailed progress",
            variable=self.verbose_var
        )
        verbose_cb.pack(side=tk.LEFT, padx=5)
        
        # Progress section with modern styling
        progress_frame = ttk.LabelFrame(
            main_frame,
            text="Progress",
            padding="15",
            style='Card.TLabelframe'
        )
        progress_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            style='Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Progress label with icon
        self.progress_label = ttk.Label(
            progress_frame,
            text=f"{self.icons['progress']} Ready to scan",
            style='Info.TLabel'
        )
        self.progress_label.pack(pady=5)
        
        # Status counters with icons
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.file_counter = ttk.Label(
            status_frame,
            text=f"{self.icons['files']} Files: 0/0",
            style='Info.TLabel'
        )
        self.file_counter.pack(side=tk.LEFT, padx=20)
        
        self.resource_counter = ttk.Label(
            status_frame,
            text=f"{self.icons['resources']} Resources: 0",
            style='Info.TLabel'
        )
        self.resource_counter.pack(side=tk.LEFT, padx=20)
        
        self.conflict_counter = ttk.Label(
            status_frame,
            text=f"{self.icons['conflicts']} Conflicts: 0",
            style='Info.TLabel'
        )
        self.conflict_counter.pack(side=tk.LEFT, padx=20)
        
        # Run button with icon
        self.run_button = ttk.Button(
            main_frame,
            text=f"{self.icons['search']} Start Conflict Detection",
            command=self.run_detection,
            style='Action.TButton'
        )
        self.run_button.pack(pady=10)
        
        # Output log with modern styling
        log_frame = ttk.LabelFrame(
            main_frame,
            text="Output Log",
            padding="15",
            style='Card.TLabelframe'
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollable text widget with modern font
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            height=20,
            font=('SF Mono' if sys.platform == 'darwin' else 'Consolas', 10),
            bg=self.colors['surface'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            selectbackground=self.colors['primary'],
            selectforeground=self.colors['surface'],
            state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        self.output_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_text.yview)
        
        # Set default mods directory if on Windows
        if os.name == 'nt':
            default_mods_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'Electronic Arts', 'The Sims 4', 'Mods')
            if os.path.exists(default_mods_dir):
                self.mods_dir_var.set(default_mods_dir)
        
        # Set default output file
        try:
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            self.output_file_var.set(os.path.join(base_dir, "conflict_report.csv"))
        except:
            self.output_file_var.set(os.path.join(os.path.expanduser('~'), "conflict_report.csv"))
        
        # Initialize progress tracking
        self.total_files = 0
        self.processed_files = 0
        self.total_resources = 0
        self.total_conflicts = 0
    
    def update_progress(self, current, total, message=None):
        """Update progress bar and label"""
        progress = (current / total * 100) if total > 0 else 0
        self.progress_var.set(progress)
        
        # Update progress message with icon
        if message:
            icon = self.icons['completed'] if progress >= 100 else self.icons['progress']
            self.progress_label.config(text=f"{icon} {message}")
        
        # Update file counter with icon
        self.file_counter.config(text=f"{self.icons['files']} Files: {current}/{total}")
        
        # Force update
        self.root.update_idletasks()
    
    def update_resource_count(self, count):
        """Update resource counter"""
        self.total_resources = count
        self.resource_counter.config(text=f"{self.icons['resources']} Resources: {count:,}")
        self.root.update_idletasks()
    
    def update_conflict_count(self, count):
        """Update conflict counter"""
        self.total_conflicts = count
        self.conflict_counter.config(text=f"{self.icons['conflicts']} Conflicts: {count:,}")
        self.root.update_idletasks()
    
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
        
        # Disable run button during processing
        self.run_button.state(['disabled'])
        
        # Clear output text
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state=tk.DISABLED)
        
        # Reset progress
        self.progress_var.set(0)
        self.progress_label.config(text="Scanning mods directory...")
        
        # Redirect stdout
        old_stdout = sys.stdout
        sys.stdout = RedirectText(self.output_text)
        
        try:
            # Run in a separate thread
            self.root.after(100, lambda: self._execute_detection(mods_dir, output_file, verbose, old_stdout))
        except Exception as e:
            sys.stdout = old_stdout
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.run_button.state(['!disabled'])
    
    def _execute_detection(self, mods_dir, output_file, verbose, old_stdout):
        try:
            # Start detection with progress tracking
            package_files = scan_mods_directory(mods_dir, verbose=verbose)
            self.total_files = len(package_files)
            self.processed_files = 0
            
            # Process files with progress updates
            resource_map = {}
            for file_path in package_files:
                try:
                    resources = parse_package_file(file_path)
                    if resources:
                        resource_map[file_path] = resources
                        self.update_resource_count(sum(len(r) for r in resource_map.values()))
                except Exception as e:
                    if verbose:
                        print(f"Error processing {file_path}: {str(e)}")
                
                self.processed_files += 1
                self.update_progress(
                    self.processed_files,
                    self.total_files,
                    f"Processing file {self.processed_files}/{self.total_files}"
                )
            
            # Find conflicts
            conflicts = find_conflicts(resource_map)
            self.update_conflict_count(len(conflicts))
            
            # Generate report
            if conflicts:
                self.progress_label.config(text="Generating conflict report...")
                generate_report(conflicts, output_file, verbose)
                self.progress_label.config(text="Completed!")
                
                if output_file:
                    messagebox.showinfo(
                        "Success",
                        f"Found {len(conflicts):,} conflicts across {len(resource_map):,} files.\n\n"
                        f"Report saved to:\n{output_file}"
                    )
            else:
                self.progress_label.config(text="No conflicts detected")
                messagebox.showinfo("Success", "No conflicts were detected in your mods.")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Restore stdout and enable run button
            sys.stdout = old_stdout
            self.run_button.state(['!disabled'])


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
        root = ThemedTk(theme='yaru')
        app = ModConflictDetectorGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()
