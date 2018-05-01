#!/bin/bash

set -e

echo "Creating documentation build container"

docker build -t be-docbuilder \
             -f pkg/com_bonseyes_base/images/docbuilder/Dockerfile \
             pkg/com_bonseyes_base/images/docbuilder

echo "Execution documentation build"

docker run --rm -v $(pwd)/pkg/com_bonseyes_base/docs:/data -u $(id -u) --group-add $(id -g) be-docbuilder make html

echo "Documentation available at file://$(pwd)/pkg/com_bonseyes_base/docs/_build/html/index.html"