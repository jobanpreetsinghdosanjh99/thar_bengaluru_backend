#!/bin/bash

# THAR Bengaluru Backend Setup Script

echo "======================================"
echo "THAR Bengaluru Backend Setup"
echo "======================================"

# Create virtual environment
echo -e "\n1. Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo -e "\n2. Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo -e "\n3. Installing dependencies..."
pip install -r requirements.txt

# Create .env file from template
echo -e "\n4. Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please update with your database credentials."
else
    echo ".env file already exists."
fi

echo -e "\n======================================"
echo "Setup complete!"
echo "======================================"
echo -e "\nNext steps:"
echo "1. Update .env file with your PostgreSQL credentials"
echo "2. Ensure PostgreSQL is running"
echo "3. Run: python main.py"
echo "4. Visit: http://localhost:8000/docs"
