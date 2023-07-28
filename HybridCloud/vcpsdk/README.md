## How to build container image

Get `vcp_ca.crt` file and place it in the current directory.

```
docker build -t vcpsdk:22.10.0 .
```


## Configuration files

Edit the following files.

- docker.env.example      (rename to `env`)
- hosts.json.example      (rename to `hosts.json`)
- vcp_config.yml.example  (rename to `vcp_config.yml`)
- vcp_flavor.yml


## add VC node

```
docker run --rm \
  -v $(pwd):/opt/ocs-templates/HybridCloud/vcpsdk \
  --env-file=$(pwd)/config/env \
  vcpsdk:22.10.0 add_vcnode.py
```


## delete all VC node

```
docker run --rm \
  -v $(pwd):/opt/ocs-templates/HybridCloud/vcpsdk \
  --env-file=$(pwd)/config/env \
  vcpsdk:22.10.0 delete_vcnode.py
```


## get VC node

```
docker run --rm \
  -v $(pwd):/opt/ocs-templates/HybridCloud/vcpsdk \
  --env-file=$(pwd)/config/env \
  vcpsdk:22.10.0 get_vcnode.py
```
