#!/bin/sh

: ${HUB_NAME:="$UGROUP_NAME"}
: ${EXPORT_DIR:=/exported}

if [ -n "$HUB_NAME" ]; then

cat > /etc/sysconfig/coursewarehub-dirs <<EOF
EXPORT_DIR=${EXPORT_DIR}
HUB_NAME=${HUB_NAME}
EOF

touch /etc/fstab
grep -wq jupyter /etc/fstab
if [ $? != 0 ]; then
cat >> /etc/fstab <<EOF
${EXPORT_DIR}/${HUB_NAME}/jupyter /jupyter none bind 0 0
EOF
fi

grep -wq exchange /etc/fstab
if [ $? != 0 ]; then
cat >> /etc/fstab <<EOF
${EXPORT_DIR}/${HUB_NAME}/exchange /exchange none bind 0 0
EOF
fi

grep -wq share /etc/fstab
if [ $? != 0 ]; then
cat >> /etc/fstab <<EOF
${EXPORT_DIR}/${HUB_NAME}/share /share none bind 0 0
EOF
fi

else

rm -f /etc/systemd/system/multi-user.target.wants/coursewarehub-dirs.service

fi
