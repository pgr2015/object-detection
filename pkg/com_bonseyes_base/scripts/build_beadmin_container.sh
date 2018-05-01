#!/usr/bin/env bash

docker build -t be-admin \
             -f pkg/com_bonseyes_base/images/cli/Dockerfile \
             pkg/com_bonseyes_base/