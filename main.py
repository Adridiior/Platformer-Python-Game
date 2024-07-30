import os
import random
import pygame
from os import listdir
from os.path import isfile, join
import logging

# configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, dir3, width, height, direction=False):
    path = join("assets", dir1, dir2, dir3)
    images = [f for f in listdir(path) if isfile(join(path, f)) and f != "Collected.png"]
    logger.info(f"Loading sprite sheets from {path}: {images}")

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "PinkMan", "", 32, 32, True)
    ANIMATION_DELAY = 3
    HIT_COOLDOWN = 2000  # Cooldown di 2 secondi

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.collecting_fruit = False
        self.health = 5  # Aggiunto parametro health
        self.last_hit_time = 0  # Tempo dell'ultimo hit

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time > self.HIT_COOLDOWN:
            self.hit = True
            self.health -= 1  # Decrementa la salute
            self.last_hit_time = current_time  # Aggiorna l'ultimo tempo di hit

    def take_fruit(self):
        self.collecting_fruit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        if self.collecting_fruit:
            self.collecting_fruit = False

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)
        logger.debug(f"Player updated at ({self.rect.x}, {self.rect.y}) with mask: {self.mask}")

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3
    TOGGLE_INTERVAL = FPS * 2

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", "", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"
        self.toggle_timer = 0

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def toggle(self):
        if self.animation_name == "off":
            self.on()
        else:
            self.off()

    def loop(self):
        self.toggle_timer += 1
        if self.toggle_timer >= self.TOGGLE_INTERVAL:
            self.toggle()
            self.toggle_timer = 0

        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

    def is_on(self):
        return self.animation_name == "on"


