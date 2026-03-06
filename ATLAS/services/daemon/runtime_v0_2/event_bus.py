from queue import Queue

class EventBus:
    def __init__(self):
        self.queue = Queue()

    def publish(self, event_type, payload=None):
        self.queue.put({
            "type": event_type,
            "payload": payload
        })

    def get_event(self):
        if not self.queue.empty():
            return self.queue.get()
        return None