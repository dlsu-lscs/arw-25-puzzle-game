import cv2
import math
import time
import random
import numpy as np

def overlay_image_alpha(background, overlay, pos):
    """
    Overlays a BGRA image onto a BGR image at a given position, handling boundaries.
    """
    x, y = pos
    h, w, _ = overlay.shape

    # Get the region of interest on the background
    y1, y2 = max(0, y), min(background.shape[0], y + h)
    x1, x2 = max(0, x), min(background.shape[1], x + w)

    # Get the corresponding region from the overlay
    overlay_y1, overlay_y2 = max(0, -y), min(h, background.shape[0] - y)
    overlay_x1, overlay_x2 = max(0, -x), min(w, background.shape[1] - x)

    # If the ROI is invalid, skip
    if y1 >= y2 or x1 >= x2 or overlay_y1 >= overlay_y2 or overlay_x1 >= overlay_x2:
        return

    # Extract alpha channel and color channels
    alpha = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2, 3] / 255.0
    color = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2, :3]

    # Blend the overlay with the background
    background_slice = background[y1:y2, x1:x2]
    alpha_expanded = np.expand_dims(alpha, axis=2)
    
    background[y1:y2, x1:x2] = (1.0 - alpha_expanded) * background_slice + alpha_expanded * color


class GameLogic:
    def __init__(self, assets, ruby_files, gear_files):
        self.assets = assets
        self.ruby_files = ruby_files
        self.gear_files = gear_files
        
        self.start_time = time.time()
        self.time_limit = 60

        # Snapping tolerance
        self.slot_snap_radius = 70

        # --- FIX IS HERE ---
        # Box area must be defined BEFORE creating objects that use it.
        self.box_area = (100, 100, 400, 300)

        self.objects = []
        self.reference_key = []
        self.create_objects() # Now this call will work correctly.

        # Slots for the sequence (centers)
        self.slots = [(300 + i * 100, 500) for i in range(5)]
        self.slot_contents = [None] * len(self.slots)

        # Tracking
        self.selected_object = None
        self.selected_offset = (0, 0)
        self.game_over = False
        self.win = False
        self.show_hand_tracking = True


    def create_objects(self):
        # --- Create Reference Key from available assets ---
        all_available_assets = self.ruby_files + self.gear_files
        if len(all_available_assets) < 5:
            raise ValueError("Not enough unique assets to create a 5-item reference key.")
        
        self.reference_key = random.sample(all_available_assets, 5)

        # --- Create all draggable objects (key + extras) ---
        extras_needed = 5
        # Get assets that are not in the reference key
        remaining_assets = [asset for asset in all_available_assets if asset not in self.reference_key]
        
        # Take unique extras first, then add random duplicates if needed
        extras = random.sample(remaining_assets, min(len(remaining_assets), extras_needed))
        while len(extras) < extras_needed:
            extras.append(random.choice(all_available_assets))

        all_symbols = self.reference_key + extras
        random.shuffle(all_symbols)

        for symbol in all_symbols:
            x = random.randint(self.box_area[0] + 40, self.box_area[0] + self.box_area[2] - 40)
            y = random.randint(self.box_area[1] + 40, self.box_area[1] + self.box_area[3] - 40)
            self.objects.append({
                "symbol": symbol,  # Symbol is now the filename
                "pos": (int(x), int(y)),
                "size": 40,  # Collision radius
                "in_slot": False,
                "slot_index": None
            })

    def is_pinching(self, p1, p2, thresh=40):
        if p1 is None or p2 is None:
            return False
        return math.dist(p1, p2) < thresh

    def check_collision(self, point):
        # Check from last drawn (top) to first
        for obj in reversed(self.objects):
            ox, oy = obj["pos"]
            size = obj["size"]
            if math.hypot(point[0] - ox, point[1] - oy) < size:
                if obj.get("in_slot"):
                    self._detach_from_slot(obj)
                return obj
        return None

    def _detach_from_slot(self, obj):
        if not obj.get("in_slot"):
            return
        idx = obj.get("slot_index")
        if idx is not None and 0 <= idx < len(self.slot_contents):
            self.slot_contents[idx] = None
        obj["in_slot"] = False
        obj["slot_index"] = None

    def check_slot_collision(self, point):
        pos_to_check = self.selected_object["pos"] if self.selected_object else point
        pos_x, pos_y = pos_to_check

        closest_dist = float("inf")
        closest_idx = None
        for i, (sx, sy) in enumerate(self.slots):
            dist = math.hypot(pos_x - sx, pos_y - sy)
            if dist < closest_dist:
                closest_dist = dist
                closest_idx = i

        return closest_idx if closest_dist <= self.slot_snap_radius else None

    def update_object_position(self, obj, new_pos):
        obj["pos"] = (int(new_pos[0]), int(new_pos[1]))

    def place_in_slot(self, obj, slot_index):
        if slot_index is None or self.slot_contents[slot_index] is not None:
            return

        sx, sy = self.slots[slot_index]
        obj["in_slot"] = True
        obj["slot_index"] = slot_index
        obj["pos"] = (int(sx), int(sy))
        self.slot_contents[slot_index] = obj["symbol"]
        self.check_win_condition()

    def remove_from_slot(self, obj, keep_pos=False):
        if not obj.get("in_slot"):
            return
        idx = obj.get("slot_index")
        if idx is not None and 0 <= idx < len(self.slot_contents):
            self.slot_contents[idx] = None
        obj["in_slot"] = False
        obj["slot_index"] = None
        if not keep_pos:
            x = random.randint(self.box_area[0] + 40, self.box_area[0] + self.box_area[2] - 40)
            y = random.randint(self.box_area[1] + 40, self.box_area[1] + self.box_area[3] - 40)
            obj["pos"] = (int(x), int(y))

    def check_win_condition(self):
        if all(self.slot_contents[i] == self.reference_key[i] for i in range(len(self.reference_key))):
            self.win = True
            self.game_over = True

    def update(self):
        elapsed = time.time() - self.start_time
        remaining = self.time_limit - elapsed
        if remaining <= 0 and not self.win:
            self.game_over = True

    def get_remaining_time(self):
        elapsed = time.time() - self.start_time
        return max(0, int(self.time_limit - elapsed))

    def draw(self, frame):
        # Draw box area
        x, y, w, h = self.box_area
        cv2.rectangle(frame, (x, y), (x + w, y + h), (200, 200, 200), 2)

        # Draw slots
        for i, (sx, sy) in enumerate(self.slots):
            color = (0, 255, 0) if self.slot_contents[i] is not None else (100, 100, 100)
            cv2.rectangle(frame, (sx - 40, sy - 40), (sx + 40, sy + 40), color, 3)

        # Draw objects (images)
        for obj in self.objects:
            symbol = obj["symbol"]
            image = self.assets[symbol]
            h, w, _ = image.shape
            
            # Center the image on its position
            ox, oy = int(obj["pos"][0]), int(obj["pos"][1])
            top_left_x = ox - w // 2
            top_left_y = oy - h // 2

            overlay_image_alpha(frame, image, (top_left_x, top_left_y))

            # Draw selection highlight
            if obj == self.selected_object:
                cv2.rectangle(frame, 
                              (top_left_x - 3, top_left_y - 3), 
                              (top_left_x + w + 3, top_left_y + h + 3), 
                              (255, 255, 0), 3)

        return frame
