#/bin/bash
set -ex
yarn build
REGISTRY=651706751476.dkr.ecr.us-east-2.amazonaws.com
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $REGISTRY 
docker build -t bloom/prism-nginx .
docker tag bloom/prism-nginx:latest $REGISTRY/bloom/prism-nginx:latest
docker push $REGISTRY/bloom/prism-nginx:latest
