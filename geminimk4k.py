import sys
import pygame

# Initialize Pygame
pygame.init()

# Game Setup & Performance Constraints
FPS = 60
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 300
HORIZON = 130 # Where the sky meets the ground

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ACS Mario Kart")
clock = pygame.time.Clock()

# Colors
COLOR_SKY = (100, 149, 237)
COLOR_GRASS_LIGHT = (34, 177, 76)
COLOR_GRASS_DARK = (26, 140, 60)
COLOR_TRACK_LIGHT = (128, 128, 128)
COLOR_TRACK_DARK = (105, 105, 105)
COLOR_MARIO_RED = (230, 25, 25)
COLOR_MARIO_BLUE = (0, 0, 200)
COLOR_TEXT = (255, 255, 255)
COLOR_TITLE = (255, 215, 0) # Gold

# Player/Kart State Variables
player_x = 0.0       
player_z = 0.0       
player_speed = 0.0   
max_speed = 3.5      
acceleration = 0.1
deceleration = 0.05
turn_speed = 0.04
max_lateral = 1.35  # Keep the kart on the drivable surface

# Track Definition (Simulated Endless Track Map)
track_segments = [0, 0, 0, 0.3, 0.5, 0.5, 0.2, 0, 0, -0.4, -0.6, -0.6, -0.3, 0, 0, 0.1, 0.2, 0]
SEGMENT_LENGTH = 100
DRAW_DISTANCE = 300
CURVE_SCALE = 0.008

