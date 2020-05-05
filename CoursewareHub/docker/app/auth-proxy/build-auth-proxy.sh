#!/bin/bash

OPT=$1
sudo docker build $OPT -t auth-proxy:latest ./

