import json
import asyncio
import websockets


async def hello() -> None:
    async with websockets.connect("ws://localhost:8080") as websocket:
        while True:
            await websocket.send(json.dumps({"type": "hello"}))
            print(json.loads(await websocket.recv()))


asyncio.get_event_loop().run_until_complete(hello())
