#/bin/bash
REGISTRY=651706751476.dkr.ecr.us-east-2.amazonaws.com
APP=api-service
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $REGISTRY 
docker build -t bloom/prism-$APP .
docker tag bloom/prism-$APP:latest $REGISTRY/bloom/prism-$APP:latest
docker push $REGISTRY/bloom/prism-$APP:latest
ssh ec2-user@BLOOM -t "cd prism; docker-compose pull api-service && docker-compose up -d api-service"
