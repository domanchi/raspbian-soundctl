#!/usr/bin/env python3.6
"""
This file controls which speaker output the sound comes from.
"""
import json
import subprocess
import sys
import textwrap

from soundctl import alsa
from soundctl.constants import CONFIG_FILE
from soundctl.constants import LOCAL_CONFIG_FILE
from soundctl.constants import SpeakerEnum


def print_usage():
    print(textwrap.dedent(
        """
        usage: soundctrl {edit,status,set,update}

        positional arguments:
            edit                edits the local copy of asound.conf
            status              gets the current primary sound device
            set <aux|google>    sets the primary sound device to specified value 
            update              copies the local asound.conf to CONFIG_FILE location
        """
    )[1:-1], file=sys.stderr)


def main(argv=None):
    args = parse_args(argv)

    if args[0] == 'edit':
        subprocess.call([
            'vim',
            LOCAL_CONFIG_FILE,
        ])

    elif args[0] == 'status':
        with open(CONFIG_FILE) as f:
            print(alsa.determine_primary_device(f.read()))

    elif args[0] == 'set':
        with open(CONFIG_FILE, 'r+') as f:
            content = f.read()
            new_content = alsa.set_primary_device(
                content,
                SpeakerEnum.GOOGLE if args[1].lower() == 'google' \
                    else SpeakerEnum.AUX,
            )

            if content != new_content:
                f.seek(0)
                f.write(new_content)

    elif args[0] == 'update':
        subprocess.call([
            'cp',
            LOCAL_CONFIG_FILE,
            CONFIG_FILE,
        ])

    return 0


def parse_args(argv):
    if len(argv) < 2:
        print_usage()
        sys.exit(0)

    allowed_commands = ['edit', 'status', 'set', 'update']

    if argv[1] == 'edit':
        return ('edit',)

    elif argv[1] == 'status':
        return ('status',)

    elif argv[1] == 'set':
        allowed_arguments = ['google', 'aux']

        if len(argv) < 3 or argv[2] not in allowed_arguments:
            print(
                'error: set must be called with either "google" or "aux"',
                file=sys.stderr
            )
            print_usage()
            sys.exit(1)

        return ('set', argv[2],)

    elif argv[1] == 'update':
        return ('update',)

    else:
        print(
            'error: command must one of the following:',
            json.dumps(allowed_commands),
            file=sys.stderr
        )
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main(sys.argv))

