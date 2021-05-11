#!/bin/bash

setup_hostname() {
  echo $(grep $PRIVATE_IP /etc/hosts | cut -f2) > /etc/hostname
}

setup_hostname
