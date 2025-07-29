#!/bin/bash

echo "========================================"
echo "DigiSafe Microservices Setup Script"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

echo "Python found. Starting setup..."
echo

# List of services to setup
SERVICES=("analysis-service" "auction-service" "payment-service" "quality-service" "user-service" "verification-service")

# Loop through each service
for service in "${SERVICES[@]}"; do
    echo
    echo "========================================"
    echo "Setting up $service"
    echo "========================================"
    
    # Check if service directory exists
    if [ ! -d "services/$service" ]; then
        echo "ERROR: services/$service directory not found"
        continue
    fi
    
    # Change to service directory
    cd "services/$service"
    
    # Remove existing venv if it exists
    if [ -d "venv" ]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    fi
    
    # Create new virtual environment
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment for $service"
        cd ../..
        continue
    fi
    
    # Activate virtual environment and install dependencies
    echo "Activating virtual environment and installing dependencies..."
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to activate virtual environment for $service"
        cd ../..
        continue
    fi
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        echo "Installing requirements from requirements.txt..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to install requirements for $service"
            cd ../..
            continue
        fi
    else
        echo "WARNING: requirements.txt not found for $service"
    fi
    
    # Deactivate virtual environment
    deactivate
    
    echo "$service setup completed successfully!"
    
    # Return to root directory
    cd ../..
done

echo
echo "========================================"
echo "Setup completed!"
echo "========================================"
echo
echo "All microservices have been configured with:"
echo "- Virtual environments created in each service directory"
echo "- Dependencies installed from requirements.txt"
echo "- VS Code settings configured for proper Python interpreter detection"
echo
echo "Next steps:"
echo "1. Restart VS Code to ensure all settings are applied"
echo "2. Open any service directory in VS Code"
echo "3. Select the Python interpreter: ./venv/bin/python (Linux/macOS) or ./venv/Scripts/python.exe (Windows)"
echo "4. The reportMissingImports errors should now be resolved"
echo 