## How to build container image

Get `tokyo_ca.crt` file and place it in the current directory.

```
docker build -t vcpsdk:20.10.0 .
```


## Configuration files

Edit the following files.

- docker.env.example      (rename to `env`)
- hosts.json.example      (rename to `hosts.json`)
- vcp_config.yml.example  (rename to `vcp_config.yml`)
- vcp_flavor.yml


## add VC node

```
. ./config/env

docker run --rm \
  -v $(pwd)/config:/opt/vcpsdk/vcpsdk/config \
  -v id_ed25519.pub:/tmp/key.pub \
  -e VCP_ACCESSKEY=${VCP_ACCESSKEY} \
  -e VC_NAME=${VC_NAME} \
  -e IMAGE_NAME=${IMAGE_NAME} \
  -e PROVIDER_NAME=${PROVIDER_NAME} \
  -e FLAVOR_NAME=${FLAVOR_NAME} \
  vcpsdk:20.10.0 add_vcnode.py
```


## delete all VC node

```
. ./config/env

docker run --rm \
  -v $(pwd)/config:/opt/vcpsdk/vcpsdk/config \
  -e VCP_ACCESSKEY=${VCP_ACCESSKEY} \
  -e VC_NAME=${VC_NAME} \
  -e IMAGE_NAME=${IMAGE_NAME} \
  -e PROVIDER_NAME=${PROVIDER_NAME} \
  -e FLAVOR_NAME=${FLAVOR_NAME} \
  vcpsdk:20.10.0 cleanup_vc.py
```


## get VC node

```
. ./config/env

docker run --rm \
  -v $(pwd)/config:/opt/vcpsdk/vcpsdk/config \
  -e VCP_ACCESSKEY=${VCP_ACCESSKEY} \
  -e VC_NAME=${VC_NAME} \
  vcpsdk:20.10.0 get_vcnode.py
```
