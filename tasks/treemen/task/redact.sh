#!/bin/bash

flag="$1"

repeat() {
	for i in {1..$1}; do echo -n "R"; done
}

replace=$(repeat ${#flag})

for fname in $(ls dumps); do
  sed -e "s/$flag/$replace/g" -i "dumps/$fname"
done
