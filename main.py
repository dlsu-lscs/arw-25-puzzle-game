import cv2
import pygame
import sys
import numpy as np
import os
from config.camera import HandTracker
from game.logic import GameLogic
from config.config import WIDTH, HEIGHT

# --- Asset Loading ---
def load_assets(path="assets", size=(80, 80)):
    """Loads and resizes images from the assets folder using OpenCV."""
    if not os.path.isdir(path):
        print(f"Error: Asset folder '{path}' not found. Please create it.")
        return None, None, None

    loaded_assets = {}
    ruby_files = []
    gear_files = []

    print("Loading assets...")
    for filename in os.listdir(path):
        if filename.lower().endswith(('.png', '.webp')):
            if 'ruby' in filename.lower():
                ruby_files.append(filename)
            elif any(keyword in filename.lower() for keyword in ['gear', 'nut', 'bolt', 'steel']):
                gear_files.append(filename)
            else:
                continue

            try:
                img_path = os.path.join(path, filename)
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                if img is None:
                    print(f"  - Warning: Failed to load {filename}")
                    continue
                
                if img.shape[2] == 3:
                   img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

                loaded_assets[filename] = cv2.resize(img, size)
                print(f"  - Loaded {filename}")

            except Exception as e:
                print(f"  - Error loading or processing {filename}: {e}")

    if not loaded_assets or not ruby_files or not gear_files:
        print("\nError: Could not find or load sufficient ruby/gear assets.")
        print("Please ensure the 'assets' folder contains valid .png or .webp image files with 'ruby' or 'gear' in their names.")
        return None, None, None

    print("Assets loaded successfully.\n")
    return loaded_assets, ruby_files, gear_files
# --- End Asset Loading ---


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


