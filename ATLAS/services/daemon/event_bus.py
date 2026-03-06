import queue


class EventBus:
    def __init__(self):
        self._queue = queue.Queue()

    def publish(self, event_type, payload=None):
        event = {
            "type": event_type,
            "payload": payload
        }
        self._queue.put(event)

    def get_event(self):
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None