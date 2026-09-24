"""Tiny signal: lets event changes wake up every open routing WebSocket."""
import asyncio


class LiveHub:
    def __init__(self):
        self._subscribers: set[asyncio.Event] = set()

    def subscribe(self) -> asyncio.Event:
        ev = asyncio.Event()
        self._subscribers.add(ev)
        return ev

    def unsubscribe(self, ev: asyncio.Event):
        self._subscribers.discard(ev)

    def notify(self):
        """Call after any change to road events."""
        for ev in self._subscribers:
            ev.set()


hub = LiveHub()