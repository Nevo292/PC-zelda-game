import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Game Layout Configurations
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 680  # Increased height to fit the Top HUD Bar cleanly!
HUD_HEIGHT = 80      # Height of the retro black status bar
TILE_SIZE = 50       # 16x16 assets upscaled cleanly to 50x50
FPS = 60

# Style Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
BROWN = (100, 50, 20)

# Setup Window Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("The Legend of Python: Zoria Overworld")
clock = pygame.time.Clock()

# --- SPRITESHEET EXTRACTION ENGINE ---
def get_sprite(sheet, x, y, w, h, scale=None):
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    surface.blit(sheet, (0, 0), (x, y, w, h))
    if scale:
        surface = pygame.transform.scale(surface, scale)
    return surface

try:
    # Load raw graphics
    sprites_sheet = pygame.image.load("sprites.png").convert_alpha()
    overworld_sheet = pygame.image.load("overworld.png").convert_alpha()
    
    # 1. Slicing Environment Assets (From overworld.png)
    # Sampling authentic tile segments out of the sheet rows
    grass_tile = get_sprite(overworld_sheet, 64, 0, 16, 16, (TILE_SIZE, TILE_SIZE))
    bush_tile  = get_sprite(overworld_sheet, 32, 64, 16, 16, (TILE_SIZE, TILE_SIZE))
    gate_tile  = get_sprite(overworld_sheet, 240, 144, 16, 16, (TILE_SIZE, TILE_SIZE)) # Cave entrance

    # 2. Slicing Player Walking Cycles (2 Frames per direction - Row 1)
    hero_sprites = {
        "down":  [get_sprite(sprites_sheet, 0, 0, 16, 16, (36, 36)), get_sprite(sprites_sheet, 16, 0, 16, 16, (36, 36))],
        "up":    [get_sprite(sprites_sheet, 32, 0, 16, 16, (36, 36)), get_sprite(sprites_sheet, 48, 0, 16, 16, (36, 36))],
        "right": [get_sprite(sprites_sheet, 64, 0, 16, 16, (36, 36)), get_sprite(sprites_sheet, 80, 0, 16, 16, (36, 36))]
    }
    # Create left frames automatically by mirroring the right-facing assets
    hero_sprites["left"] = [pygame.transform.flip(f, True, False) for f in hero_sprites["right"]]

    # 3. Slicing Enemy Walking Cycles (Red Octorok - Row 2)
    enemy_sprites = {
        "down":  [get_sprite(sprites_sheet, 0, 16, 16, 16, (34, 34)), get_sprite(sprites_sheet, 16, 16, 16, 16, (34, 34))],
        "up":    [get_sprite(sprites_sheet, 32, 16, 16, 16, (34, 34)), get_sprite(sprites_sheet, 48, 16, 16, 16, (34, 34))],
        "right": [get_sprite(sprites_sheet, 64, 16, 16, 16, (34, 34)), get_sprite(sprites_sheet, 80, 16, 16, 16, (34, 34))]
    }
    enemy_sprites["left"] = [pygame.transform.flip(f, True, False) for f in enemy_sprites["right"]]

    # 4. Miscellaneous Drop Items
    rupee_sprite = get_sprite(sprites_sheet, 176, 0, 16, 16, (24, 24))
    heart_sprite = get_sprite(sprites_sheet, 176, 16, 16, 16, (22, 22))

except FileNotFoundError:
    print("CRITICAL ERROR: Could not locate 'sprites.png' or 'overworld.png' in this directory.")
    pygame.quit()
    sys.exit()

