import asyncio
import json

class EventBus:
    def __init__(self):
        self.subscribers = []

    async def subscribe(self):
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            self.subscribers.remove(queue)

    async def publish(self, event: dict):
        for queue in self.subscribers:
            await queue.put(event)

# Global singleton event bus
domino_event_bus = EventBus()
