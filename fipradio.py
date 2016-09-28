#!/usr/bin/env python

import asyncio
import aiohttp.client
import time

"""
Plays & notifies the currently playing media at FIP radio:
http://www.fipradio.fr/player
"""

APP_NAME = "FIP radio"
META_URL = 'http://www.fipradio.fr/livemeta/7'

RADIO_URL = 'http://audio.scdn.arkena.com/11016/fip-midfi128.mp3'
RADIO_PLAYER = ['mplayer', RADIO_URL]


def subprocess(cmd, **kwargs):
    return asyncio.create_subprocess_exec(cmd[0], *cmd[1:],
                                          stdin=asyncio.subprocess.DEVNULL,
                                          stdout=asyncio.subprocess.DEVNULL,
                                          stderr=asyncio.subprocess.DEVNULL,
                                          **kwargs)


async def run_player():
    await (await subprocess(RADIO_PLAYER)).wait()


async def get_metadata():
    client = aiohttp.client.ClientSession()
    last_data = None

    notification = Notify.Notification.new("")
    notification.props.app_name = APP_NAME
    notification.props.summary = APP_NAME
    notification.props.icon_name = "applications-multimedia"
    notification.set_timeout(2000)

    while True:
        try:
            data = await (await client.get(META_URL)).json()
            level = data['levels'][-1]
            uid = level['items'][level['position']]
            data = data['steps'][uid]
        except Exception:
            time.sleep(2)
            continue

        for field in ('title', 'authors', 'anneeEditionMusique'):
            data[field] = data.get(field, '?')

        if data != last_data:
            msg = "{title} — {authors} ({anneeEditionMusique})".format(**data)
            notification.props.body = msg
            notification.show()

        last_data = data
        await asyncio.sleep(10)


if __name__ == '__main__':
    import gi

    gi.require_version('Notify', '0.7')
    from gi.repository import Notify

    Notify.init(APP_NAME)

    metadata = get_metadata()
    player = run_player()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(metadata, player))
