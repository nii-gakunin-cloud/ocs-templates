#!/bin/sh

: ${REPOSITORY:=10.0.0.1:5001/}

export REPOSITORY
export TAG=$(date "+%Y%m%d")

git clone https://github.com/NII-cloud-operation/CoursewareHub-LC_platform
git clone https://github.com/NII-cloud-operation/CoursewareHub-LC_idp-proxy.git

docker-compose -f docker-compose-nii.yml build
docker-compose build
docker-compose push

for name in auth-proxy auth-proxy-fed idp-proxy jupyterhub singleuser-disable-run-through; do
  docker tag ${REPOSITORY}vcp/coursewarehub:${name}-${TAG}  ${REPOSITORY}vcp/coursewarehub:${name}
  docker push ${REPOSITORY}vcp/coursewarehub:${name}
done
