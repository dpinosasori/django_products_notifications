#!/bin/bash
# Start script for Render
python manage.py migrate
gunicorn core.wsgi:application --bind 0.0.0.0:$PORT