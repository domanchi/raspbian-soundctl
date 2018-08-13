import re
import subprocess
import textwrap

from .constants import CONFIG_FILE
from .constants import SpeakerEnum


def determine_primary_device(content):
    """
    :param content: the contents of CONFIG_FILE, read into memory
    :type content: str
    """
    blocks = _get_plugin_config_block(content, 'pcm.!default')
    matches = re.search('[^#]playback.pcm [\'"](\w+)[\'"]', blocks[1])

    if not matches:
        raise FileNotFoundError(
            f'Unable to find override for default pcm in {CONFIG_FILE}'
        )

    # The speaker aliases are coded to assume that ALSA is mapped to hw:0,0
    device_ordering = determine_device_ordering()
    speaker_alias = matches.group(1)
    if speaker_alias == SpeakerEnum.GOOGLE.value:
        return device_ordering[1]
    elif speaker_alias == SpeakerEnum.AUX.value:
        return device_ordering[0]
    else:
        raise ValueError(f'Unknown speaker alias: {speaker_alias}')


def set_primary_device(content, desired_device):
    """
    :param content: see determine_primary_device
    :type content: str

    :param desired_device: the device to set primary output to
    :type desired_device: SpeakerEnum

    :returns: str, to write into CONFIG_FILE
    """
    blocks = _get_plugin_config_block(content, 'pcm.!default')
    blocks[1] = _replace_key_in_block(
        blocks[1],
        'playback.pcm',
        desired_device.value
    )

    content = ''.join(blocks).strip()

    device_ordering = determine_device_ordering()
    if device_ordering[0] != SpeakerEnum.AUX:
        content = _reorder_devices(content)

    return content


def determine_device_ordering():
    """Unfortunately, the sound card load order is non-deterministic.
    As a result, we need to see which card corresponds to `hw:0,0` and `hw:1,0`
    manually. 
    
    :returns: SpeakerEnum tuple, corresponding to order.
    """
    output = subprocess.check_output([
        'aplay',
        '-l',
    ]).decode('utf-8')

    google_sound_card_device_name = 'sndrpigooglevoi'
    card_number = int(re.search(
        r'card (\d): {}'.format(google_sound_card_device_name),
        output,
    ).group(1))

    if card_number == 0:
        return (SpeakerEnum.GOOGLE, SpeakerEnum.AUX,)
    else:
        return (SpeakerEnum.AUX, SpeakerEnum.GOOGLE,)


def _reorder_devices(content):
    blocks = _get_plugin_config_block(content, 'pcm.homespeakers')
    matches = re.search(r'slave\.pcm\s+[\'"]([^\'"]+)[\'"]', blocks[1])
    card, _ = matches.group(1)[len('hw:'):].split(',')

    new_card = 1 if card == '0' else 0
    blocks[1] = _replace_key_in_block(
        blocks[1],
        'slave.pcm',
        f'hw:{new_card},0',
    )
    blocks[1] = _replace_key_in_block(
        blocks[1],
        'control.card',
        str(new_card),
    )

    content = ''.join(blocks).strip()

    blocks = _get_plugin_config_block(content, 'pcm.googlespeaker')
    blocks[1] = _replace_key_in_block(
        blocks[1],
        'slave.pcm',
        f'hw:{card},0',
    )
    blocks[1] = _replace_key_in_block(
        blocks[1],
        'control.card',
        card,
    )

    return ''.join(blocks).strip()


def _get_plugin_config_block(content, name):
    """Only gets root plugin configs, assuming they are all left-justified.

    :type content: str
    :param content: file content

    :type name: str
    :param name: name of plugin config block

    :returns: (before, block, after,) so that you can combine them together
        again to recreate content.
    """
    output = ['', '', '',]
    writing_index = 0
    bracket_count = 0

    start_line_regex = re.compile(re.escape(name) + ' {')
    for line in content.splitlines():
        if writing_index == 1 and bracket_count == 0:
            # This goes before, because we want to capture the last bracket
            # before moving to the next writing index.
            writing_index = 2

        if start_line_regex.match(line):
            writing_index = 1

        if writing_index == 1:
            if '{' in line:
                bracket_count += 1
            elif '}' in line:
                bracket_count -= 1

        output[writing_index] += line + '\n'

    return output


def _replace_key_in_block(block, key, new_value):
    """
    :type block: str
    :param block: pluign config block

    :type key: str
    :param key: identifier in block to replace the value of

    :type new_value: str
    :param new_value: value to replace
    """
    return re.sub(
        (
            r'([\s\S]*?)'
            r'([^#]{} [\'"]?)([^\'"\n]+)([\'"]?)'
            r'([\s\S]*?)'
        ).format(key),
        r'\g<1>\g<2>{}\g<4>\g<5>'.format(new_value),
        block,
    )

