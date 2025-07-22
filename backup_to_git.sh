#!/bin/bash

# Set working directory to your project
cd /home/gowth/photon_cure/

# Set Git identity (optional, but useful for cron jobs)
git config user.name "Gka001"
git config user.email "gowthamkanyadhara09@gmail.com"

# Add all changes
git add .

# Commit with current date and time
git commit -m "Automated backup on $(date '+%Y-%m-%d %H:%M:%S')"

# Push to GitHub
git push origin main  # Or replace 'main' with your current branch
