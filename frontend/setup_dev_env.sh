#!/bin/bash
docker run --restart always -d --name cors-anywhere -p 30080:80 yasinuslu/cors-anywhere
