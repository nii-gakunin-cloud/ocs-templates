#!/bin/bash

hubdir=$1
user_name=$2
hashed_password=$3
mail_addr=$4

"$hubdir"/jhvmdir-hub/ssh-shortcut.sh -q \
sudo docker exec -i root_jpydb_1 \
psql -U postgres -d jupyterhub << EOS

INSERT INTO local_users VALUES(nextval(local_users_id_seq), $user_name, $hashed_password, $mail_addr); 

EOS
