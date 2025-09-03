import cv2
import pygame
import sys
import numpy as np
from config.camera import HandTracker
from game.logic import GameLogic
from config.config import WIDTH, HEIGHT


def draw_hud_top_left(screen, tracker, camera_available):
    font = pygame.font.SysFont("Arial", 20)
    hud_surface = pygame.Surface((200, 70), pygame.SRCALPHA)
    hud_surface.fill((0, 0, 0, 160))

    y = 10
    if camera_available:
        mode_text = font.render(
            f"Mode: {'Mouse' if tracker.use_mouse else 'Camera'}",
            True, (255, 255, 255)
        )
        hud_surface.blit(mode_text, (10, y))
        y += 30

        debug_text = font.render(
            f"Debug: {'ON' if tracker.debug_mode else 'OFF'}",
            True, (255, 255, 255)
        )
        hud_surface.blit(debug_text, (10, y))

    screen.blit(hud_surface, (10, 10))


def draw_controls_bottom_left(screen, tracker, camera_available):
    font = pygame.font.SysFont("Arial", 18)
    panel_surface = pygame.Surface((450, 80), pygame.SRCALPHA)
    panel_surface.fill((0, 0, 0, 160))

    controls_text = font.render(
        "M: Mode | D: Debug | R: Restart | ESC: Quit",
        True, (200, 200, 200)
    )
    panel_surface.blit(controls_text, (10, 10))

    if not tracker.use_mouse and camera_available:
        pinch_text = font.render("Pinch: Grab | Release: Drop",
                                 True, (200, 200, 200))
        panel_surface.blit(pinch_text, (10, 40))

    screen.blit(panel_surface, (10, HEIGHT - 90))


def draw_reference_panel(screen, reference_list):
    font = pygame.font.SysFont("Arial", 20, bold=True)
    small_font = pygame.font.SysFont("Arial", 18)

    width = 220
    height = 30 + 25 * len(reference_list)

    panel_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    panel_surface.fill((0, 0, 0, 160))

    title = font.render("Reference Key:", True, (255, 255, 255))
    panel_surface.blit(title, (10, 5))

    y = 35
    for i, item in enumerate(reference_list, start=1):
        text = small_font.render(f"{i}. {item}", True, (220, 220, 220))
        panel_surface.blit(text, (10, y))
        y += 25

    screen.blit(panel_surface, (WIDTH - width - 10, 10))


def draw_game_over(screen, game):
    if not game.game_over:
        return

    big_font = pygame.font.SysFont("Arial", 40, bold=True)
    small_font = pygame.font.SysFont("Arial", 24)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    if game.win:
        text = big_font.render("🎉 You Win! 🎉", True, (0, 255, 0))
    else:
        text = big_font.render("❌ Game Over ❌", True, (255, 0, 0))

    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
    screen.blit(text, text_rect)

    restart_text = small_font.render("Press R to Restart", True, (255, 255, 255))
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
    screen.blit(restart_text, restart_rect)


def draw_timer_top_center(screen, game):
    font = pygame.font.SysFont("Arial", 28, bold=True)
    panel_surface = pygame.Surface((160, 40), pygame.SRCALPHA)
    panel_surface.fill((0, 0, 0, 160))

    remaining_time = game.get_remaining_time()
    timer_text = font.render(f"⏳ {remaining_time}s", True, (255, 255, 0))
    text_rect = timer_text.get_rect(center=(panel_surface.get_width() // 2,
                                            panel_surface.get_height() // 2))
    panel_surface.blit(timer_text, text_rect)

    screen.blit(panel_surface, (WIDTH // 2 - panel_surface.get_width() // 2, 10))


def main():
    pygame.init()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera. Switching to mouse mode.")
        camera_available = False
    else:
        camera_available = True
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    tracker = HandTracker()
    game = GameLogic()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Symbol Matching Challenge")
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over:
                    game = GameLogic()
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_m and camera_available:
                    tracker.use_mouse = not tracker.use_mouse
                elif event.key == pygame.K_d and camera_available:
                    tracker.debug_mode = not tracker.debug_mode
                elif event.key == pygame.K_h and camera_available:
                    game.show_hand_tracking = not game.show_hand_tracking

        if camera_available:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Warning: Camera read failed, falling back to mouse mode.")
                camera_available = False
                tracker.use_mouse = True
                frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            else:
                frame = cv2.flip(frame, 1)
                landmarks, index_tip, thumb_tip = tracker.get_hand_landmarks(frame)

                if not game.game_over and index_tip and thumb_tip:
                    if tracker.is_pinching(index_tip, thumb_tip):
                        if game.selected_object is None:
                            game.selected_object = game.check_collision(index_tip)
                            if game.selected_object:
                                game.selected_offset = (
                                    index_tip[0] - game.selected_object["pos"][0],
                                    index_tip[1] - game.selected_object["pos"][1],
                                )
                        else:
                            new_x = index_tip[0] - game.selected_offset[0]
                            new_y = index_tip[1] - game.selected_offset[1]
                            game.update_object_position(
                                game.selected_object, (new_x, new_y)
                            )
                    else:
                        if game.selected_object:
                            slot_index = game.check_slot_collision(index_tip)
                            if slot_index is not None:
                                game.place_in_slot(game.selected_object, slot_index)
                            else:
                                game.remove_from_slot(game.selected_object)
                            game.selected_object = None
                            game.selected_offset = (0, 0)
        else:
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            cv2.putText(
                frame, "Camera not available",
                (WIDTH // 2 - 150, HEIGHT // 2 - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
            )
            cv2.putText(
                frame, "Using mouse mode only",
                (WIDTH // 2 - 150, HEIGHT // 2 + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
            )
            tracker.use_mouse = True

        game.update()
        frame_game = game.draw(frame)

        if frame_game is not None and frame_game.size > 0:
            frame = frame_game  # prefer game-drawn frame
        else:
            print("Warning: game.draw returned None, using raw frame")

        # Convert OpenCV BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Rotate & flip so Pygame displays correctly
        frame_rgb = np.flipud(np.rot90(frame_rgb))

        # Convert to Pygame surface
        frame_surface = pygame.surfarray.make_surface(frame_rgb)

        # Ensure scaling to match screen size
        frame_surface = pygame.transform.scale(frame_surface, (WIDTH, HEIGHT))

        screen.blit(frame_surface, (0, 0))

        # UI panels
        draw_hud_top_left(screen, tracker, camera_available)
        draw_timer_top_center(screen, game)
        draw_controls_bottom_left(screen, tracker, camera_available)
        draw_reference_panel(screen, game.reference_key)
        draw_game_over(screen, game)

        pygame.display.flip()
        clock.tick(60)

    if camera_available:
        cap.release()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
