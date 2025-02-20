#!/bin/bash
set -ex
python ./manage.py migrate

# deploy the static files
python ./manage.py collectstatic --no-input --clear
cp -rf static/* shared-static-files/

export ANALYTICS_SERVER=api-service
export SEND_DRIP=1
export API_SERVER=api-service
export FE_SERVER=nginx
# run the server
gunicorn authentication.wsgi -b 0.0.0.0:8040
