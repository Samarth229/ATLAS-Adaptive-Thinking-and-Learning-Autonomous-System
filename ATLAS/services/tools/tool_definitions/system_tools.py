import ctypes
import re
import subprocess
from pycaw.pycaw import AudioUtilities


def _get_volume_interface():
    return AudioUtilities.GetSpeakers().EndpointVolume


def _volume_up(arg=None):
    try:
        volume = _get_volume_interface()
        current = volume.GetMasterVolumeLevelScalar()
        new_level = min(1.0, current + 0.1)
        volume.SetMasterVolumeLevelScalar(new_level, None)
        return f"Volume increased to {int(new_level * 100)} percent."
    except Exception as e:
        return f"Could not adjust volume: {e}"


def _volume_down(arg=None):
    try:
        volume = _get_volume_interface()
        current = volume.GetMasterVolumeLevelScalar()
        new_level = max(0.0, current - 0.1)
        volume.SetMasterVolumeLevelScalar(new_level, None)
        return f"Volume decreased to {int(new_level * 100)} percent."
    except Exception as e:
        return f"Could not adjust volume: {e}"


def _mute_toggle(arg=None):
    try:
        volume = _get_volume_interface()
        current_mute = volume.GetMute()
        volume.SetMute(not current_mute, None)
        return "Muted." if not current_mute else "Unmuted."
    except Exception as e:
        return f"Could not toggle mute: {e}"


def _lock_screen():
    ctypes.windll.user32.LockWorkStation()
    return "Locking the screen."


def _brightness_up():
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness(display=0)
        if isinstance(current, list):
            current = current[0]
        new_val = min(100, current + 10)
        sbc.set_brightness(new_val, display=0)
        return f"Brightness increased to {new_val} percent."
    except Exception as e:
        return f"Could not adjust brightness: {e}"


def _brightness_down():
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness(display=0)
        if isinstance(current, list):
            current = current[0]
        new_val = max(0, current - 10)
        sbc.set_brightness(new_val, display=0)
        return f"Brightness decreased to {new_val} percent."
    except Exception as e:
        return f"Could not adjust brightness: {e}"


# Shutdown and restart use confirmation_handler — set by voice_runtime at registration time
def make_shutdown_handler(stt, tts):
    def _shutdown():
        tts.speak("Are you sure you want to shut down? Say yes to confirm.")
        heard = stt.listen()
        if heard and ("yes" in heard.lower() or "confirm" in heard.lower()):
            tts.speak("Shutting down.")
            subprocess.Popen(["shutdown", "/s", "/t", "5"])
            return "Shutting down in 5 seconds."
        return "Shutdown cancelled."
    return _shutdown


def make_restart_handler(stt, tts):
    def _restart():
        tts.speak("Are you sure you want to restart? Say yes to confirm.")
        heard = stt.listen()
        if heard and ("yes" in heard.lower() or "confirm" in heard.lower()):
            tts.speak("Restarting.")
            subprocess.Popen(["shutdown", "/r", "/t", "5"])
            return "Restarting in 5 seconds."
        return "Restart cancelled."
    return _restart


def _set_volume_absolute(arg=None):
    try:
        if not arg:
            return "Please specify a percentage, like 'set volume to 50 percent'."
        match = re.search(r'\d+', arg)
        if not match:
            return "I couldn't understand the percentage."
        target = max(0, min(100, int(match.group())))
        volume = _get_volume_interface()
        volume.SetMasterVolumeLevelScalar(target / 100.0, None)
        return f"Volume set to {target} percent."
    except Exception as e:
        return f"Could not set volume: {e}"


def _set_brightness_absolute(arg=None):
    try:
        import screen_brightness_control as sbc
        if not arg:
            return "Please specify a percentage, like 'set brightness to 50 percent'."
        match = re.search(r'\d+', arg)
        if not match:
            return "I couldn't understand the percentage."
        target = max(0, min(100, int(match.group())))
        sbc.set_brightness(target)
        return f"Brightness set to {target} percent."
    except Exception as e:
        return f"Could not set brightness: {e}"


def register_all(matcher, stt_engine, tts_engine):
    # Absolute setters first — must take priority over generic "volume"/"brightness" keywords
    matcher.register([
        "set volume to", "set the volume to", "volume to",
        "change volume to", "make the volume",
    ], _set_volume_absolute, needs_arg=True)
    matcher.register([
        "set brightness to", "set the brightness to", "brightness to",
        "change brightness to",
    ], _set_brightness_absolute, needs_arg=True)
    matcher.register([
        "volume up", "turn up the volume", "turn the volume up",
        "increase volume", "increase the volume", "raise the volume",
        "raise volume", "louder", "make it louder", "make the volume louder",
        "turn it up", "vol up",
    ], _volume_up)
    matcher.register([
        "volume down", "turn down the volume", "turn the volume down",
        "decrease volume", "decrease the volume", "lower the volume",
        "lower volume", "down the volume", "reduce the volume",
        "reduce volume", "quieter", "make it quieter", "turn it down",
        "vol down",
    ], _volume_down)
    matcher.register([
        "mute", "unmute", "toggle mute", "mute it", "silence",
        "turn off the sound", "turn off sound", "no sound",
        "be quiet", "quiet please",
    ], _mute_toggle)
    matcher.register([
        "lock screen", "lock my pc", "lock the screen", "lock computer",
        "lock my computer", "lock the pc", "lock my screen",
    ], _lock_screen)
    matcher.register([
        "brightness up", "increase brightness", "brighter",
        "make it brighter", "turn up brightness", "raise brightness",
        "increase the brightness",
    ], _brightness_up)
    matcher.register([
        "brightness down", "decrease brightness", "dimmer",
        "make it dimmer", "turn down brightness", "lower brightness",
        "decrease the brightness", "reduce brightness",
    ], _brightness_down)
    matcher.register([
        "shutdown", "shut down", "shut down the pc", "shut down my pc",
        "shut down computer", "turn off the pc", "turn off my pc",
        "turn off the computer", "power off", "power down",
    ], make_shutdown_handler(stt_engine, tts_engine))
    matcher.register([
        "restart", "restart the pc", "restart my pc", "reboot",
        "restart the computer", "restart my computer", "reboot the pc",
    ], make_restart_handler(stt_engine, tts_engine))
