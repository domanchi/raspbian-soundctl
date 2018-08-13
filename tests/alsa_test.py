import textwrap
from unittest import mock

import pytest

from soundctl import alsa
from soundctl.constants import SpeakerEnum


def test_determine_device_ordering_google_first():
    content = b"""
**** List of PLAYBACK Hardware Devices ****
card 0: sndrpigooglevoi [snd_rpi_googlevoicehat_soundcar], device 0: Google voiceHAT SoundCard HiFi voicehat-hifi-0 []
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 1: ALSA [bcm2835 ALSA], device 0: bcm2835 ALSA [bcm2835 ALSA]
  Subdevices: 7/8
  Subdevice #0: subdevice #0
  Subdevice #1: subdevice #1
  Subdevice #2: subdevice #2
  Subdevice #3: subdevice #3
  Subdevice #4: subdevice #4
  Subdevice #5: subdevice #5
  Subdevice #6: subdevice #6
  Subdevice #7: subdevice #7
card 1: ALSA [bcm2835 ALSA], device 1: bcm2835 ALSA [bcm2835 IEC958/HDMI]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
"""
    with mock.patch.object(
        alsa,
        'subprocess',
    ) as mock_subprocess:
        mock_subprocess.check_output.return_value = content

        assert alsa.determine_device_ordering() == (
            SpeakerEnum.GOOGLE,
            SpeakerEnum.AUX,
        )


def test_determine_device_ordering_alsa_first():
    with mock.patch.object(
        alsa,
        'subprocess',
    ) as mock_subprocess:
        mock_subprocess.check_output.return_value = b'card 1: sndrpigooglevoi'

        assert alsa.determine_device_ordering() == (
            SpeakerEnum.AUX,
            SpeakerEnum.GOOGLE,
        )


@pytest.mark.parametrize(
    'content,expected',
    [
        # Basic case
        (
            textwrap.dedent("""
                pcm.!default {
                    playback.pcm "homespeakers" 
                }
            """)[1:-1],
            SpeakerEnum.AUX,
        ),

        # Supports comments
        (
            textwrap.dedent("""
                pcm.!default {
                    #playback.pcm "homespeakers"
                    playback.pcm "googlespeaker"
                }
            """)[1:-1],
            SpeakerEnum.GOOGLE,
        ),

        # Does not have to be first
        (
            textwrap.dedent("""
                pcm.!default {
                    type asym
                    playback.pcm "googlespeaker"
                }
            """)[1:-1],
            SpeakerEnum.GOOGLE,
        ),
    ]
)
def test_determine_primary_device(content, expected):
    with mock.patch.object(
        alsa,
        'determine_device_ordering',
        return_value=(SpeakerEnum.AUX, SpeakerEnum.GOOGLE,),
    ):
        assert alsa.determine_primary_device(content) == expected 


def test_determine_primary_device_reverse():
    content = textwrap.dedent("""
        pcm.!default {
            playback.pcm "googlespeaker"
        }
    """)[1:-1]

    with mock.patch.object(
        alsa,
        'determine_device_ordering',
        return_value=(SpeakerEnum.GOOGLE, SpeakerEnum.AUX,),
    ):
        assert alsa.determine_primary_device(content) == SpeakerEnum.AUX


@pytest.mark.parametrize(
    'content, exception',
    [
        (
            textwrap.dedent("""
                pcm.otherplugin {
                    playback.pcm "googlespeaker"
                }
            """)[1:-1],
            FileNotFoundError,
        ),
        (
            textwrap.dedent("""
                pcm.!default {
                    playback.pcm "otherspeaker"
                }
            """)[1:-1],
            ValueError,
        ),
    ],
)
def test_determine_primary_device_throws_exception(content, exception):
    with pytest.raises(exception), mock.patch.object(
        alsa,
        'determine_device_ordering',
        return_value=(SpeakerEnum.AUX, SpeakerEnum.GOOGLE,),
    ):
        alsa.determine_primary_device(content)


def test_set_primary_device_regular():
    content = textwrap.dedent("""
        pcm.googlespeaker {
            type softvol
        }

        pcm.!default {
            type asym
            #playback.pcm "googlespeaker"
            playback.pcm "homespeakers"
        }

        # some content after
    """)[1:-1]

    with mock.patch.object(
        alsa,
        'determine_device_ordering',
        return_value=(SpeakerEnum.AUX, SpeakerEnum.GOOGLE,),
    ):
        # No difference, because already on AUX.
        output = alsa.set_primary_device(content, SpeakerEnum.AUX)
        assert output == content

        output = alsa.set_primary_device(content, SpeakerEnum.GOOGLE)
        assert output == textwrap.dedent("""
            pcm.googlespeaker {
                type softvol
            }

            pcm.!default {
                type asym
                #playback.pcm "googlespeaker"
                playback.pcm "googlespeaker"
            }

            # some content after
        """)[1:-1]


def test_set_primary_device_reorders_devices_too():
    content = textwrap.dedent("""
        pcm.googlespeaker {
            slave.pcm "hw:1,0"
            control.card 1
        }

        pcm.homespeakers {
            slave.pcm "hw:0,0"
            control.card 0
        }

        pcm.!default {
            playback.pcm "homespeakers"
        }
    """)[1:-1]

    with mock.patch.object(
        alsa,
        'determine_device_ordering',
        return_value=(SpeakerEnum.GOOGLE, SpeakerEnum.AUX,),
    ):
        # Make change even though already on googlespeaker
        output = alsa.set_primary_device(content, SpeakerEnum.GOOGLE)
        assert output == textwrap.dedent("""
            pcm.googlespeaker {
                slave.pcm "hw:0,0"
                control.card 0
            }

            pcm.homespeakers {
                slave.pcm "hw:1,0"
                control.card 1
            }

            pcm.!default {
                playback.pcm "googlespeaker"
            }
        """)[1:-1]

        output = alsa.set_primary_device(content, SpeakerEnum.AUX)
        assert output == textwrap.dedent("""
            pcm.googlespeaker {
                slave.pcm "hw:0,0"
                control.card 0
            }

            pcm.homespeakers {
                slave.pcm "hw:1,0"
                control.card 1
            }

            pcm.!default {
                playback.pcm "homespeakers"
            }
        """)[1:-1]

