set -xe
APP_NAME='auth'
PROJECT='tm'
GALLERY='us.gcr.io'
PROJECT_ID='skolivine-kube'
IMAGE_NAME=${PROJECT}-apps-${APP_NAME}
TAG_NAME=latest

realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}
SCRIPT=`realpath $0`
BASE_DIR=`dirname ${SCRIPT}`/
DOCKER_FILE_REL_PATH='../Dockerfile'
DOCKER_DIR=`dirname ${BASE_DIR}${DOCKER_FILE_REL_PATH}`
RELEASE_NAME="${PROJECT}-${APP_NAME}"
echo ${DOCKER_DIR}
pushd ${DOCKER_DIR}
docker build . -t ${IMAGE_NAME}:${TAG_NAME}
docker tag ${IMAGE_NAME}:${TAG_NAME} ${GALLERY}/${PROJECT_ID}/${IMAGE_NAME}:${TAG_NAME}
docker push ${GALLERY}/${PROJECT_ID}/${IMAGE_NAME}:${TAG_NAME} 
popd
if command -v helm3 &> /dev/null
then
    HELM=helm3
else
    HELM=helm
fi
echo "using $HELM"
${HELM} upgrade --install ${RELEASE_NAME} ./deploy/${APP_NAME} --debug \
    --set image.repository=${GALLERY}/${PROJECT_ID}/${IMAGE_NAME},image.tag=${TAG_NAME},timestamp=`date +t%s` $1 --wait
../gcr_delete_old_images.sh $IMAGE_NAME 1


