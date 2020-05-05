# auth-proxy
Authentication and proxy for JupyterHub

## Build
sudo docker build -t auth-proxy:latest ./

## Run
sudo docker run -v /home/ubuntu/auth-proxy/php:/var/www/php -v /home/ubuntu/auth-proxy/nginx/certs:/etc/nginx/certs --privileged --name root_nginx_1 -p 443:443 --link root_jpydb_1:root_jpydb_1 -d auth-proxy:latest /sbin/init
