#!/usr/bin/env python
""" Ansible module: glfs_status """
# Copyright: (c) 2019, Ryan Kraus (rkraus@redhat.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import shlex
from subprocess import Popen, PIPE
from ansible.module_utils.basic import AnsibleModule


def _list_strip(arr):
    '''Remove leading and trailing empty entries from list.'''
    output = []
    buffer = []
    seen_text = False
    for item in arr:
        if item.strip():
            seen_text = True
            output += buffer
            buffer = []
            output.append(item)
        elif seen_text:
            buffer.append(item)
    return output


def _exec(cmd):
    '''Execute the provided command, return stdout.'''
    proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = proc.communicate()
    if proc.returncode != 0:
        raise OSError(stderr)
    return _list_strip(stdout.split('\n'))


def _list_split(arr, delim_fun):
    '''Slice an array by specified delimeter.'''
    output = []
    buffer = []
    for item in arr:
        if delim_fun(item):
            output.append(buffer)
            buffer = []
        else:
            buffer.append(item)
    output.append(buffer)
    return output


def _offline_bricks(check, volume):
    '''Check the status of a volumes bricks.'''
    if not check: return []
    br_status = _exec('/sbin/gluster vol status ' + volume + ' detail')
    br_status = _list_split(br_status, lambda item: item.startswith('---'))[1:]
    offline = []
    for brick in br_status:
        bname = ''
        for line in brick:
            (key, value) = [val.strip() for val in line.split(':', 1)]
            if key == 'Brick':
                bname = value
            elif key == 'Online' and value != 'Y':
                offline.append(bname)
    return offline


def _offline_shd(check, volume):
    '''Check the self healing daemons.'''
    if not check: return []
    br_status = _exec('/sbin/gluster vol status ' + volume + ' shd')
    br_status = _list_split(br_status, lambda item: item.startswith('---'))[1]
    offline = []
    for shd in br_status:
        name = shd[0:44].strip()
        port = shd[44:54].strip() == 'N/A'
        online = shd[65:73].strip() == 'N'
        if port and online:
            offline.append(name)
    return offline


def _split_bricks(check, volume):
    '''Check for split brain bricks needing healing.'''
    if not check: return []
    br_status = _exec('/sbin/gluster vol heal ' + volume + ' info')
    br_status = _list_split(br_status, lambda item: not bool(item.strip()))
    split = []
    for brick in br_status:
        name = brick[0]
        count = int(brick[-1].split(':')[1].strip())
        if count > 0:
            split.append(name)
    return split


def _create_msg(volume, offline_bricks, offline_shd, split_bricks):
    '''Create a human readable message about the volume status.'''
    msg = ''
    for item in offline_bricks + offline_shd:
        msg += item + ' in ' + volume + ' is offline. '
    for item in split_bricks:
        msg += item + ' in ' + volume + ' is unhealthy. '
    ret_code = len(offline_bricks) + len(offline_shd) + len(split_bricks)
    return (msg, ret_code)


def _glfs_status(chksb, chkb):
    '''Check gluster status.'''
    volumes = _exec('/sbin/gluster vol list')
    msg = ''
    ret_code = 0
    for vol in volumes:
        offline_bricks = _offline_bricks(chkb, vol)
        offline_shd = _offline_shd(chkb, vol)
        split_bricks = _split_bricks(chksb, vol)
        (bmsg, brc) = _create_msg(vol, \
                                  offline_bricks, offline_shd, split_bricks)
        msg += bmsg
        ret_code += brc
    return (msg, ret_code)


def main():
    # define inputs
    module_args = dict(
        check_split_brain=dict(type='bool', required=False, default=True),
        check_bricks=dict(type='bool', required=False, default=True)
    )

    # connect to Ansible
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # parse input args
    check_split_brain=module.params['check_split_brain']
    check_bricks=module.params['check_bricks']

    # perform action
    (msg, rc) = _glfs_status(check_split_brain, check_bricks)

    # exit
    if rc:
        module.fail_json(msg=msg, changed=False)
    else:
        module.exit_json(changed=False)


if __name__=="__main__":
    main()