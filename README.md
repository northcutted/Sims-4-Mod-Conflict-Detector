# Sims 4 Mod Conflict Detector

This tool scans your Sims 4 mods folder to identify potential conflicts between different mods. It analyzes the resource identifiers in package files to detect when two or more mods are trying to modify the same game resources.

## Features

- Scans Sims 4 package files (.package) to extract resource identifiers
- Detects conflicts where multiple mods modify the same resources
- Works on Windows, macOS, and Linux
- Supports both DBPF v1 and v2 package formats

## Requirements

- Python 3.6 or newer

## Installation

### Windows

1. Download or clone this repository
2. Make sure Python 3.6+ is installed (download from [python.org](https://www.python.org/downloads/))
3. Double-click on `run_detector.bat` to start the tool

Alternatively, you can install the package:

```
pip install -e .
mod_conflict_detector
```

### macOS/Linux

1. Download or clone this repository
2. Open Terminal
3. Navigate to the project directory: 
   ```
   cd path/to/mod_conflict_detector
   ```
4. Run the tool: 
   ```
   python mod_conflict_detector.py
   ```

Or install the package:

```
pip install -e .
mod_conflict_detector
```

## Usage

### Basic Usage

Run the tool with the path to your mods folder:

```
python mod_conflict_detector.py "/path/to/Sims 4/Mods"
```

### Command Line Options

```
python mod_conflict_detector.py [options] [path_to_mods_folder]
```

Options:
- `--recursive` or `-r`: Scan subdirectories (default: enabled)
- `--verbose` or `-v`: Display more detailed information
- `--by-type` or `-t`: Group conflicts by resource type instead of individual resources
- `--output` or `-o`: Specify output file for the report (default: displayed in console)

### Examples

Scan the default Sims 4 Mods folder:
```
python mod_conflict_detector.py
```

Scan a specific folder:
```
python mod_conflict_detector.py "D:\Games\Sims 4\Mods"
```

Generate a report file:
```
python mod_conflict_detector.py --output conflicts.txt
```

## Common Paths to Sims 4 Mods Folder

- **Windows**: `C:\Users\[YourUsername]\Documents\Electronic Arts\The Sims 4\Mods`
- **macOS**: `/Users/[YourUsername]/Documents/Electronic Arts/The Sims 4\Mods`

## Troubleshooting

### File Permission Issues

If you encounter permission errors:
- Make sure you have read access to the mods folder
- Try running the script with administrator privileges

### Large Files

For very large mod folders:
- The scan might take some time, please be patient
- If you encounter memory issues, try scanning subdirectories separately

### Windows-Specific Issues

- If you get "Python is not recognized as an internal or external command", make sure Python is installed and added to your PATH
- If you have issues with file paths containing spaces, enclose the path in quotes

## Development

To run the test suite:

```
python run_tests.py
```

## License

This project is open source and available under the MIT License.
