#!/bin/bash
DCI_CS_URL="https://api.distributed-ci.io/"
DCI_CLIENT_ID=<remoteci_id>
DCI_API_SECRET=<api_secret>
# The file is used by systemd. This is the reason why we cannot
# use the common 'export FOO=bar' syntax.
export DCI_CS_URL
export DCI_CLIENT_ID
export DCI_API_SECRET
