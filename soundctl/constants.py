import os
from enum import Enum


class SpeakerEnum(Enum):
    """These values should correspond to whatever custom pcm plugin name
    used in the CONFIG_FILE.
    """
    AUX = 'homespeakers'
    GOOGLE = 'googlespeaker'


CONFIG_FILE = '/etc/asound.conf'
LOCAL_CONFIG_FILE = os.path.abspath(
    os.path.join(
        os.path.realpath(__file__),
        '../../asound.conf',
    ),
)

