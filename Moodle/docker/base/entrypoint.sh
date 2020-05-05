#!/bin/bash

#!/bin/bash
for rc in /etc/vcp/rc.d/*.sh; do
  [ -x $rc ] && $rc
done

if [ "$#" -eq 0 -o "${1#-}" != "$1" ]; then
  set -- /usr/sbin/init "$@"
fi

exec "$@"
