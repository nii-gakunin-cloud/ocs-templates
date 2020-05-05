import pwd
import os
import subprocess
from copy import copy

from dockerspawner import SwarmSpawner
from docker.types import Mount
from textwrap import dedent
from traitlets import (
    Integer,
    Unicode,
    List,
    default
)
from tornado import gen

class CoursewareUserSpawner(SwarmSpawner):

    image_homedir_format_string = Unicode(
        "/home/{username}",
        config=True,
        help=dedent(
            """
            Format string for the path to the user's home directory
            inside the image.  The format string should include a
            `username` variable, which will be formatted with the
            user's username.
            """
        )
    )

    user_id = Integer(-1,
        help=dedent(
            """
            If system users are being used, then we need to know their user id
            in order to mount the home directory.
            User IDs are looked up in two ways:
            1. stored in the state dict (authenticator can write here)
            2. lookup via pwd
            """
        )
    )

    user_mounts = List(
        config=True,
        help=dedent(
            """
            Mount options for a single-user container.
            List of docker.types.Mount objects.

            - {username} is expanded to the jupyterhub username
            - {homedir} is expanded to user's home directory in a container
            """
        )
    )

    extra_user_mounts = List(
        default=[],
        config=True,
        help=dedent(
            """
            Extra mount options for a single-user container.
            List of docker.types.Mount objects.

            - {username} is expanded to the jupyterhub username
            - {homedir} is expanded to user's home directory in a container
            """
        )
    )

    admin_mounts = List(
        config=True,
        help=dedent(
            """
            Mount options for an admin's single-user container.
            List of docker.types.Mount objects.

            - {username} is expanded to the jupyterhub username
            - {homedir} is expanded to user's home directory in a container
            """
        )
    )

    extra_admin_mounts = List(
        default=[],
        config=True,
        help=dedent(
            """
            Extra mount options for an admin's single-user container.
            List of docker.types.Mount objects.

            - {username} is expanded to the jupyterhub username
            - {homedir} is expanded to user's home directory in a container
            """
        )
    )

    non_admin_mounts = List(
        config=True,
        help=dedent(
            """
            Mount options for an non-admin's single-user container.
            List of docker.types.Mount objects.

            - {username} is expanded to the jupyterhub username
            - {homedir} is expanded to user's home directory in a container
            """
        )
    )

    extra_non_admin_mounts = List(
        default=[],
        config=True,
        help=dedent(
            """
            Extra mount options for an non-admin's single-user container.
            List of docker.types.Mount objects.

            - {username} is expanded to the jupyterhub username
            - {homedir} is expanded to user's home directory in a container
            """
        )
    )

    @property
    def homedir(self):
        """
        Path to the user's home directory in the docker image.
        """
        return self.image_homedir_format_string.format(username=self.user.name)

    @property
    def mounts(self):
        mounts = []
        mounts.extend(self.user_mounts)
        mounts.extend(self.extra_user_mounts)
        if self._is_admin():
            mounts.extend(self.admin_mounts)
            mounts.extend(self.extra_admin_mounts)
        else:
            mounts.extend(self.non_admin_mounts)
            mounts.extend(self.extra_non_admin_mounts)
        mounts = [self._expand_mount_properties(m) for m in mounts]
        return sorted(mounts, key=lambda v: v['Target'])

    @default('user_mounts')
    def _default_user_mounts(self):
        mounts = []
        mounts.append(
            Mount(
                type="bind",
                target='{homedir}',
                source='/jupyter/users/{username}',
                read_only=False
            )
        )
        return mounts

    @default('admin_mounts')
    def _default_admin_mounts(self):
        mounts = []
        mounts.append(
            Mount(
                type="bind",
                target='{homedir}/admin_tools',
                source='/jupyter/admin/admin_tools',
                read_only=False
            )
        )
        for dirname in ['textbook', 'info']:
            mounts.append(
                Mount(
                    type="bind",
                    target=os.path.join('/home/jupyter', dirname),
                    source=os.path.join('/jupyter/admin', dirname),
                    read_only=False
                )
            )
        mounts.append(
            Mount(
                type="bind",
                target='/home/jupyter/workspace',
                source='/jupyter/users',
                read_only=False
            )
        )
        mounts.append(
            Mount(
                type="bind",
                target='/jupyter/admin',
                source='/jupyter/admin',
                read_only=False
            )
        )
        return mounts

    @default('non_admin_mounts')
    def _default_non_admin_mounts(self):
        mounts = []
        for dirname in ['textbook', 'tools', 'info']:
            mounts.append(
                Mount(
                    type="bind",
                    target='{homedir}/' + dirname,
                    source=os.path.join('/jupyter/admin', dirname),
                    read_only=True
                )
            )
        return mounts

    def _expand_user_properties(self, template):
        return template.format(
            homedir=self.homedir,
            username=self.user.name
        )

    def _expand_mount_properties(self, m):
        m = copy(m)
        for k, v in m.items():
            if isinstance(v, str):
                m[k] = self._expand_user_properties(v)
        return m

    def get_env(self):
        env = super(CoursewareUserSpawner, self).get_env()
        # relies on NB_USER and NB_UID handling in jupyter/docker-stacks
        env.update(dict(
            USER=self.user.name, # deprecated
            NB_USER=self.user.name,
            USER_ID=self.user_id, # deprecated
            NB_UID=self.user_id,
            HOME=self.homedir,
        ))
        # Fix 20180802
        if self._is_admin():
            env['GRANT_SUDO'] = 'yes'
        return env

    @default('user_id')
    def _default_user_id(self):
        """
        Get user_id from pwd lookup by name
        If the authenticator stores user_id in the user state dict,
        this will never be called, which is necessary if
        the system users are not on the Hub system (i.e. Hub itself is in a container).
        """
        userout = subprocess.check_output(['/get_user_id.sh', self.user.name])
        return int(userout.decode('utf-8'))

    def load_state(self, state):
        super().load_state(state)
        if 'user_id' in state:
            self.user_id = state['user_id']

    def get_state(self):
        state = super().get_state()
        if self.user_id >= 0:
            state['user_id'] = self.user_id
        return state

    @gen.coroutine
    def create_object(self):
        # systemuser image must be started as root
        # relies on NB_UID and NB_USER handling in docker-stacks
        self.extra_container_spec = {'workdir': self.homedir, 'user': '0'}

        return (yield super(CoursewareUserSpawner, self).create_object())

    def _is_admin(self):
        return self.user.admin
