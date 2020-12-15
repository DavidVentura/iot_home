import asyncio
import logging

from functools import partial

from asyncio_mqtt import Client
from pychromecast import get_listed_chromecasts

CAST_NAME = "🤖"

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

async def sync_to_async(task):
    return await asyncio.get_event_loop().run_in_executor(None, task)


async def get_device(name):
    _c = partial(get_listed_chromecasts, friendly_names=[name])
    chromecasts, service_browser = await sync_to_async(_c)

    if not chromecasts:
        logger.error("was not able to find chromecast %s" % name)
        exit(1)

    device = chromecasts[0]
    await sync_to_async(device.wait)
    logger.info("Connected to chromecast <%s>!", device.name)
    mc = device.media_controller

    return device


class StatusListener:
    def __init__(self, name, queue):
        self.name = name
        self.queue = queue

    def new_cast_status(self, status):
        logger.info("Chromecast %s changed status, display_name: %s", self.name, status.display_name)
        logger.debug(status)
        is_running = status.app_id not in [None, 'Backdrop']
        loop.run_until_complete(self.queue.put((is_running, status.title)))

    def new_media_status(self, status):
        is_running = status.player_state == 'PLAYING'
        logger.info("Media status: %s", status.player_state)
        loop.run_until_complete(self.queue.put((is_running, status.title)))

class Events:
    def __init__(self, queue):
        self.queue = queue

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.queue.get()


async def main():
    device = await get_device(CAST_NAME)
    q = asyncio.Queue()
    listenerCast = StatusListener(device.name, q)
    device.register_status_listener(listenerCast)
    device.media_controller.register_status_listener(listenerCast)

    ev = Events(q)

    async with Client("iot.labs") as client:
        logger.info("Connected to MQTT!")
        async for is_running, title in ev:
            await client.publish(f'chromecast/{listenerCast.name}/playing', is_running)
            await client.publish(f'chromecast/{listenerCast.name}/title', title)

loop = asyncio.get_event_loop()
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
