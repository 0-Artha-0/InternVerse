#!/bin/bash

# Make the script executable
chmod +x startup.sh

# Start the application on port 8000 to work with Azure App Service
gunicorn --bind 0.0.0.0:8000 --reuse-port --timeout 600 main:app