# --- AUTHENTIC ZELDA SCREEN MAP ---
# 0 = Grass, 1 = Dense Trees (Solid), 2 = Secret Cave Entrance, 3 = Rare Rupee Drop
ZELDA_MAP = [
    [1,1,1,1,1,1,1,2,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,0,0,0,0,0,0,1,1,1,0,1],
    [1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1],
    [1,0,1,0,1,1,0,0,0,1,1,0,0,1,0,1],
    [1,0,0,0,1,3,0,0,0,0,1,0,0,0,0,1],
    [1,0,0,0,1,1,1,0,1,1,1,0,0,0,0,1],
    [1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1],
    [1,0,1,1,1,0,0,0,0,0,0,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 34, 34)
        self.speed = 3
        self.direction = "down"
        self.rupees_count = 0
        self.health = 3
        
        # Attack Configurations
        self.is_attacking = False
        self.attack_timer = 0
        self.sword_rect = pygame.Rect(0, 0, 0, 0)
        
        # Animation Frame Counters
        self.walk_timer = 0
        self.current_frame = 0

    def move(self, dx, dy, walls, doors):
        if self.is_attacking: return

        is_moving = (dx != 0 or dy != 0)
        if is_moving:
            self.walk_timer += 1
            if self.walk_timer >= 10:  # Toggle walking frame every 10 ticks
                self.current_frame = 1 - self.current_frame
                self.walk_timer = 0

        # Run axis movement separation for perfect tile sliding physics
        if dx != 0:
            self.rect.x += dx * self.speed
            self.handle_collision(dx, 0, walls, doors)
            self.direction = "right" if dx > 0 else "left"
        if dy != 0:
            self.rect.y += dy * self.speed
            self.handle_collision(0, dy, walls, doors)
            self.direction = "down" if dy > 0 else "up"

    def handle_collision(self, dx, dy, walls, doors):
        # Prevent leaving boundary edges of the screen
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
        if self.rect.top < HUD_HEIGHT: self.rect.top = HUD_HEIGHT
        if self.rect.bottom > SCREEN_HEIGHT: self.rect.bottom = SCREEN_HEIGHT

        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0: self.rect.right = wall.left
                if dx < 0: self.rect.left = wall.right
                if dy > 0: self.rect.bottom = wall.top
                if dy < 0: self.rect.top = wall.bottom
        for door in doors:
            if self.rect.colliderect(door):
                if self.rupees_count >= 1:
                    doors.remove(door)
                    grid_x = door.x // TILE_SIZE
                    grid_y = (door.y - HUD_HEIGHT) // TILE_SIZE
                    ZELDA_MAP[grid_y][grid_x] = 0
                    self.rupees_count -= 1
                    print("The Cave Passage Opens!")
                else:
                    if dx > 0: self.rect.right = door.left
                    if dx < 0: self.rect.left = door.right
                    if dy > 0: self.rect.bottom = door.top
                    if dy < 0: self.rect.top = door.bottom

    def attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = 12

    def update_attack(self):
        if self.is_attacking:
            self.attack_timer -= 1
            # Thrust sword positioning away from body heading
            if self.direction == "up":    self.sword_rect = pygame.Rect(self.rect.centerx - 3, self.rect.top - 22, 6, 22)
            elif self.direction == "down":  self.sword_rect = pygame.Rect(self.rect.centerx - 3, self.rect.bottom, 6, 22)
            elif self.direction == "left":  self.sword_rect = pygame.Rect(self.rect.left - 22, self.rect.centery - 3, 22, 6)
            elif self.direction == "right": self.sword_rect = pygame.Rect(self.rect.right, self.rect.centery - 3, 22, 6)
            if self.attack_timer <= 0: self.is_attacking = False

    def draw(self, surface):
        # Render the current slice frame depending on direction state
        frame = hero_sprites[self.direction][self.current_frame]
        surface.blit(frame, self.rect.topleft)
        
        if self.is_attacking:
            # Draw an 8-bit silver wooden sword element
            pygame.draw.rect(surface, WHITE, self.sword_rect)
            pygame.draw.rect(surface, BROWN, (self.sword_rect.x-1, self.sword_rect.y-1, 2, 2))

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 34, 34)
        self.direction = random.choice(["up", "down", "left", "right"])
        self.speed = 1.5
        self.ai_timer = random.randint(30, 90)
        self.walk_timer = 0
        self.current_frame = 0

    def update_ai(self, walls):
        self.ai_timer -= 1
        self.walk_timer += 1
        
        if self.walk_timer >= 12:
            self.current_frame = 1 - self.current_frame
            self.walk_timer = 0

        # Pick random new directions periodically to simulate genuine retro patrol routines
        if self.ai_timer <= 0:
            self.direction = random.choice(["up", "down", "left", "right"])
            self.ai_timer = random.randint(40, 120)

        # Apply velocity vectors
        dx, dy = 0, 0
        if self.direction == "left":  dx = -1
        elif self.direction == "right": dx = 1
        elif self.direction == "up":    dy = -1
        elif self.direction == "down":  dy = 1

        self.rect.x += dx * self.speed
        # Collide with walls horizontally
        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0: self.rect.right = wall.left
                if dx < 0: self.rect.left = wall.right
                self.direction = random.choice(["up", "down", "left", "right"])

        self.rect.y += dy * self.speed
        # Collide with walls vertically
        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0: self.rect.bottom = wall.top
                if dy < 0: self.rect.top = wall.bottom
                self.direction = random.choice(["up", "down", "left", "right"])

    def draw(self, surface):
        frame = enemy_sprites[self.direction][self.current_frame]
        surface.blit(frame, self.rect.topleft)

