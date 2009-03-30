#!/bin/sh

echo "updating mirror list from launchpad"
utils/get_ubuntu_mirrors_from_lp.py > data/templates/Ubuntu.mirrors
