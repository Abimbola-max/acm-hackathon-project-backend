#!/bin/bash
source ~/Documents/acm-backend-project/acm-hackathon-project-backend/.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
deactivate
