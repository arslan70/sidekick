#!/usr/bin/env python3
"""
Quick Run Script for SideKick Chainlit App

This script provides a simple way to run the Chainlit app with proper setup.
"""

import os
import subprocess
from pathlib import Path


def setup_environment():
    """Ensure environment is properly configured."""
    # Load .env if it exists
    env_file = Path(".env")
    if env_file.exists():
        print("📁 Loading environment from .env file...")
        # Simple .env loading without external dependencies
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
    else:
        print("⚠️  No .env file found. Using default settings...")
        print("💡 Run 'python setup_local_dev.py' to create .env file")
        # Set default environment variables
        os.environ.setdefault("AWS_REGION", "eu-central-1")
        os.environ.setdefault("BEDROCK_MODEL_ID", "eu.amazon.nova-pro-v1:0")
    
    # Check AWS credentials warning
    has_aws_creds = (
        os.getenv("AWS_ACCESS_KEY_ID") or 
        os.getenv("AWS_PROFILE") or 
        (Path.home() / ".aws" / "credentials").exists()
    )
    
    if not has_aws_creds:
        print("⚠️  WARNING: No AWS credentials detected!")
        print("   The app needs AWS Bedrock access for LLMs to work")
        print("   Run 'aws configure' or set AWS credentials in .env")
        print("   Continuing anyway - you may see authentication errors...")


def check_dependencies():
    """Check if required packages are installed."""
    # Map package names to their import names
    package_imports = {
        "chainlit": "chainlit",
        "strands-agents": "strands",
        "boto3": "boto3"
    }
    
    missing_packages = []
    
    for package_name, import_name in package_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("💡 Run: python setup_local_dev.py --install-deps")
        return False
    
    return True


def run_chainlit_app():
    """Run the Chainlit application."""
    print("🚀 Starting SideKick Chainlit App...")
    print("📱 Access the app at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the app\n")
    
    try:
        # Change to the app directory and run
        app_file = Path("app/app.py")
        if not app_file.exists():
            print(f"❌ App file not found: {app_file.absolute()}")
            return 1
        
        # Run chainlit
        cmd = ["chainlit", "run", str(app_file), "--host", "localhost", "--port", "8000"]
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Chainlit app: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 SideKick stopped by user")
        return 0
    except FileNotFoundError:
        print("❌ Chainlit not found. Please install it first:")
        print("   pip install chainlit")
        return 1


def main():
    """Main function."""
    print("🏗️  SideKick - Quick Run")
    print("=" * 30)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Run the app
    return run_chainlit_app()


if __name__ == "__main__":
    exit(main())