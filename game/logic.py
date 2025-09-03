import cv2
import math
import time
import random


class GameLogic:
    def __init__(self):
        self.start_time = time.time()
        self.time_limit = 60  # total time in seconds

        # Randomize reference key (you already had this)
        base_symbols = ["RUBY-1", "GEAR-A", "RUBY-2", "GEAR-B", "RUBY-3"]
        self.reference_key = base_symbols[:]
        random.shuffle(self.reference_key)

        # Snapping tolerance (increase for more forgiving snap)
        self.slot_snap_radius = 70

        self.objects = []
        self.create_objects()

        # Slots for the sequence (centers)
        self.slots = [(300 + i * 100, 500) for i in range(5)]
        self.slot_contents = [None] * len(self.slots)

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
                "pos": (int(x), int(y)),
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
        """
        Return the top-most object under 'point'.
        If that object is currently in a slot, detach it immediately (so slot clears).
        """
        # pick top-most by iterating reversed (last drawn/top-most last)
        for obj in reversed(self.objects):
            ox, oy = obj["pos"]
            size = obj["size"]
            if (abs(point[0] - ox) < size and abs(point[1] - oy) < size):
                # If it's in a slot, detach but keep its position (so user can drag it)
                if obj.get("in_slot"):
                    self._detach_from_slot(obj)
                return obj
        return None

    def _detach_from_slot(self, obj):
        """Internal helper: clear the slot but keep object position (for picking up)."""
        if not obj.get("in_slot"):
            return
        idx = obj.get("slot_index")
        if idx is not None and 0 <= idx < len(self.slot_contents):
            self.slot_contents[idx] = None
        obj["in_slot"] = False
        obj["slot_index"] = None
        # keep obj["pos"] as-is so the player continues dragging it

    def check_slot_collision(self, point):
        """
        Backwards-compatible: main.py passes fingertip point here on release.
        But to be more robust, if there's a selected_object, prefer using its pos
        (the object center) to decide snapping — this avoids finger offset issues.
        Returns slot index or None.
        """
        if self.selected_object is not None:
            pos_x, pos_y = self.selected_object["pos"]
        else:
            pos_x, pos_y = point

        # find nearest slot within snap radius
        closest_idx = None
        closest_dist = float("inf")
        for i, (sx, sy) in enumerate(self.slots):
            dist = math.hypot(pos_x - sx, pos_y - sy)
            if dist < closest_dist:
                closest_dist = dist
                closest_idx = i

        if closest_dist <= self.slot_snap_radius:
            return closest_idx
        return None

    def get_nearest_slot_index(self, pos):
        """Utility: returns nearest slot index within radius or None."""
        px, py = pos
        best_i = None
        best_d = float("inf")
        for i, (sx, sy) in enumerate(self.slots):
            d = math.hypot(px - sx, py - sy)
            if d < best_d:
                best_d = d
                best_i = i
        return best_i if best_d <= self.slot_snap_radius else None

    def update_object_position(self, obj, new_pos):
        obj["pos"] = (int(new_pos[0]), int(new_pos[1]))

    def place_in_slot(self, obj, slot_index):
        """
        Place object into slot if empty. Snap object's pos to slot center and update flags.
        """
        if slot_index is None:
            return
        if self.slot_contents[slot_index] is not None:
            # slot already occupied -> do nothing
            return

        sx, sy = self.slots[slot_index]
        obj["in_slot"] = True
        obj["slot_index"] = slot_index
        obj["pos"] = (int(sx), int(sy))
        self.slot_contents[slot_index] = obj["symbol"]
        self.check_win_condition()

    def remove_from_slot(self, obj, keep_pos=False):
        """
        Remove object from its slot. If keep_pos is False, respawn it randomly in box area.
        """
        if not obj.get("in_slot"):
            return
        idx = obj.get("slot_index")
        if idx is not None and 0 <= idx < len(self.slot_contents):
            self.slot_contents[idx] = None
        obj["in_slot"] = False
        obj["slot_index"] = None
        if not keep_pos:
            x = random.randint(self.box_area[0] + 20, self.box_area[0] + self.box_area[2] - 20)
            y = random.randint(self.box_area[1] + 20, self.box_area[1] + self.box_area[3] - 20)
            obj["pos"] = (int(x), int(y))

    def check_win_condition(self):
        # Compare placed symbols to reference key (length-safe)
        # A slot with None is not equal to a target symbol, so this works.
        if all(self.slot_contents[i] == self.reference_key[i] for i in range(len(self.reference_key))):
            self.win = True
            self.game_over = True

    def update(self):
        """Update game state each frame (timer)."""
        # Timer handling (non-blocking)
        elapsed = time.time() - self.start_time
        remaining = self.time_limit - elapsed
        if remaining <= 0 and not self.win:
            self.game_over = True

        # Ensure objects that are in slots remain snapped to centers
        for i, obj_sym in enumerate(self.slot_contents):
            if obj_sym is not None:
                # find object that matches this symbol and is flagged as in_slot==True and slot_index==i
                for obj in self.objects:
                    if obj.get("in_slot") and obj.get("slot_index") == i:
                        sx, sy = self.slots[i]
                        obj["pos"] = (int(sx), int(sy))
                        break

    def get_remaining_time(self):
        """Return seconds left as integer (never below 0)."""
        elapsed = time.time() - self.start_time
        return max(0, int(self.time_limit - elapsed))

    def draw(self, frame):
        # Draw box area
        x, y, w, h = self.box_area
        cv2.rectangle(frame, (x, y), (x + w, y + h), (200, 200, 200), 2)

        # Draw objects
        for obj in self.objects:
            ox, oy = int(obj["pos"][0]), int(obj["pos"][1])
            color, size = obj["color"], obj["size"]

            if obj == self.selected_object:
                cv2.circle(frame, (ox, oy), size + 5, (255, 255, 0), 3)

            if "RUBY" in obj["symbol"]:
                cv2.circle(frame, (ox, oy), size, color, -1)
                cv2.circle(frame, (ox, oy), size, (255, 255, 255), 2)
            else:
                cv2.rectangle(frame, (ox - size, oy - size),
                              (ox + size, oy + size), color, -1)
                cv2.rectangle(frame, (ox - size, oy - size),
                              (ox + size, oy + size), (255, 255, 255), 2)

            text_size = cv2.getTextSize(obj["symbol"], cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.putText(frame, obj["symbol"],
                        (ox - text_size[0] // 2, oy + text_size[1] // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Draw slots (green if filled, gray if empty)
        for i, (sx, sy) in enumerate(self.slots):
            if self.slot_contents[i] is not None:
                color = (0, 255, 0)  # green if filled
            else:
                color = (100, 100, 100)  # gray if empty
            cv2.rectangle(frame, (sx - 40, sy - 40), (sx + 40, sy + 40), color, 2)

        return frame
