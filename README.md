## Background

My raspberry PI has a [Google AIY Voice Kit](https://aiyprojects.withgoogle.com/voice/)
attached to it, which provides an additional sound card (for the front speaker).
However, I also have a home speaker system that connects to the PI through the AUX
cable.

Furthermore, I often find myself needing to switch between the sound cards, as output
can only come from one sound card at a time.

## Solution

Design a tool that allows me to switch between the different sound cards, by
modifying ALSA sound configs.

## Testing

With vlc, you can play sonds on command line like the following:

```
cvlc <song-file> --alsa-audio-device <plugin-name>
```

