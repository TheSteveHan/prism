#!/bin/bash
python ./manage.py migrate

# clear out expired JWT tokens
python ./manage.py flushexpiredtokens

# deploy the static files
python ./manage.py collectstatic --no-input --clear

export ANALYTICS_SERVER=api-service
export SEND_DRIP=1
export API_SERVER=api-service
export FE_SERVER=nginx
# run the server
gunicorn authentication.wsgi -b 0.0.0.0:8040
