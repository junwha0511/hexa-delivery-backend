#!/bin/bash
# docker build -t hexa-delivery ./
docker stop hexa-delivery
docker rm hexa-delivery
id=$(docker run -it -v "`pwd`:/server"  -p 7777:7777 -d hexa-delivery)
docker rename $id hexa-delivery
