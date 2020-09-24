#! /bin/sh

export FLASK_DEBUG=0
export FLASK_APP=flaskapp.py
export FLASK_ENV=development
flask run --host 0.0.0.0