class Fruit(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, name):
        super().__init__(x, y, width, height, name)
        self.fruit_images = load_sprite_sheets("Items", "Fruits", "", width, height)
        self.image = self.fruit_images[name][0]
        self.animation_count = 0
        self.update()
        logger.debug(f"Created fruit {name} at ({x}, {y}) with mask: {self.mask}")

    def update(self):
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)
        logger.debug(f"Updated fruit {self.name} at ({self.rect.x}, {self.rect.y}) with mask: {self.mask}")

    def loop(self):
        sprites = self.fruit_images[self.name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
            self.animation_count = 0


class Checkpoint(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "checkpoint")
        self.checkpoint_images = load_sprite_sheets("Items", "Checkpoints", "Checkpoint", width, height)
        self.image = self.checkpoint_images["Checkpoint (Flag Out) (64x64)"][0]
        self.animation_count = 0
        self.activated = False
        self.update()
        logger.debug(f"Created checkpoint at ({x}, {y}) with mask: {self.mask}")

    def update(self):
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)
        logger.debug(f"Updated checkpoint at ({self.rect.x}, {self.rect.y}) with mask: {self.mask}")

    def loop(self):
        if self.activated:
            sprites = self.checkpoint_images["Checkpoint (Flag Out) (64x64)"]
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.image = sprites[sprite_index]
            self.animation_count += 1

            if self.animation_count // self.ANIMATION_DELAY >= len(sprites):
                self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x, score):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    score_text = pygame.font.SysFont('Arial', 30).render(f'Score: {score}', True, (0, 0, 0))
    window.blit(score_text, (WIDTH - 150, 10))

    health_text = pygame.font.SysFont('Arial', 30).render(f'Health: {player.health}', True, (0, 0, 0))
    window.blit(health_text, (10, 10))

    if player.health <= 0:
        lost_text = pygame.font.SysFont('Arial', 60).render('You Lost!', True, (255, 0, 0))
        window.blit(lost_text, (WIDTH // 2 - lost_text.get_width() // 2, HEIGHT // 2 - lost_text.get_height() // 2))

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects, score, checkpoint):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire" and isinstance(obj, Fire) and obj.is_on():
            player.make_hit()
        elif obj and obj.name in ["Apple", "Bananas", "Cherries", "Kiwi", "Melon", "Orange", "Pineapple", "Strawberry"]:
            player.take_fruit()
            score += 1
            objects.remove(obj)
            break

    if pygame.sprite.collide_mask(player, checkpoint):
        checkpoint.activated = True

    return score


def find_valid_position(fruit, blocks, floor, player, max_attempts=50):
    attempts = 0
    all_blocks = blocks + floor
    while attempts < max_attempts:
        block = random.choice(all_blocks)
        x_pos = block.rect.x + (block.rect.width - fruit.rect.width) // 2
        y_pos = block.rect.y - fruit.rect.height

        # Assicurati che il frutto compaia solo a destra del player
        if x_pos <= player.rect.x:
            attempts += 1
            continue

        valid_position = True
        for obj in all_blocks:
            if obj != block and pygame.sprite.collide_rect(fruit, obj):
                valid_position = False
                break

        if valid_position:
            fruit.rect.topleft = (x_pos, y_pos)
            return True
        attempts += 1

    return False


def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("skyp.png")

    block_size = 96

    player = Player(100, 100, 50, 50)

    fire_positions = [
        (200, HEIGHT - block_size - 64, 16, 32),
        (800, HEIGHT - block_size - 64, 16, 32),
        (1200, HEIGHT - block_size - 64, 16, 32),
        (3000, HEIGHT - block_size - 64, 16, 32),
        (1800, HEIGHT - block_size - 64, 16, 32),
        (2200, HEIGHT - block_size - 64, 16, 32),
        (3500, HEIGHT - block_size - 64, 16, 32),
        (3800, HEIGHT - block_size - 64, 16, 32)
    ]

    block_positions = [
        (block_size * 13, HEIGHT - block_size * 3, block_size),
        (block_size * 9, HEIGHT - block_size * 4, block_size),
        (block_size * 4, HEIGHT - block_size * 3, block_size),
        (block_size * 7, HEIGHT - block_size * 5, block_size),
        (block_size * 3, HEIGHT - block_size * 3, block_size),
        (block_size * 10, HEIGHT - block_size * 5, block_size),
        (block_size * 14, HEIGHT - block_size * 4, block_size),
        (block_size * 16, HEIGHT - block_size * 3, block_size),
        (block_size * 17, HEIGHT - block_size * 6, block_size),
        (block_size * 20, HEIGHT - block_size * 4, block_size),
        (block_size * 22, HEIGHT - block_size * 6, block_size),
        (block_size * 25, HEIGHT - block_size * 4, block_size),
        (block_size * 28, HEIGHT - block_size * 5, block_size),
        (block_size * 30, HEIGHT - block_size * 5, block_size),
        (block_size * 32, HEIGHT - block_size * 4, block_size),
    ]

    fires = [Fire(x, y, width, height) for (x, y, width, height) in fire_positions]
    for fire in fires:
        fire.on()

    blocks = [Block(x, y, size) for (x, y, size) in block_positions]

    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 5) // block_size)]

    objects = [*floor, *blocks, *fires]

    checkpoint = Checkpoint(floor[-1].rect.x - 100, floor[-1].rect.y - 120, 64, 64)

    fruits = []
    fruit_spawn_time = 0
    score = 0

    offset_x = 0
    scroll_area_width = 200

    run = True
    level_complete = False
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        for fire in fires:
            fire.loop()
        for fruit in fruits:
            fruit.loop()
        checkpoint.loop()

        score = handle_move(player, objects, score, checkpoint)

        fruit_spawn_time += 1
        if fruit_spawn_time >= FPS * 3:
            fruit_spawn_time = 0
            fruit_name = random.choice(
                ["Apple", "Bananas", "Cherries", "Kiwi", "Melon", "Orange", "Pineapple", "Strawberry"])

            fruit = Fruit(0, 0, 32, 32, fruit_name)

            if find_valid_position(fruit, blocks, floor, player):
                logger.info(f"Placed fruit {fruit_name} at ({fruit.rect.x}, {fruit.rect.y})")
                fruits.append(fruit)
                objects.append(fruit)
            else:
                logger.warning(f"Could not place fruit {fruit_name} after 50 attempts")

        draw(window, background, bg_image, player, objects + [checkpoint], offset_x, score)

        if player.health <= 0:
            lost_text = pygame.font.SysFont('Arial', 60).render('You Lost!', True, (255, 0, 0))
            window.blit(lost_text, (WIDTH // 2 - lost_text.get_width() // 2, HEIGHT // 2 - lost_text.get_height() // 2))
            pygame.display.update()
            pygame.time.delay(3000)
            run = False

        if checkpoint.activated and not level_complete:
            level_complete = True
            complete_text = pygame.font.SysFont('Arial', 60).render('Level Complete!', True, (81, 65, 79))
            window.blit(complete_text, (WIDTH // 2 - complete_text.get_width() // 2, HEIGHT // 2 - complete_text.get_height() // 2))
            pygame.display.update()
            pygame.time.delay(2000)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
