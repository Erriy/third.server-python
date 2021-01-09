#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import asyncio
import aiohttp




def test(urls, concurrent=100):
    semmaphore = asyncio.Semaphore(concurrent)
    async def do_notify(id='', title='', text='', url=''):
        url = 'https://api.day.app/{}/{}/{}'.format(id, title, text)
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    pass
                    # response = await response.read()
                    # print(response.decode())
    asyncio.get_event_loop().run_until_complete(
        asyncio.wait(
            map(lambda u: asyncio.ensure_future(do_notify(*u)), urls)
        )
    )


if __name__ == "__main__":

    us = []
    id = ''
    for i in range(1):
        us.append((id,))
    test(us)