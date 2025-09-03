import cv2
import math
import time
import random


class GameLogic:
    def __init__(self):
        self.start_time = time.time()
        self.time_limit = 60  # total time in seconds

        # Randomize reference key
        base_symbols = ["RUBY-1", "GEAR-A", "RUBY-2", "GEAR-B", "RUBY-3"]
        self.reference_key = base_symbols[:]  
        random.shuffle(self.reference_key)   # shuffle order

        self.objects = []
        self.create_objects()

        # Slots for the sequence
        self.slots = [(300 + i * 100, 500) for i in range(5)]
        self.slot_contents = [None] * 5

        # Box area for random objects
        self.box_area = (100, 100, 400, 300)

        # Tracking
        self.selected_object = None
        self.selected_offset = (0, 0)
        self.pinch_threshold = 40
        self.game_over = False
        self.win = False
        self.show_hand_tracking = True

    def create_objects(self):
        # Always include the reference key + extras
        extra_symbols = ["GEAR-C", "RUBY-4", "GEAR-D", "RUBY-5", "GEAR-E"]
        all_symbols = self.reference_key + extra_symbols
        random.shuffle(all_symbols)

        for symbol in all_symbols:
            x = random.randint(120, 460)
            y = random.randint(120, 280)
            self.objects.append({
                "symbol": symbol,
                "pos": (x, y),
                "size": 40,
                "color": self.get_color_for_symbol(symbol),
                "in_slot": False,
                "slot_index": None
            })

    def get_color_for_symbol(self, symbol):
        return (231, 76, 60) if "RUBY" in symbol else (52, 152, 219)

    def is_pinching(self, p1, p2, thresh=40):
        if p1 is None or p2 is None:
            return False
        return math.dist(p1, p2) < thresh

    def check_collision(self, point):
        """Return object under fingertip (even if in slot)."""
        for obj in self.objects:
            x, y = obj["pos"]
            size = obj["size"]
            if (abs(point[0] - x) < size and
                abs(point[1] - y) < size):
                return obj
        return None

    def check_slot_collision(self, point):
        for i, (x, y) in enumerate(self.slots):
            if (abs(point[0] - x) < 40 and abs(point[1] - y) < 40):
                return i
        return None

    def update_object_position(self, obj, new_pos):
        obj["pos"] = new_pos

    def place_in_slot(self, obj, slot_index):
        if self.slot_contents[slot_index] is not None:
            return
        obj["in_slot"] = True
        obj["slot_index"] = slot_index
        obj["pos"] = self.slots[slot_index]
        self.slot_contents[slot_index] = obj["symbol"]
        self.check_win_condition()

    def remove_from_slot(self, obj):
        if obj["in_slot"]:
            self.slot_contents[obj["slot_index"]] = None
            obj["in_slot"] = False
            obj["slot_index"] = None

    def check_win_condition(self):
        if all(self.slot_contents[i] == self.reference_key[i] for i in range(5)):
            self.win = True
            self.game_over = True

    def update(self):
        """Update game state each frame"""
        elapsed = time.time() - self.start_time
        remaining = self.time_limit - elapsed
        if remaining <= 0 and not self.win:
            self.game_over = True

    def get_remaining_time(self):
        """Return seconds left as integer (never below 0)"""
        elapsed = time.time() - self.start_time
        return max(0, int(self.time_limit - elapsed))

    def draw(self, frame):
        # Draw box area
        x, y, w, h = self.box_area
        cv2.rectangle(frame, (x, y), (x + w, y + h), (200, 200, 200), 2)

        # Draw objects
        for obj in self.objects:
            x, y = obj["pos"]
            color, size = obj["color"], obj["size"]

            if obj == self.selected_object:
                cv2.circle(frame, (x, y), size + 5, (255, 255, 0), 3)

            if "RUBY" in obj["symbol"]:
                cv2.circle(frame, (x, y), size, color, -1)
                cv2.circle(frame, (x, y), size, (255, 255, 255), 2)
            else:
                cv2.rectangle(frame, (x - size, y - size),
                              (x + size, y + size), color, -1)
                cv2.rectangle(frame, (x - size, y - size),
                              (x + size, y + size), (255, 255, 255), 2)

            text_size = cv2.getTextSize(obj["symbol"], cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.putText(frame, obj["symbol"],
                        (x - text_size[0] // 2, y + text_size[1] // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Draw slots
        for i, (x, y) in enumerate(self.slots):
            if self.slot_contents[i] is not None:
                # Highlight filled slots green
                color = (0, 255, 0)
            else:
                # Empty slots stay gray
                color = (100, 100, 100)

            cv2.rectangle(frame, (x - 40, y - 40), (x + 40, y + 40), color, 2)
            cv2.putText(frame, str(i + 1), (x - 5, y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)

        return frame
