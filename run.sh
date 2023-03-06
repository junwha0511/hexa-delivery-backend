#!/bin/bash
# docker build -t hexa-delivery ./
docker run -it -v "`pwd`:/server"  -p 7777:7777 -d hexa-delivery
