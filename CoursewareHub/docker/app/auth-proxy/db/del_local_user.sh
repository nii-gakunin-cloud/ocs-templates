#!/bin/bash

hubdir=$1
$user_name=$2

"$hubdir"/jhvmdir-hub/ssh-shortcut.sh -q \
sudo docker exec -i root_jpydb_1 \
psql -U postgres -d jupyterhub << EOS

DELETE FROM local_users where user_name=$username;

EOS
