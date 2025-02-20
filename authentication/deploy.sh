#/bin/bash
set -ex
REGISTRY=651706751476.dkr.ecr.us-east-2.amazonaws.com
APP=prism-auth
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $REGISTRY 
docker build -t bloom/$APP .
docker tag bloom/$APP:latest $REGISTRY/bloom/$APP:latest
docker push $REGISTRY/bloom/$APP:latest
ssh ec2-user@BLOOM -t "cd prism; docker-compose pull auth && docker-compose up -d auth"