# --- CHANGED SECTION 1 ---
# This function is updated to draw images instead of text.
def draw_reference_panel(screen, reference_list, assets_pygame):
    font = pygame.font.SysFont("Arial", 20, bold=True) # Still use for title
    
    item_size = (60, 60) # Increased image size slightly for better visibility
    padding_x = 10
    padding_y = 5
    spacing_y = 10 # Spacing between images

    # Calculate panel height based on image size and spacing
    content_height = item_size[1] * len(reference_list) + spacing_y * (len(reference_list) - 1)
    
    width = item_size[0] + padding_x * 2 # Panel width just fits the image
    height = 30 + padding_y + content_height + padding_y # Title + padding + content

    panel_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    panel_surface.fill((0, 0, 0, 160))

    title = font.render("Key:", True, (255, 255, 255)) # Simplified title
    title_rect = title.get_rect(centerx=panel_surface.get_width() // 2)
    panel_surface.blit(title, (title_rect.left, padding_y))

    current_y = 30 + padding_y # Starting Y position for the first image

    for item_name in reference_list:
        image_surface = assets_pygame.get(item_name)
        if image_surface:
            # Scale image to desired size for the panel
            image_thumb = pygame.transform.scale(image_surface, item_size)
            # Center image horizontally in the panel
            image_x = (panel_surface.get_width() - item_size[0]) // 2
            panel_surface.blit(image_thumb, (image_x, current_y))
        
        current_y += item_size[1] + spacing_y # Move to next position

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

    assets, ruby_files, gear_files = load_assets()
    if assets is None:
        pygame.quit()
        sys.exit()
    
    # --- CHANGED SECTION 2 ---
    # Create a second dictionary of assets converted for Pygame's UI
    pygame_assets = {}
    for name, cv2_img in assets.items():
        # Convert OpenCV's BGRA format to Pygame's required RGBA
        img_rgba = cv2.cvtColor(cv2_img, cv2.COLOR_BGRA2RGBA)
        # Create a Pygame surface from the numpy array
        pygame_surface = pygame.image.frombuffer(img_rgba.tobytes(), img_rgba.shape[1::-1], "RGBA")
        pygame_assets[name] = pygame_surface

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera. Switching to mouse mode.")
        camera_available = False
    else:
        camera_available = True
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    tracker = HandTracker()
    game = GameLogic(assets, ruby_files, gear_files)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Symbol Matching Challenge")
    clock = pygame.time.Clock()

    running = True
    while running:
        # Event handling for keyboard and mouse
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game = GameLogic(assets, ruby_files, gear_files)
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_m and camera_available:
                    tracker.use_mouse = not tracker.use_mouse
                elif event.key == pygame.K_d and camera_available:
                    tracker.debug_mode = not tracker.debug_mode

        # Process camera frame and hand tracking
        if camera_available:
            ret, frame = cap.read()
            if not ret or frame is None:
                camera_available = False
                tracker.use_mouse = True
                frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            else:
                frame = cv2.flip(frame, 1)
                landmarks, index_tip, thumb_tip = tracker.get_hand_landmarks(frame)

                if not game.game_over and (index_tip or tracker.use_mouse):
                    interaction_point = pygame.mouse.get_pos() if tracker.use_mouse else index_tip
                    is_action = pygame.mouse.get_pressed()[0] if tracker.use_mouse else tracker.is_pinching(index_tip, thumb_tip)
                    
                    if is_action:
                        if game.selected_object is None:
                            game.selected_object = game.check_collision(interaction_point)
                            if game.selected_object:
                                game.selected_offset = (
                                    interaction_point[0] - game.selected_object["pos"][0],
                                    interaction_point[1] - game.selected_object["pos"][1],
                                )
                        elif game.selected_object:
                            new_x = interaction_point[0] - game.selected_offset[0]
                            new_y = interaction_point[1] - game.selected_offset[1]
                            game.update_object_position(game.selected_object, (new_x, new_y))
                    elif game.selected_object:
                        slot_index = game.check_slot_collision(interaction_point)
                        if slot_index is not None:
                            game.place_in_slot(game.selected_object, slot_index)
                        else:
                            game.remove_from_slot(game.selected_object)
                        game.selected_object = None
        else: # Handle mouse-only mode if camera fails
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            cv2.putText(frame, "Camera not available. Using mouse.", (WIDTH // 2 - 250, HEIGHT // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            tracker.use_mouse = True
            if not game.game_over:
                interaction_point = pygame.mouse.get_pos()
                is_action = pygame.mouse.get_pressed()[0]
                if is_action:
                    if game.selected_object is None:
                        game.selected_object = game.check_collision(interaction_point)
                        if game.selected_object:
                            game.selected_offset = (interaction_point[0] - game.selected_object["pos"][0],
                                                    interaction_point[1] - game.selected_object["pos"][1])
                    elif game.selected_object:
                        new_pos = (interaction_point[0] - game.selected_offset[0],
                                   interaction_point[1] - game.selected_offset[1])
                        game.update_object_position(game.selected_object, new_pos)
                elif game.selected_object:
                    slot_index = game.check_slot_collision(interaction_point)
                    if slot_index is not None:
                        game.place_in_slot(game.selected_object, slot_index)
                    else:
                        game.remove_from_slot(game.selected_object)
                    game.selected_object = None

        # Update and draw game state
        game.update()
        frame = game.draw(frame)

        # Convert OpenCV frame to Pygame surface for display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = np.rot90(frame_rgb)
        frame_surface = pygame.surfarray.make_surface(frame_rgb)
        frame_surface = pygame.transform.flip(frame_surface, True, False)

        # Draw all elements to the screen
        screen.blit(frame_surface, (0, 0))
        draw_hud_top_left(screen, tracker, camera_available)
        draw_timer_top_center(screen, game)
        draw_controls_bottom_left(screen, tracker, camera_available)
        draw_reference_panel(screen, game.reference_key, pygame_assets) # Pass the new asset dict
        draw_game_over(screen, game)

        pygame.display.flip()
        clock.tick(60)

    if camera_available:
        cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
