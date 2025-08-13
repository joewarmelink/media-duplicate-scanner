# Remote Development Setup Guide

This guide will help you set up remote debugging for the Media Duplicate Scanner on your Linux machine while developing from your Windows laptop using Cursor.

## Prerequisites

### On Windows Laptop (Cursor IDE):
1. Install the **Remote - SSH** extension in Cursor
2. Ensure SSH client is available (Windows 10/11 usually has it built-in)

### On Linux Machine:
1. SSH server running
2. Python 3.6+ installed
3. Network access between machines

## Setup Steps

### Step 1: Install Remote-SSH Extension
1. Open Cursor
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Remote - SSH"
4. Install the extension by Microsoft

### Step 2: Configure SSH Connection
1. Press `Ctrl+Shift+P` to open command palette
2. Type "Remote-SSH: Connect to Host"
3. Select "Add New SSH Host"
4. Enter your SSH connection string:
   ```
   ssh username@your-linux-machine-ip
   ```
5. Choose SSH config file location (usually the default)

### Step 3: Connect to Remote Machine
1. Press `Ctrl+Shift+P` again
2. Type "Remote-SSH: Connect to Host"
3. Select your Linux machine from the list
4. Enter your password when prompted
5. Cursor will open a new window connected to the remote machine

### Step 4: Open Project on Remote Machine
1. In the remote Cursor window, go to File → Open Folder
2. Navigate to where you want to store the project on the Linux machine
3. Create a new folder or select existing one
4. Upload your project files to this location

### Step 5: Configure Python Interpreter
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose the Python interpreter on the Linux machine (usually `/usr/bin/python3`)

### Step 6: Set Up Debugging
1. Open the Debug panel (Ctrl+Shift+D)
2. You should see the debug configurations we created
3. Update the media directory path in the launch configuration:
   ```json
   "args": [
       "--log-level",
       "DEBUG",
       "--output-dir",
       "./media-dup-reports",
       "--log-dir",
       "./media-dup-reports/logs",
       "/actual/path/to/your/media/directory"
   ]
   ```

## Usage

### Running with Debugging:
1. Set breakpoints in your code by clicking in the gutter
2. Press F5 or go to Run → Start Debugging
3. Select "Remote Debug - Media Scanner" configuration
4. The debugger will stop at your breakpoints

### Running Without Debugging:
1. Open terminal in Cursor (Ctrl+`)
2. Run the script directly:
   ```bash
   python3 media_duplicate_scanner.py --log-level DEBUG /path/to/media
   ```

## File Transfer Options

### Option 1: Git (Recommended)
1. Initialize git repository on Linux machine
2. Push your code from Windows to a git repository
3. Clone/pull on Linux machine

### Option 2: SCP/SFTP
```bash
# From Windows command prompt
scp -r C:\path\to\your\project username@linux-ip:/path/on/linux
```

### Option 3: Shared Network Drive
1. Mount the Linux filesystem on Windows
2. Copy files directly

## Troubleshooting

### SSH Connection Issues:
- Ensure SSH server is running: `sudo systemctl status ssh`
- Check firewall settings
- Verify SSH key authentication if using keys

### Python Issues:
- Verify Python version: `python3 --version`
- Install missing packages if needed
- Check file permissions

### Debugging Issues:
- Ensure the media directory path is correct
- Check that the Python interpreter is properly set
- Verify file permissions on the media directories

## Performance Tips

1. **Use SSH Keys**: Set up SSH key authentication for faster connections
2. **Optimize Network**: Use wired connection if possible
3. **Local Testing**: Test with smaller directories first
4. **Monitor Resources**: Watch CPU/memory usage on Linux machine

## Example Workflow

1. **Develop on Windows**: Write and edit code in Cursor
2. **Sync to Linux**: Push changes to git or transfer files
3. **Debug on Linux**: Connect via Remote-SSH and debug with real data
4. **Iterate**: Make changes and repeat

This setup gives you the best of both worlds: comfortable development environment on Windows with direct access to your Linux media files for testing and debugging.
