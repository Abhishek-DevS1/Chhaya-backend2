#!/bin/bash

project_directory="/home/abhishek/CICDpro/Chhaya-backend"

echo "Change directory to python project directory"

cd $project_directory

echo "Activating the virtual environment"
source venv/bin/activate

echo "Checking if virtual environment is active after activation"
if [ -z "$VIRTUAL_ENV" ]; then
  echo "No virtual environment is active."
else
  echo "Virtual environment is active: $VIRTUAL_ENV"
fi

#echo "Processing for makemigrations"
cd $project_directory/Chhaya-backend
#python3 manage.py makemigrations --noinput

echo "Processing for migrations"
python3 manage.py migrate

echo "Migrations Done"

echo "Deactivating the virtual environment"
deactivate

echo "Checking if virtual environment is active after deactivation"
if [ -z "$VIRTUAL_ENV" ]; then
  echo "No virtual environment is active."
else
  echo "Virtual environment is active: $VIRTUAL_ENV"
fi
