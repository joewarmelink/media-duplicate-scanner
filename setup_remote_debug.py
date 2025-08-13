#!/usr/bin/env python3
"""
Remote Debug Setup Helper

This script helps validate the remote environment and configure debugging settings.
Run this on the Linux machine after connecting via Remote-SSH.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.major}.{version.minor}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("❌ Python 3.6+ is required")
        return False
    else:
        print("✅ Python version is compatible")
        return True


def check_required_modules():
    """Check if required modules are available."""
    required_modules = [
        'argparse', 'hashlib', 'json', 'logging', 'os', 're', 'sys',
        'collections', 'datetime', 'pathlib', 'typing'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nMissing modules: {', '.join(missing_modules)}")
        return False
    else:
        print("\n✅ All required modules are available")
        return True


def check_file_permissions():
    """Check file permissions for the scanner script."""
    script_path = Path("media_duplicate_scanner.py")
    
    if not script_path.exists():
        print("❌ media_duplicate_scanner.py not found")
        return False
    
    # Check if script is executable
    if os.access(script_path, os.X_OK):
        print("✅ Script is executable")
    else:
        print("⚠️  Script is not executable, making it executable...")
        try:
            script_path.chmod(0o755)
            print("✅ Made script executable")
        except Exception as e:
            print(f"❌ Failed to make script executable: {e}")
            return False
    
    return True


def create_test_directories():
    """Create test directories for output."""
    test_dirs = [
        "media-dup-reports",
        "media-dup-reports/logs"
    ]
    
    for dir_path in test_dirs:
        path = Path(dir_path)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            except Exception as e:
                print(f"❌ Failed to create directory {dir_path}: {e}")
                return False
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    return True


def test_scanner_import():
    """Test if the scanner can be imported."""
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        # Try to import the scanner
        import media_duplicate_scanner
        print("✅ Scanner module imports successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import scanner: {e}")
        return False


def generate_debug_config():
    """Generate a debug configuration file."""
    config_content = """{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Remote Debug - Media Scanner",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/media_duplicate_scanner.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "args": [
                "--log-level",
                "DEBUG",
                "--output-dir",
                "./media-dup-reports",
                "--log-dir",
                "./media-dup-reports/logs",
                "/path/to/your/media/directory"
            ],
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}"""
    
    config_path = Path(".vscode/launch.json")
    config_path.parent.mkdir(exist_ok=True)
    
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        print("✅ Debug configuration created")
        return True
    except Exception as e:
        print(f"❌ Failed to create debug config: {e}")
        return False


def main():
    """Main setup function."""
    print("🔧 Remote Debug Setup Helper")
    print("=" * 40)
    
    # System information
    print(f"Platform: {platform.platform()}")
    print(f"Current directory: {os.getcwd()}")
    print()
    
    # Run checks
    checks = [
        ("Python Version", check_python_version),
        ("Required Modules", check_required_modules),
        ("File Permissions", check_file_permissions),
        ("Test Directories", create_test_directories),
        ("Scanner Import", test_scanner_import),
        ("Debug Config", generate_debug_config)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error during {check_name}: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 SETUP SUMMARY:")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check_name}: {status}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All checks passed! Your environment is ready for remote debugging.")
        print("\nNext steps:")
        print("1. Update the media directory path in .vscode/launch.json")
        print("2. Set breakpoints in your code")
        print("3. Press F5 to start debugging")
    else:
        print("⚠️  Some checks failed. Please address the issues above before proceeding.")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
