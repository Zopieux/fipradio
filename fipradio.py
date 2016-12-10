import aiohttp.client
import asyncio
import time
import warnings

APP_NAME = "FIP radio"
META_URL = 'http://www.fipradio.fr/livemeta/7'
ICON_NAME = 'applications-multimedia'

RADIO_URL = 'http://direct.fipradio.fr/live/fip-midfi.mp3'
PLAYER_BINARY = 'mplayer'
RADIO_PLAYER = [PLAYER_BINARY, RADIO_URL]


def subprocess(cmd, **kwargs):
    cmd, *args = cmd
    kwargs = {
        'stdin': asyncio.subprocess.DEVNULL,
        'stdout': asyncio.subprocess.DEVNULL,
        'stderr': asyncio.subprocess.DEVNULL,
        **kwargs
    }
    return asyncio.create_subprocess_exec(cmd, *args, **kwargs)


async def run_player():
    await (await subprocess(RADIO_PLAYER)).wait()


async def get_metadata():
    session = aiohttp.client.ClientSession(
        headers={'User-Agent': 'Mozilla/5.0 (fipradio.py)'})
    while True:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                data = await (await session.get(META_URL)).json()
            level = data['levels'][-1]
            uid = level['items'][level['position']]
            session.close()
            return data['steps'][uid]
        except Exception:
            time.sleep(.5)


async def music_toggle(enable):
    def is_player(line):
        player = PLAYER_BINARY.encode()
        return ((line.startswith(b'application.name') and
                 b'[%s]' % player in line) or
                (line.startswith(b'application.process.binary') and
                 line.endswith(b'"%s"' % player)))

    sub = await subprocess(['pacmd', 'list-sink-inputs'],
                           stdout=asyncio.subprocess.PIPE)
    index = None
    is_enabled = False
    async for line in sub.stdout:
        line = line.strip()
        if line.startswith(b'index: '):
            index = line.rsplit(b' ', 1)[-1]
        if line.startswith(b'muted:'):
            is_enabled = line.endswith(b'no')
        if index is not None and is_player(line):
            break
    else:
        return
    if is_enabled == enable:
        return
    await subprocess(['pacmd', 'set-sink-input-mute', index,
                      '0' if enable else '1'])
