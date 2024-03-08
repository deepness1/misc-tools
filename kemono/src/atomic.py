import threading

class AtomicInt():
    def __init__(self):
        self.data = 0
        self.lock = threading.Lock()

    def fetch_add(self):
        with self.lock:
            self.data += 1
            return self.data - 1

