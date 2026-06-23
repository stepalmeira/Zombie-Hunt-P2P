class LogicalClock:
    def __init__(self):
        self.time = 0

    def tick(self):
        self.time += 1
        return self.time

    def update(self, received_time):
        self.time = max(
            self.time,
            received_time
        ) + 1

        return self.time

    def get_time(self):
        return self.time

    def reset(self):
        self.time = 0

    def __str__(self):
        return f"LogicalClock(time={self.time})"