# --- INITIALIZE SIMULATION ENVIRONMENT ---
player = Player(100, 200)
enemies = [Enemy(300, 250), Enemy(500, 400), Enemy(250, 500)]
walls, doors = [], []
rupee_rect = None

def build_world():
    global rupee_rect
    walls.clear()
    doors.clear()
    for row_idx, row in enumerate(ZELDA_MAP):
        for col_idx, tile in enumerate(row):
            x = col_idx * TILE_SIZE
            y = (row_idx * TILE_SIZE) + HUD_HEIGHT # Add HUD offset to push playgrid downwards
            if tile == 1:   walls.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
            elif tile == 2: doors.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
            elif tile == 3: rupee_rect = pygame.Rect(x + 13, y + 13, 24, 24)

build_world()

def draw_hud(surface, player):
    """Draws a crisp, arcade-style top bar menu interface."""
    pygame.draw.rect(surface, BLACK, (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
    pygame.draw.line(surface, WHITE, (0, HUD_HEIGHT - 2), (SCREEN_WIDTH, HUD_HEIGHT - 2), 3)

    # Render Text Information Metrics
    font = pygame.font.SysFont("monospace", 20, bold=True)
    
    # Inventory Item indicators
    rupee_label = font.render(f"X {player.rupees_count:02d}", True, WHITE)
    surface.blit(rupee_sprite, (35, 28))
    surface.blit(rupee_label, (70, 30))

    # Health Layout Metrics Label
    life_label = font.render("- LIFE -", True, RED)
    surface.blit(life_label, (600, 15))
    
    # Blit matching heart count textures based on live metrics
    for i in range(3):
        if i < player.health:
            surface.blit(heart_sprite, (570 + (i * 28), 42))

# --- MAIN ENGINE LOOP ---
running = True
while running:
    clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: player.attack()

    # Read inputs
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:  dx = -1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = 1
    if keys[pygame.K_UP] or keys[pygame.K_w]:    dy = -1
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:  dy = 1

    if dx != 0 and dy != 0: dx, dy = dx * 0.707, dy * 0.707
    
    player.move(dx, dy, walls, doors)
    player.update_attack()

    # Enemy handling updates
    for enemy in enemies[:]:
        enemy.update_ai(walls)
        
        # Core Collision Interaction Resolvers
        if player.is_attacking and enemy.rect.colliderect(player.sword_rect):
            enemies.remove(enemy) # Kill enemy instantly
        elif enemy.rect.colliderect(player.rect) and not player.is_attacking:
            player.health -= 1
            # Knock back player dynamically based on direction heading
            if player.direction == "up":    player.rect.y += 45
            elif player.direction == "down":  player.rect.y -= 45
            elif player.direction == "left":  player.rect.x += 45
            elif player.direction == "right": player.rect.x -= 45
            
            if player.health <= 0:
                player.health = 3
                player.rupees_count = 0
                player.rect.topleft = (100, 200)
                build_world() # Regenerate layout completely

    # Item Grab Logic Loop
    if rupee_rect and player.rect.colliderect(rupee_rect):
        player.rupees_count += 1
        rupee_rect = None
        for r in range(len(ZELDA_MAP)):
            for c in range(len(ZELDA_MAP[r])):
                if ZELDA_MAP[r][c] == 3: ZELDA_MAP[r][c] = 0

    # RENDERING LOOP PIPELINE
    screen.fill(BLACK)

    # Render Environment Blocks with HUD vertical context shift
    for row_idx, row in enumerate(ZELDA_MAP):
        for col_idx, tile in enumerate(row):
            x = col_idx * TILE_SIZE
            y = (row_idx * TILE_SIZE) + HUD_HEIGHT
            
            # Base Ground Floor Stamp
            screen.blit(grass_tile, (x, y))
            
            if tile == 1:
                screen.blit(bush_tile, (x, y))
            elif tile == 2:
                screen.blit(gate_tile, (x, y))

    # Items & Unit Layer Stamps
    if rupee_rect:
        screen.blit(rupee_sprite, rupee_rect.topleft)
    for enemy in enemies:
        enemy.draw(screen)
        
    player.draw(screen)
    draw_hud(screen, player) # Draw HUD on top layer cleanly

    pygame.display.flip()

pygame.quit()
sys.exit()