#!/bin/sh

td=$(mktemp -d)
mkdir $td/attachments

docker build . -f Dockerfile.generator -t generator_treemen

docker run -v $td:$td --rm generator_treemen 1234 $td
