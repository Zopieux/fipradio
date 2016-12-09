#!/usr/bin/env python

import aiohttp.client
import asyncio
import time

"""
Plays & notifies the currently playing media at FIP radio:
http://www.fipradio.fr/player
"""

APP_NAME = "FIP radio"
META_URL = 'http://www.fipradio.fr/livemeta/7'
ICON_NAME = 'applications-multimedia'

RADIO_URL = 'http://direct.fipradio.fr/live/fip-midfi.mp3'
PLAYER_BINARY = 'mplayer'
RADIO_PLAYER = [PLAYER_BINARY, RADIO_URL]

notification = None


def subprocess(cmd, **kwargs):
    cmd, *args = cmd
    kwargs = {
        'stdin': asyncio.subprocess.DEVNULL,
        'stdout': asyncio.subprocess.DEVNULL,
        'stderr': asyncio.subprocess.DEVNULL,
        **kwargs
    }
    return asyncio.create_subprocess_exec(cmd, *args, **kwargs)


async def notify(body):
    try:
        import gi
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify
        global notification
        if not notification:
            Notify.init(APP_NAME)
            notification = Notify.Notification.new("")
            notification.props.app_name = APP_NAME
            notification.props.summary = APP_NAME
            notification.props.icon_name = ICON_NAME
            notification.set_timeout(2000)
        notification.props.body = body
        notification.show()
    except ImportError:
        await subprocess(['notify-send', '-i', ICON_NAME, APP_NAME, body])


async def run_player():
    await (await subprocess(RADIO_PLAYER)).wait()


async def get_metadata():
    while True:
        try:
            data = await (await aiohttp.client.get(META_URL)).json()
            level = data['levels'][-1]
            uid = level['items'][level['position']]
            return data['steps'][uid]
        except Exception:
            time.sleep(.1)


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
