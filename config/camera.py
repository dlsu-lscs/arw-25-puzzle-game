# config/camera.py
import cv2
import numpy as np
import pygame

try:
    import mediapipe as mp
except ImportError:
    mp = None


class HandTracker:
    """
    MediaPipe-based hand tracker.
    Exposes:
      - get_hand_landmarks(frame) -> (landmarks, index_tip(x,y), thumb_tip(x,y))
      - is_pinching(p1, p2, thresh=None) -> bool
    Also sets these fields after each call:
      - hand_detected (bool)
      - hand_bbox (x, y, w, h)
      - hand_state ("open" | "pinch" | "none")
    """

    def __init__(self):
        self.use_mouse = False
        self.debug_mode = True

        self.hand_detected = False
        self.hand_bbox = None
        self.hand_state = "none"

        # Pinch threshold is *normalized by hand size* (bbox diag)
        # Smaller number = stricter pinch.
        self.norm_pinch_threshold = 0.18

        # MediaPipe setup
        if mp is None:
            raise RuntimeError(
                "mediapipe is not installed. Run: pip install mediapipe"
            )

        self.mp_hands = mp.solutions.hands
        # Tweak these if needed for your lighting/environment
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.draw_styles = mp.solutions.drawing_styles

    def _to_xy(self, lm, w, h):
        return int(lm.x * w), int(lm.y * h)

    def get_hand_landmarks(self, frame):
        """Return landmarks and key fingertip points; draws state overlays."""
        if self.use_mouse:
            return self.get_mouse_landmarks(frame)
        else:
            return self.get_mediapipe_hand(frame)

    def get_mouse_landmarks(self, frame):
        """Mouse emulation (unchanged)."""
        mouse_pos = pygame.mouse.get_pos()
        cv2.circle(frame, mouse_pos, 20, (0, 255, 255), 2)
        cv2.putText(frame, "MOUSE MODE", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        landmarks = [mouse_pos]
        thumb_tip = (mouse_pos[0] - 15, mouse_pos[1])
        index_tip = (mouse_pos[0] + 15, mouse_pos[1])

        # Simulate "open" vs "pinch" via mouse left button
        self.hand_detected = True
        self.hand_state = "pinch" if pygame.mouse.get_pressed()[0] else "open"
        # fake bbox
        self.hand_bbox = (mouse_pos[0] - 40, mouse_pos[1] - 40, 80, 80)

        self._draw_state_box(frame)
        return landmarks, index_tip, thumb_tip

    def get_mediapipe_hand(self, frame):
        """Use MediaPipe to get landmarks and classify open/pinch state."""
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        self.hand_detected = False
        self.hand_bbox = None
        self.hand_state = "none"

        index_tip = None
        thumb_tip = None
        points_xy = []

        if results.multi_hand_landmarks:
            # Take the first detected hand
            hand_lms = results.multi_hand_landmarks[0]
            # Convert all 21 landmarks to pixel coords
            for lm in hand_lms.landmark:
                points_xy.append(self._to_xy(lm, w, h))

            self.hand_detected = True

            # Bounding box around the landmarks
            xs = [p[0] for p in points_xy]
            ys = [p[1] for p in points_xy]
            x_min, x_max = max(min(xs), 0), min(max(xs), w - 1)
            y_min, y_max = max(min(ys), 0), min(max(ys), h - 1)
            bbox_w, bbox_h = x_max - x_min, y_max - y_min
            self.hand_bbox = (x_min, y_min, bbox_w, bbox_h)

            # Key fingertip indices (MediaPipe convention)
            # Thumb tip = 4, Index tip = 8
            thumb_tip = points_xy[4]
            index_tip = points_xy[8]

            # Draw landmarks (optional)
            if self.debug_mode:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.draw_styles.get_default_hand_landmarks_style(),
                    self.draw_styles.get_default_hand_connections_style(),
                )

            # Determine openness vs pinch
            # We'll use normalized thumb-index distance (by bbox diagonal)
            diag = max(1.0, np.hypot(bbox_w, bbox_h))
            thumb_index_dist = np.hypot(
                thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1]
            ) / diag

            # Additionally estimate "openness" using average fingertip-to-palm distance
            # Palm reference: wrist (0)
            wrist = points_xy[0]
            fingertip_ids = [4, 8, 12, 16, 20]
            avg_tip_to_wrist = np.mean(
                [np.hypot(points_xy[i][0] - wrist[0], points_xy[i][1] - wrist[1])
                 for i in fingertip_ids]
            ) / diag

            # Heuristic state:
            # - "pinch" if thumb-index distance small OR bbox is very small
            # - otherwise "open" if fingertips are spread (avg distance bigger)
            is_pinch_by_dist = thumb_index_dist < self.norm_pinch_threshold
            is_small_box = diag < 120  # pixels; tweak if your camera resolution differs
            if is_pinch_by_dist or is_small_box:
                self.hand_state = "pinch"
            else:
                # require some spread to call it open; adjust 0.35–0.5 range as needed
                self.hand_state = "open" if avg_tip_to_wrist > 0.38 else "none"

            self._draw_state_box(frame)

            # Status text
            cv2.putText(
                frame,
                f"State: {self.hand_state.upper()}  "
                f"thumb-index: {thumb_index_dist:.2f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "Press M for mouse mode | D to toggle debug",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        else:
            # No hand
            cv2.putText(
                frame,
                "Show your hand to the camera",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        return points_xy, index_tip, thumb_tip

    def _draw_state_box(self, frame):
        """Draw a bbox around the hand; green when open, orange when none, red when pinch."""
        if not self.hand_bbox:
            return
        x, y, w, h = self.hand_bbox
        if self.hand_state == "open":
            color = (0, 200, 0)
            thickness = 3
        elif self.hand_state == "pinch":
            color = (0, 0, 255)
            thickness = max(1, int(min(w, h) / 20))  # thinner when very small box
        else:
            color = (0, 165, 255)  # orange-ish for "none/unknown"
            thickness = 2

        cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)

    def is_pinching(self, p1, p2, thresh=None):
        """Pinch when thumb-index distance normalized by bbox diag < threshold,
        or when we've classified state=="pinch"."""
        if self.use_mouse:
            return pygame.mouse.get_pressed()[0]

        if not self.hand_detected or self.hand_bbox is None or p1 is None or p2 is None:
            return False

        x, y, w, h = self.hand_bbox
        diag = max(1.0, np.hypot(w, h))
        dist = np.hypot(p1[0] - p2[0], p1[1] - p2[1]) / diag
        threshold = self.norm_pinch_threshold if thresh is None else thresh

        # Accept either geometric threshold OR previously assigned "pinch" state
        return dist < threshold or self.hand_state == "pinch"

