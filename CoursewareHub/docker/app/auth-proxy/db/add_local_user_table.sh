#!/bin/bash

hubdir=$1

"$hubdir"/jhvmdir-hub/ssh-shortcut.sh -q \
sudo docker exec -i root_jpydb_1 \
psql -U postgres -d jupyterhub << EOS
CREATE SEQUENCE local_users_id_seq START 1;
CREATE TABLE local_users (
    id  integer CONSTRAINT firstkey PRIMARY KEY,
    user_name  varchar(64) UNIQUE NOT NULL,
    password  varchar(128) NOT NULL,
    mail  varchar(64) NOT NULL
);
EOS