def get_track_curve(z_pos):
    """Calculates the track curvature at a given distance forward."""
    segment_index = int(z_pos // SEGMENT_LENGTH) % len(track_segments)
    return track_segments[segment_index]

def render_road(player_z, player_x):
    """Draw pseudo-3D road scanlines with perspective-correct curve offsets."""
    base_idx = int(player_z // SEGMENT_LENGTH) % len(track_segments)
    base_pct = (player_z % SEGMENT_LENGTH) / SEGMENT_LENGTH
    road_dx = -track_segments[base_idx] * base_pct
    road_x = 0.0

    for screen_y in range(HORIZON, SCREEN_HEIGHT):
        depth = (screen_y - HORIZON) / (SCREEN_HEIGHT - HORIZON)
        if depth <= 0:
            continue

        road_x += road_dx
        road_dx += get_track_curve(player_z + depth * DRAW_DISTANCE) * CURVE_SCALE

        line_center_x = (SCREEN_WIDTH / 2) + road_x * depth - (player_x * SCREEN_WIDTH * depth)
        track_width = SCREEN_WIDTH * 0.4 * depth

        z_sample = player_z + depth * DRAW_DISTANCE
        is_alternate = int(z_sample * 0.1) % 2 == 0
        grass_color = COLOR_GRASS_LIGHT if is_alternate else COLOR_GRASS_DARK
        track_color = COLOR_TRACK_LIGHT if is_alternate else COLOR_TRACK_DARK

        pygame.draw.line(screen, grass_color, (0, screen_y), (SCREEN_WIDTH, screen_y))

        start_x = max(0, int(line_center_x - track_width))
        end_x = min(SCREEN_WIDTH, int(line_center_x + track_width))
        if start_x < end_x:
            pygame.draw.line(screen, track_color, (start_x, screen_y), (end_x, screen_y))

def reset_game():
    """Resets the player stats when starting a new race."""
    global player_x, player_z, player_speed
    player_x = 0.0
    player_z = 0.0
    player_speed = 0.0

# Fonts (Using Pygame's default system fonts to avoid external files)
font_large = pygame.font.SysFont("monospace", 36, bold=True)
font_medium = pygame.font.SysFont("monospace", 18, bold=True)
font_small = pygame.font.SysFont("monospace", 14, bold=True)

# Game States
STATE_MENU = 0
STATE_PLAYING = 1
current_state = STATE_MENU

# Main Game Loop
running = True
while running:
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Menu Input Handling
        if current_state == STATE_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    reset_game()
                    current_state = STATE_PLAYING

        if current_state == STATE_PLAYING and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                current_state = STATE_MENU

    # 2. State specific logic & rendering
    if current_state == STATE_MENU:
        # --- MAIN MENU RENDERING ---
        screen.fill(COLOR_SKY)
        
        # Draw a static ground layer for the menu
        pygame.draw.rect(screen, COLOR_GRASS_DARK, (0, HORIZON, SCREEN_WIDTH, SCREEN_HEIGHT - HORIZON))
        pygame.draw.polygon(screen, COLOR_TRACK_DARK, [(SCREEN_WIDTH//2 - 20, HORIZON), (SCREEN_WIDTH//2 + 20, HORIZON), (SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)])

        # Draw Title Text
        title_text = font_large.render("ACS MARIO KART", True, COLOR_TITLE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        
        # Draw Title Shadow for retro effect
        shadow_text = font_large.render("ACS MARIO KART", True, (0, 0, 0))
        screen.blit(shadow_text, (title_rect.x + 3, title_rect.y + 3))
        screen.blit(title_text, title_rect)

        # Blinking "PRESS ENTER" prompt
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            start_text = font_medium.render("PRESS ENTER TO START", True, COLOR_TEXT)
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
            
            # Shadow
            shadow_start = font_medium.render("PRESS ENTER TO START", True, (0, 0, 0))
            screen.blit(shadow_start, (start_rect.x + 2, start_rect.y + 2))
            screen.blit(start_text, start_rect)

    elif current_state == STATE_PLAYING:
        # --- GAMEPLAY LOGIC ---
        keys = pygame.key.get_pressed()
        
        # Acceleration / Braking
        if keys[pygame.K_UP]:
            player_speed = min(player_speed + acceleration, max_speed)
        elif keys[pygame.K_DOWN]:
            player_speed = max(player_speed - acceleration, -max_speed / 2)
        else:
            if player_speed > 0:
                player_speed = max(player_speed - deceleration, 0)
            elif player_speed < 0:
                player_speed = min(player_speed + deceleration, 0)

        # Steering (only while moving; reverse keeps left/right consistent)
        current_curve = get_track_curve(player_z + 20)
        if player_speed != 0:
            steer = turn_speed * (abs(player_speed) / max_speed)
            if player_speed < 0:
                steer = -steer
            if keys[pygame.K_LEFT]:
                player_x -= steer
            if keys[pygame.K_RIGHT]:
                player_x += steer

            # Centrifugal force pulling player outward on curves
            player_x -= current_curve * 0.015 * (abs(player_speed) / max_speed)

        player_x = max(-max_lateral, min(max_lateral, player_x))

        # Progress player along the course
        player_z += player_speed

        # --- PLAY RENDERING ---
        screen.fill(COLOR_SKY)
        render_road(player_z, player_x)

        # Draw Player/Kart Sprite
        kart_w, kart_h = 40, 30
        kart_x = int((SCREEN_WIDTH / 2) - (kart_w / 2))
        kart_y = SCREEN_HEIGHT - 60

        pygame.draw.ellipse(screen, COLOR_MARIO_RED, (kart_x, kart_y, kart_w, kart_h))
        pygame.draw.circle(screen, COLOR_MARIO_BLUE, (kart_x + kart_w // 2, kart_y + 8), 10)
        pygame.draw.circle(screen, COLOR_MARIO_RED, (kart_x + kart_w // 2, kart_y - 2), 6)
        pygame.draw.rect(screen, (0, 0, 0), (kart_x - 4, kart_y + 14, 8, 12))
        pygame.draw.rect(screen, (0, 0, 0), (kart_x + kart_w - 4, kart_y + 14, 8, 12))

        # UI Overlays
        speed_text = font_small.render(f"SPEED: {abs(int(player_speed * 45))} KM/H", True, COLOR_TEXT)
        # Give speed text a shadow for readability against the sky
        shadow_speed = font_small.render(f"SPEED: {abs(int(player_speed * 45))} KM/H", True, (0, 0, 0))
        screen.blit(shadow_speed, (11, 11))
        screen.blit(speed_text, (10, 10))
        
        esc_text = font_small.render("ESC to Menu", True, COLOR_TEXT)
        screen.blit(esc_text, (SCREEN_WIDTH - 100, 10))

    # Maintenance & Double Buffer Swap
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
