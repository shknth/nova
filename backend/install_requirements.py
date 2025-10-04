#!/usr/bin/env python3
"""
Install required packages for NASA data access testing
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    """Install all required packages"""
    print("🚀 Installing NASA data access requirements...")
    print("="*50)
    
    packages = [
        "earthaccess",
        "xarray",
        "requests",
        "pandas",
        "numpy"
    ]
    
    success_count = 0
    for package in packages:
        print(f"\nInstalling {package}...")
        if install_package(package):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"Installation complete: {success_count}/{len(packages)} packages installed")
    
    if success_count == len(packages):
        print("🎉 All packages installed successfully!")
        print("You can now run: python data_test.py")
    else:
        print("⚠️  Some packages failed to install")
        print("Try installing them manually or check your Python environment")

if __name__ == "__main__":
    main()
