import pygame
import math
import random
import json
import asyncio
import socket
import threading

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
DEFAULT_PORT = 5555

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (150, 0, 255)
CYAN = (0, 255, 255)
PINK = (255, 100, 150)
DARK_BLUE = (10, 10, 40)
CREAM = (255, 248, 220)

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter 2D")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 24)


def create_nebula_background():
    """Create a nebula-style space background"""
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.fill((5, 5, 15))

    # Draw nebula clouds
    for _ in range(8):
        cx = random.randint(0, WIDTH)
        cy = random.randint(0, HEIGHT)
        for r in range(150, 10, -5):
            alpha = int(15 * (r / 150))
            color = random.choice([
                (30 + alpha, 20 + alpha, 60 + alpha),
                (20 + alpha, 30 + alpha, 50 + alpha),
                (40 + alpha, 25 + alpha, 55 + alpha),
            ])
            pygame.draw.circle(surface, color, (cx + random.randint(-20, 20),
                                                cy + random.randint(-20, 20)), r)

    # Add stars
    for _ in range(150):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(1, 2)
        brightness = random.randint(150, 255)
        pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)

    return surface


def create_planet():
    """Create a planet surface"""
    size = 60
    surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

    # Planet body - orange/brown
    pygame.draw.circle(surface, (180, 100, 60), (size, size), size)
    pygame.draw.circle(surface, (200, 120, 70), (size - 10, size - 10), size - 5)

    # Crater details
    pygame.draw.circle(surface, (150, 80, 50), (size + 15, size - 10), 12)
    pygame.draw.circle(surface, (160, 90, 55), (size - 20, size + 15), 8)
    pygame.draw.circle(surface, (140, 70, 45), (size + 5, size + 20), 10)

    return surface


class SpaceDebris:
    """Colorful space debris floating in background"""
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(-50, HEIGHT)
        self.speed = random.uniform(0.3, 1.5)
        self.size = random.randint(2, 6)
        self.color = random.choice([
            CYAN, PINK, YELLOW, PURPLE, ORANGE, (100, 200, 255), (255, 150, 200)
        ])
        self.shape = random.choice(['rect', 'diamond'])
        self.angle = random.uniform(0, math.pi * 2)
        self.rotation_speed = random.uniform(-0.05, 0.05)

    def update(self):
        self.y += self.speed
        self.angle += self.rotation_speed
        if self.y > HEIGHT + 10:
            self.y = -10
            self.x = random.randint(0, WIDTH)

    def draw(self, surface):
        if self.shape == 'rect':
            # Rotated rectangle
            points = []
            for i in range(4):
                a = self.angle + i * math.pi / 2
                px = self.x + math.cos(a) * self.size
                py = self.y + math.sin(a) * self.size
                points.append((px, py))
            pygame.draw.polygon(surface, self.color, points)
        else:
            # Diamond shape
            points = [
                (self.x, self.y - self.size),
                (self.x + self.size, self.y),
                (self.x, self.y + self.size),
                (self.x - self.size, self.y)
            ]
            pygame.draw.polygon(surface, self.color, points)


class Star:
    """Background star for parallax effect"""
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.2, 0.8)
        self.size = random.randint(1, 2)
        brightness = random.randint(150, 255)
        self.color = (brightness, brightness, brightness)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


class Particle:
    """Explosion particle effect"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = random.randint(15, 30)
        self.max_life = self.life
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        size = int(self.size * (self.life / self.max_life))
        if size > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)


class Bullet:
    """Player bullet"""
    def __init__(self, x, y, angle, damage=10, speed=12, color=CYAN, owner=0):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.color = color
        self.owner = owner
        self.radius = 4

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        return 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius + 2)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)


class EnemyBullet:
    """Enemy bullet"""
    def __init__(self, x, y, angle, speed=6, damage=10):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.radius = 5

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        return 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y)), self.radius - 2)


class Player:
    """Player ship - cream/white triangular spacecraft"""
    def __init__(self, x, y, player_num=0):
        self.x = x
        self.y = y
        self.player_num = player_num
        self.angle = -math.pi / 2
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.damage = 10
        self.fire_rate = 200
        self.last_shot = 0
        self.score = 0
        self.radius = 20

        # Ship colors - cream/white main color
        self.colors = [CREAM, (200, 255, 200), (255, 200, 150), (200, 200, 255)]
        self.color = self.colors[player_num % 4]

        # Power-up effects
        self.shield_active = False
        self.shield_timer = 0
        self.rapid_fire = False
        self.rapid_fire_timer = 0
        self.spread_shot = False
        self.spread_shot_timer = 0
        self.damage_boost = False
        self.damage_boost_timer = 0

        # Upgrades
        self.speed_level = 0
        self.damage_level = 0
        self.fire_rate_level = 0
        self.health_level = 0

    def update(self, keys, mouse_pos=None, local_player_num=0):
        dx, dy = 0, 0
        aim_dx, aim_dy = 0, 0

        if local_player_num == 0:
            if keys[pygame.K_w]: dy -= 1
            if keys[pygame.K_s]: dy += 1
            if keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_d]: dx += 1
            if mouse_pos:
                aim_dx = mouse_pos[0] - self.x
                aim_dy = mouse_pos[1] - self.y
        elif local_player_num == 1:
            if keys[pygame.K_i]: dy -= 1
            if keys[pygame.K_k]: dy += 1
            if keys[pygame.K_j]: dx -= 1
            if keys[pygame.K_l]: dx += 1
            if keys[pygame.K_UP]: aim_dy -= 1
            if keys[pygame.K_DOWN]: aim_dy += 1
            if keys[pygame.K_LEFT]: aim_dx -= 1
            if keys[pygame.K_RIGHT]: aim_dx += 1
        elif local_player_num == 2:
            if keys[pygame.K_t]: dy -= 1
            if keys[pygame.K_g]: dy += 1
            if keys[pygame.K_f]: dx -= 1
            if keys[pygame.K_h]: dx += 1
            if keys[pygame.K_KP8]: aim_dy -= 1
            if keys[pygame.K_KP2]: aim_dy += 1
            if keys[pygame.K_KP4]: aim_dx -= 1
            if keys[pygame.K_KP6]: aim_dx += 1

        if dx != 0 or dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length

        actual_speed = self.speed + self.speed_level * 0.5
        self.x += dx * actual_speed
        self.y += dy * actual_speed

        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

        if aim_dx != 0 or aim_dy != 0:
            self.angle = math.atan2(aim_dy, aim_dx)

        current_time = pygame.time.get_ticks()
        if self.shield_active and current_time > self.shield_timer:
            self.shield_active = False
        if self.rapid_fire and current_time > self.rapid_fire_timer:
            self.rapid_fire = False
        if self.spread_shot and current_time > self.spread_shot_timer:
            self.spread_shot = False
        if self.damage_boost and current_time > self.damage_boost_timer:
            self.damage_boost = False

    def shoot(self):
        current_time = pygame.time.get_ticks()
        actual_fire_rate = self.fire_rate - self.fire_rate_level * 20
        if self.rapid_fire:
            actual_fire_rate //= 2

        if current_time - self.last_shot >= actual_fire_rate:
            self.last_shot = current_time
            bullets = []
            damage = self.damage + self.damage_level * 5
            if self.damage_boost:
                damage *= 2

            if self.spread_shot:
                for offset in [-0.3, 0, 0.3]:
                    bullets.append(Bullet(self.x, self.y, self.angle + offset, damage, 12, CYAN, self.player_num))
            else:
                bullets.append(Bullet(self.x, self.y, self.angle, damage, 12, CYAN, self.player_num))
            return bullets
        return []

    def take_damage(self, amount):
        if not self.shield_active:
            self.health -= amount
            return True
        return False

    def apply_powerup(self, powerup_type):
        current_time = pygame.time.get_ticks()
        duration = 8000

        if powerup_type == "shield":
            self.shield_active = True
            self.shield_timer = current_time + duration
        elif powerup_type == "rapid_fire":
            self.rapid_fire = True
            self.rapid_fire_timer = current_time + duration
        elif powerup_type == "spread_shot":
            self.spread_shot = True
            self.spread_shot_timer = current_time + duration
        elif powerup_type == "damage_boost":
            self.damage_boost = True
            self.damage_boost_timer = current_time + duration
        elif powerup_type == "health":
            self.health = min(self.max_health, self.health + 30)

    def draw(self, surface):
        """Draw the detailed pixel-art style spacecraft"""
        cx, cy = int(self.x), int(self.y)

        # Colors for the ship
        GRAY_LIGHT = (200, 200, 210)
        GRAY_MED = (160, 160, 170)
        GRAY_DARK = (120, 120, 130)
        GRAY_DARKER = (90, 90, 100)
        GOLD = (220, 180, 50)
        GOLD_DARK = (180, 140, 30)
        BLUE_COCKPIT = (80, 140, 220)
        BLUE_COCKPIT_LIGHT = (120, 180, 255)
        RED_ACCENT = (200, 60, 60)

        # Ship is pointing up by default, rotate all points by self.angle + pi/2
        a = self.angle + math.pi / 2

        def rotate_point(px, py):
            """Rotate point around center"""
            cos_a = math.cos(a)
            sin_a = math.sin(a)
            return (cx + px * cos_a - py * sin_a, cy + px * sin_a + py * cos_a)

        # Main body - center fuselage (gray metallic)
        body_points = [
            rotate_point(0, -28),   # Nose tip
            rotate_point(-4, -20),
            rotate_point(-6, -10),
            rotate_point(-5, 5),
            rotate_point(-3, 18),
            rotate_point(0, 22),    # Bottom center
            rotate_point(3, 18),
            rotate_point(5, 5),
            rotate_point(6, -10),
            rotate_point(4, -20),
        ]
        pygame.draw.polygon(surface, GRAY_LIGHT, body_points)

        # Body shading - left side darker
        body_left = [
            rotate_point(0, -28),
            rotate_point(-4, -20),
            rotate_point(-6, -10),
            rotate_point(-5, 5),
            rotate_point(-3, 18),
            rotate_point(0, 18),
            rotate_point(0, -28),
        ]
        pygame.draw.polygon(surface, GRAY_MED, body_left)

        # Left wing - outer
        left_wing_outer = [
            rotate_point(-6, -5),
            rotate_point(-22, 8),
            rotate_point(-28, 18),
            rotate_point(-24, 22),
            rotate_point(-18, 20),
            rotate_point(-8, 12),
            rotate_point(-5, 5),
        ]
        pygame.draw.polygon(surface, GRAY_DARK, left_wing_outer)

        # Right wing - outer
        right_wing_outer = [
            rotate_point(6, -5),
            rotate_point(22, 8),
            rotate_point(28, 18),
            rotate_point(24, 22),
            rotate_point(18, 20),
            rotate_point(8, 12),
            rotate_point(5, 5),
        ]
        pygame.draw.polygon(surface, GRAY_MED, right_wing_outer)

        # Left wing inner layer
        left_wing_inner = [
            rotate_point(-5, 0),
            rotate_point(-16, 10),
            rotate_point(-20, 18),
            rotate_point(-14, 16),
            rotate_point(-6, 10),
        ]
        pygame.draw.polygon(surface, GRAY_DARKER, left_wing_inner)

        # Right wing inner layer
        right_wing_inner = [
            rotate_point(5, 0),
            rotate_point(16, 10),
            rotate_point(20, 18),
            rotate_point(14, 16),
            rotate_point(6, 10),
        ]
        pygame.draw.polygon(surface, GRAY_DARK, right_wing_inner)

        # Gold accents on wings
        left_gold = [
            rotate_point(-18, 14),
            rotate_point(-24, 20),
            rotate_point(-20, 20),
            rotate_point(-15, 16),
        ]
        pygame.draw.polygon(surface, GOLD, left_gold)

        right_gold = [
            rotate_point(18, 14),
            rotate_point(24, 20),
            rotate_point(20, 20),
            rotate_point(15, 16),
        ]
        pygame.draw.polygon(surface, GOLD, right_gold)

        # Red accent on left wing tip
        red_accent = [
            rotate_point(-26, 16),
            rotate_point(-28, 18),
            rotate_point(-26, 20),
            rotate_point(-24, 18),
        ]
        pygame.draw.polygon(surface, RED_ACCENT, red_accent)

        # Engine housings (yellow/gold tubes on sides)
        left_engine = [
            rotate_point(-8, 8),
            rotate_point(-10, 10),
            rotate_point(-10, 20),
            rotate_point(-8, 22),
            rotate_point(-6, 20),
            rotate_point(-6, 10),
        ]
        pygame.draw.polygon(surface, GOLD_DARK, left_engine)

        right_engine = [
            rotate_point(8, 8),
            rotate_point(10, 10),
            rotate_point(10, 20),
            rotate_point(8, 22),
            rotate_point(6, 20),
            rotate_point(6, 10),
        ]
        pygame.draw.polygon(surface, GOLD, right_engine)

        # Main engine exhaust (yellow at bottom center)
        engine_exhaust = [
            rotate_point(-4, 18),
            rotate_point(-3, 26),
            rotate_point(0, 28),
            rotate_point(3, 26),
            rotate_point(4, 18),
        ]
        pygame.draw.polygon(surface, GOLD, engine_exhaust)

        # Engine glow
        glow_pos = rotate_point(0, 24)
        pygame.draw.circle(surface, (255, 200, 100), (int(glow_pos[0]), int(glow_pos[1])), 4)
        pygame.draw.circle(surface, (255, 255, 200), (int(glow_pos[0]), int(glow_pos[1])), 2)

        # Cockpit (blue oval)
        cockpit_pos = rotate_point(0, -12)
        # Draw elongated cockpit
        cockpit_points = []
        for i in range(12):
            angle_c = i * math.pi * 2 / 12
            px = math.cos(angle_c) * 4
            py = math.sin(angle_c) * 8
            cockpit_points.append(rotate_point(px, -12 + py))
        pygame.draw.polygon(surface, BLUE_COCKPIT, cockpit_points)

        # Cockpit highlight
        highlight_points = []
        for i in range(8):
            angle_c = i * math.pi * 2 / 8
            px = math.cos(angle_c) * 2
            py = math.sin(angle_c) * 5
            highlight_points.append(rotate_point(px - 1, -14 + py))
        pygame.draw.polygon(surface, BLUE_COCKPIT_LIGHT, highlight_points)

        # Shield effect
        if self.shield_active:
            pygame.draw.circle(surface, (100, 200, 255), (cx, cy), self.radius + 12, 3)

        # Power-up indicators
        indicators = []
        if self.rapid_fire:
            indicators.append(("R", YELLOW))
        if self.spread_shot:
            indicators.append(("S", PURPLE))
        if self.damage_boost:
            indicators.append(("D", RED))

        for i, (text, color) in enumerate(indicators):
            x = cx - 10 + i * 15
            txt = small_font.render(text, True, color)
            surface.blit(txt, (x, cy - self.radius - 20))


class Enemy:
    """Robot-style enemy"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 30
        self.max_health = 30
        self.damage = 10
        self.speed = 2
        self.radius = 18
        self.color = (200, 50, 80)  # Red-pink robot
        self.points = 100
        self.last_shot = 0
        self.fire_rate = 2000
        self.angle = 0

    def update(self, players):
        if not players:
            return True

        nearest = min(players, key=lambda p: math.hypot(p.x - self.x, p.y - self.y))
        angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
        self.x += math.cos(angle) * self.speed
        self.y += math.sin(angle) * self.speed
        self.angle += 0.05
        return True

    def try_shoot(self, players):
        if not players:
            return None

        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot >= self.fire_rate:
            nearest = min(players, key=lambda p: math.hypot(p.x - self.x, p.y - self.y))
            dist = math.hypot(nearest.x - self.x, nearest.y - self.y)
            if dist < 400:
                self.last_shot = current_time
                angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
                return EnemyBullet(self.x, self.y, angle, 5, self.damage)
        return None

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)

        # Robot body - hexagonal shape
        points = []
        for i in range(6):
            a = self.angle + i * math.pi / 3
            px = cx + math.cos(a) * self.radius
            py = cy + math.sin(a) * self.radius
            points.append((px, py))
        pygame.draw.polygon(surface, self.color, points)

        # Inner body
        inner_points = []
        for i in range(6):
            a = self.angle + i * math.pi / 3
            px = cx + math.cos(a) * (self.radius - 5)
            py = cy + math.sin(a) * (self.radius - 5)
            inner_points.append((px, py))
        pygame.draw.polygon(surface, (100, 30, 50), inner_points)

        # Robot eye
        pygame.draw.circle(surface, (255, 50, 50), (cx, cy), 6)
        pygame.draw.circle(surface, WHITE, (cx, cy), 3)

        # Health bar
        if self.health < self.max_health:
            bar_width = self.radius * 2
            bar_height = 4
            health_pct = self.health / self.max_health
            pygame.draw.rect(surface, RED, (cx - bar_width//2, cy - self.radius - 10, bar_width, bar_height))
            pygame.draw.rect(surface, GREEN, (cx - bar_width//2, cy - self.radius - 10, bar_width * health_pct, bar_height))


class FastEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 20
        self.max_health = 20
        self.speed = 4
        self.radius = 14
        self.color = (255, 200, 50)  # Yellow
        self.points = 75
        self.fire_rate = 3000


class HeavyEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 80
        self.max_health = 80
        self.speed = 1
        self.radius = 28
        self.color = (150, 50, 200)  # Purple
        self.points = 200
        self.damage = 20
        self.fire_rate = 1500


class SniperEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 25
        self.max_health = 25
        self.speed = 1.5
        self.radius = 16
        self.color = (255, 150, 50)  # Orange
        self.points = 150
        self.fire_rate = 1200
        self.preferred_distance = 300

    def update(self, players):
        if not players:
            return True

        nearest = min(players, key=lambda p: math.hypot(p.x - self.x, p.y - self.y))
        dist = math.hypot(nearest.x - self.x, nearest.y - self.y)
        angle = math.atan2(nearest.y - self.y, nearest.x - self.x)

        if dist < self.preferred_distance - 50:
            self.x -= math.cos(angle) * self.speed
            self.y -= math.sin(angle) * self.speed
        elif dist > self.preferred_distance + 50:
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
        self.angle += 0.08
        return True


class Boss:
    """Boss enemy"""
    def __init__(self, wave):
        self.x = WIDTH // 2
        self.y = -100
        self.target_y = 100
        self.health = 500 + wave * 100
        self.max_health = self.health
        self.radius = 60
        self.speed = 1
        self.phase = 0
        self.last_shot = 0
        self.points = 1000 + wave * 200
        self.entering = True
        self.angle = 0
        self.attack_pattern = 0
        self.pattern_timer = 0

    def update(self, players):
        if self.entering:
            self.y += 2
            if self.y >= self.target_y:
                self.entering = False
            return True

        self.angle += 0.02
        self.x = WIDTH // 2 + math.sin(self.angle) * 200

        current_time = pygame.time.get_ticks()
        if current_time - self.pattern_timer > 5000:
            self.attack_pattern = (self.attack_pattern + 1) % 3
            self.pattern_timer = current_time

        return True

    def try_shoot(self, players):
        if self.entering or not players:
            return []

        current_time = pygame.time.get_ticks()
        bullets = []

        if self.attack_pattern == 0:
            if current_time - self.last_shot >= 300:
                self.last_shot = current_time
                for i in range(5):
                    angle = math.pi / 2 + (i - 2) * 0.3
                    bullets.append(EnemyBullet(self.x, self.y + self.radius, angle, 4, 15))
        elif self.attack_pattern == 1:
            if current_time - self.last_shot >= 500:
                self.last_shot = current_time
                for p in players:
                    angle = math.atan2(p.y - self.y, p.x - self.x)
                    bullets.append(EnemyBullet(self.x, self.y + self.radius, angle, 6, 20))
        else:
            if current_time - self.last_shot >= 100:
                self.last_shot = current_time
                angle = self.angle * 5
                bullets.append(EnemyBullet(self.x, self.y + self.radius, angle, 3, 10))

        return bullets

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)

        # Boss body - large robot
        pygame.draw.circle(surface, (200, 50, 100), (cx, cy), self.radius)
        pygame.draw.circle(surface, (150, 30, 70), (cx, cy), self.radius - 10)

        # Rotating outer ring
        for i in range(8):
            a = self.angle + i * math.pi / 4
            px = cx + math.cos(a) * (self.radius - 5)
            py = cy + math.sin(a) * (self.radius - 5)
            pygame.draw.circle(surface, CYAN, (int(px), int(py)), 8)

        # Eyes
        pygame.draw.circle(surface, WHITE, (cx - 20, cy - 10), 15)
        pygame.draw.circle(surface, WHITE, (cx + 20, cy - 10), 15)
        pygame.draw.circle(surface, RED, (cx - 20, cy - 10), 8)
        pygame.draw.circle(surface, RED, (cx + 20, cy - 10), 8)

        # Health bar
        bar_width = 200
        bar_height = 20
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = 20
        health_pct = self.health / self.max_health

        pygame.draw.rect(surface, (50, 50, 50), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * health_pct, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 2)

        boss_text = font.render("BOSS", True, WHITE)
        surface.blit(boss_text, (WIDTH // 2 - boss_text.get_width() // 2, bar_y + bar_height + 5))


class PowerUp:
    """Collectible power-up"""
    def __init__(self, x, y, powerup_type=None):
        self.x = x
        self.y = y
        self.radius = 15
        self.types = ["shield", "rapid_fire", "spread_shot", "damage_boost", "health"]
        self.type = powerup_type or random.choice(self.types)
        self.colors = {
            "shield": CYAN,
            "rapid_fire": YELLOW,
            "spread_shot": PURPLE,
            "damage_boost": RED,
            "health": GREEN
        }
        self.color = self.colors[self.type]
        self.angle = 0
        self.lifetime = 10000
        self.spawn_time = pygame.time.get_ticks()

    def update(self):
        self.angle += 0.1
        self.y += 0.5
        return pygame.time.get_ticks() - self.spawn_time < self.lifetime and self.y < HEIGHT

    def draw(self, surface):
        pulse = abs(math.sin(self.angle)) * 5
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius + pulse))
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)

        icons = {"shield": "S", "rapid_fire": "R", "spread_shot": "W", "damage_boost": "D", "health": "+"}
        icon = small_font.render(icons[self.type], True, WHITE)
        surface.blit(icon, (self.x - icon.get_width() // 2, self.y - icon.get_height() // 2))


class NetworkManager:
    """Handles online multiplayer networking"""
    def __init__(self):
        self.socket = None
        self.connected = False
        self.is_host = False
        self.clients = []
        self.messages = []
        self.lock = threading.Lock()

    def host_game(self, port=DEFAULT_PORT):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', port))
            self.socket.listen(3)
            self.socket.setblocking(False)
            self.is_host = True
            self.connected = True
            threading.Thread(target=self._accept_clients, daemon=True).start()
            return True
        except Exception as e:
            print(f"Host error: {e}")
            return False

    def join_game(self, host_ip, port=DEFAULT_PORT):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host_ip, port))
            self.socket.setblocking(False)
            self.is_host = False
            self.connected = True
            threading.Thread(target=self._receive_messages, daemon=True).start()
            return True
        except Exception as e:
            print(f"Join error: {e}")
            return False

    def _accept_clients(self):
        while self.connected:
            try:
                client, addr = self.socket.accept()
                client.setblocking(False)
                self.clients.append(client)
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except BlockingIOError:
                pass
            except:
                break

    def _handle_client(self, client):
        while self.connected:
            try:
                data = client.recv(4096)
                if data:
                    with self.lock:
                        self.messages.append(json.loads(data.decode()))
            except BlockingIOError:
                pass
            except:
                break

    def _receive_messages(self):
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if data:
                    with self.lock:
                        self.messages.append(json.loads(data.decode()))
            except BlockingIOError:
                pass
            except:
                break

    def send(self, msg):
        if not self.connected:
            return
        data = json.dumps(msg).encode()
        try:
            if self.is_host:
                for client in self.clients[:]:
                    try:
                        client.send(data)
                    except:
                        self.clients.remove(client)
            else:
                self.socket.send(data)
        except:
            pass

    def get_messages(self):
        with self.lock:
            msgs = self.messages[:]
            self.messages.clear()
        return msgs

    def disconnect(self):
        self.connected = False
        try:
            if self.socket:
                self.socket.close()
            for client in self.clients:
                client.close()
        except:
            pass


class Game:
    """Main game class"""
    def __init__(self):
        self.state = "menu"
        self.players = []
        self.enemies = []
        self.boss = None
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.particles = []
        self.stars = [Star() for _ in range(50)]
        self.debris = [SpaceDebris() for _ in range(40)]

        # Create background
        self.background = create_nebula_background()
        self.planet = create_planet()
        self.planet_x = WIDTH - 100
        self.planet_y = 80

        self.wave = 1
        self.wave_timer = 0
        self.enemies_to_spawn = 0
        self.spawn_timer = 0

        self.num_local_players = 1
        self.network = NetworkManager()
        self.online_mode = False

        self.credits = 0
        self.load_data()

        self.shop_items = [
            {"name": "Speed +1", "cost": 100, "stat": "speed"},
            {"name": "Damage +1", "cost": 150, "stat": "damage"},
            {"name": "Fire Rate +1", "cost": 200, "stat": "fire_rate"},
            {"name": "Health +1", "cost": 250, "stat": "health"}
        ]
        self.shop_selection = 0
        self.menu_selection = 0
        self.ip_input = ""

    def load_data(self):
        try:
            with open("save_2d.json", "r") as f:
                data = json.load(f)
                self.credits = data.get("credits", 0)
        except:
            self.credits = 0

    def save_data(self):
        try:
            with open("save_2d.json", "w") as f:
                json.dump({"credits": self.credits}, f)
        except:
            pass

    def start_game(self, num_players=1, online=False):
        self.state = "playing"
        self.wave = 1
        self.num_local_players = num_players
        self.online_mode = online

        self.players = []
        start_positions = [
            (WIDTH // 2, HEIGHT - 100),
            (WIDTH // 3, HEIGHT - 100),
            (2 * WIDTH // 3, HEIGHT - 100),
            (WIDTH // 2, HEIGHT - 150)
        ]

        for i in range(num_players):
            x, y = start_positions[i]
            self.players.append(Player(x, y, i))

        self.enemies = []
        self.boss = None
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.particles = []
        self.start_wave()

    def start_wave(self):
        self.wave_timer = pygame.time.get_ticks()

        if self.wave % 5 == 0:
            self.boss = Boss(self.wave)
            self.enemies_to_spawn = 0
        else:
            self.boss = None
            self.enemies_to_spawn = 5 + self.wave * 2

        self.spawn_timer = pygame.time.get_ticks()

    def spawn_enemy(self):
        if self.enemies_to_spawn <= 0:
            return

        side = random.choice(["top", "left", "right"])
        if side == "top":
            x = random.randint(50, WIDTH - 50)
            y = -30
        elif side == "left":
            x = -30
            y = random.randint(50, HEIGHT // 2)
        else:
            x = WIDTH + 30
            y = random.randint(50, HEIGHT // 2)

        enemy_type = random.choices(
            [Enemy, FastEnemy, HeavyEnemy, SniperEnemy],
            weights=[40, 30, 15, 15]
        )[0]

        self.enemies.append(enemy_type(x, y))
        self.enemies_to_spawn -= 1

    def create_explosion(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self, events):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        # Update background elements
        for star in self.stars:
            star.update()
        for debris in self.debris:
            debris.update()

        if self.state == "menu":
            self.update_menu(events, keys)
        elif self.state == "playing":
            self.update_playing(events, keys, mouse_pos, mouse_buttons)
        elif self.state == "shop":
            self.update_shop(events, keys)
        elif self.state == "game_over":
            self.update_game_over(events, keys)
        elif self.state == "multiplayer_menu":
            self.update_multiplayer_menu(events, keys)
        elif self.state == "join_game":
            self.update_join_game(events, keys)

    def update_menu(self, events, keys):
        options = ["Single Player", "Local Co-op (2P)", "Local Co-op (3P)", "Online Multiplayer", "Shop", "Quit"]

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.menu_selection = (self.menu_selection - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    self.menu_selection = (self.menu_selection + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if self.menu_selection == 0:
                        self.start_game(1)
                    elif self.menu_selection == 1:
                        self.start_game(2)
                    elif self.menu_selection == 2:
                        self.start_game(3)
                    elif self.menu_selection == 3:
                        self.state = "multiplayer_menu"
                        self.menu_selection = 0
                    elif self.menu_selection == 4:
                        self.state = "shop"
                        self.shop_selection = 0
                    elif self.menu_selection == 5:
                        pygame.quit()
                        return

    def update_multiplayer_menu(self, events, keys):
        options = ["Host Game", "Join Game", "Back"]

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.menu_selection = (self.menu_selection - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    self.menu_selection = (self.menu_selection + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if self.menu_selection == 0:
                        if self.network.host_game():
                            self.start_game(1, online=True)
                    elif self.menu_selection == 1:
                        self.state = "join_game"
                        self.ip_input = ""
                    elif self.menu_selection == 2:
                        self.state = "menu"
                        self.menu_selection = 0
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    self.menu_selection = 0

    def update_join_game(self, events, keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.ip_input:
                    if self.network.join_game(self.ip_input):
                        self.start_game(1, online=True)
                elif event.key == pygame.K_BACKSPACE:
                    self.ip_input = self.ip_input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.state = "multiplayer_menu"
                    self.menu_selection = 0
                elif event.unicode and (event.unicode.isdigit() or event.unicode == '.'):
                    self.ip_input += event.unicode

    def update_shop(self, events, keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.shop_selection = (self.shop_selection - 1) % len(self.shop_items)
                elif event.key == pygame.K_DOWN:
                    self.shop_selection = (self.shop_selection + 1) % len(self.shop_items)
                elif event.key == pygame.K_RETURN:
                    item = self.shop_items[self.shop_selection]
                    if self.credits >= item["cost"]:
                        self.credits -= item["cost"]
                        self.save_data()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                    self.menu_selection = 0

    def update_playing(self, events, keys, mouse_pos, mouse_buttons):
        current_time = pygame.time.get_ticks()

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "menu"
                return

        # Update players
        for i, player in enumerate(self.players):
            if player.health > 0:
                player.update(keys, mouse_pos, i)

                should_shoot = False
                if i == 0:
                    should_shoot = mouse_buttons[0]
                elif i == 1:
                    should_shoot = keys[pygame.K_SPACE]
                elif i == 2:
                    should_shoot = keys[pygame.K_b]

                if should_shoot:
                    new_bullets = player.shoot()
                    self.bullets.extend(new_bullets)

        # Spawn enemies
        if self.enemies_to_spawn > 0 and current_time - self.spawn_timer > 1000:
            self.spawn_enemy()
            self.spawn_timer = current_time

        # Update enemies
        alive_players = [p for p in self.players if p.health > 0]
        for enemy in self.enemies[:]:
            enemy.update(alive_players)
            bullet = enemy.try_shoot(alive_players)
            if bullet:
                self.enemy_bullets.append(bullet)

        # Update boss
        if self.boss:
            self.boss.update(alive_players)
            new_bullets = self.boss.try_shoot(alive_players)
            self.enemy_bullets.extend(new_bullets)

        # Update bullets
        self.bullets = [b for b in self.bullets if b.update()]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.update()]

        # Update power-ups
        self.powerups = [p for p in self.powerups if p.update()]

        # Update particles
        self.particles = [p for p in self.particles if p.update()]

        # Check collisions
        self.check_collisions()

        # Check wave complete
        if not self.enemies and not self.boss and self.enemies_to_spawn <= 0:
            self.wave += 1
            self.start_wave()

        # Check game over
        if not alive_players:
            self.state = "game_over"
            total_score = sum(p.score for p in self.players)
            self.credits += total_score // 10
            self.save_data()

    def check_collisions(self):
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                if dist < bullet.radius + enemy.radius:
                    enemy.health -= bullet.damage
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)

                    if enemy.health <= 0:
                        self.create_explosion(enemy.x, enemy.y, enemy.color)
                        for p in self.players:
                            p.score += enemy.points

                        if random.random() < 0.2:
                            self.powerups.append(PowerUp(enemy.x, enemy.y))

                        self.enemies.remove(enemy)
                    break

            if self.boss and bullet in self.bullets:
                dist = math.hypot(bullet.x - self.boss.x, bullet.y - self.boss.y)
                if dist < bullet.radius + self.boss.radius:
                    self.boss.health -= bullet.damage
                    self.bullets.remove(bullet)

                    if self.boss.health <= 0:
                        self.create_explosion(self.boss.x, self.boss.y, PURPLE, 30)
                        for p in self.players:
                            p.score += self.boss.points
                        self.boss = None

        for bullet in self.enemy_bullets[:]:
            for player in self.players:
                if player.health <= 0:
                    continue
                dist = math.hypot(bullet.x - player.x, bullet.y - player.y)
                if dist < bullet.radius + player.radius:
                    player.take_damage(bullet.damage)
                    if bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(bullet)
                    break

        for player in self.players:
            if player.health <= 0:
                continue
            for enemy in self.enemies:
                dist = math.hypot(player.x - enemy.x, player.y - enemy.y)
                if dist < player.radius + enemy.radius:
                    player.take_damage(20)

        for player in self.players:
            if player.health <= 0:
                continue
            for powerup in self.powerups[:]:
                dist = math.hypot(player.x - powerup.x, player.y - powerup.y)
                if dist < player.radius + powerup.radius:
                    player.apply_powerup(powerup.type)
                    self.powerups.remove(powerup)

    def update_game_over(self, events, keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.state = "menu"
                    self.menu_selection = 0

    def draw(self):
        # Draw nebula background
        screen.blit(self.background, (0, 0))

        # Draw stars
        for star in self.stars:
            star.draw(screen)

        # Draw debris
        for debris in self.debris:
            debris.draw(screen)

        # Draw planet
        screen.blit(self.planet, (self.planet_x - 60, self.planet_y - 60))

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_playing()
        elif self.state == "shop":
            self.draw_shop()
        elif self.state == "game_over":
            self.draw_game_over()
        elif self.state == "multiplayer_menu":
            self.draw_multiplayer_menu()
        elif self.state == "join_game":
            self.draw_join_game()

        pygame.display.flip()

    def draw_menu(self):
        title = large_font.render("SPACE SHOOTER 2D", True, CYAN)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        subtitle = font.render("Classic Arcade Edition", True, WHITE)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 170))

        options = ["Single Player", "Local Co-op (2P)", "Local Co-op (3P)", "Online Multiplayer", "Shop", "Quit"]

        for i, option in enumerate(options):
            color = YELLOW if i == self.menu_selection else WHITE
            text = font.render(option, True, color)
            y = 260 + i * 50
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))

            if i == self.menu_selection:
                pygame.draw.polygon(screen, YELLOW, [
                    (WIDTH // 2 - text.get_width() // 2 - 30, y + 10),
                    (WIDTH // 2 - text.get_width() // 2 - 15, y + 5),
                    (WIDTH // 2 - text.get_width() // 2 - 15, y + 15)
                ])

        credits_text = small_font.render(f"Credits: {self.credits}", True, GREEN)
        screen.blit(credits_text, (10, HEIGHT - 30))

        controls = small_font.render("Arrow Keys to Navigate | Enter to Select", True, WHITE)
        screen.blit(controls, (WIDTH // 2 - controls.get_width() // 2, HEIGHT - 30))

    def draw_multiplayer_menu(self):
        title = large_font.render("ONLINE MULTIPLAYER", True, CYAN)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        options = ["Host Game", "Join Game", "Back"]

        for i, option in enumerate(options):
            color = YELLOW if i == self.menu_selection else WHITE
            text = font.render(option, True, color)
            y = 250 + i * 60
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))

    def draw_join_game(self):
        title = large_font.render("JOIN GAME", True, CYAN)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        prompt = font.render("Enter Host IP Address:", True, WHITE)
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 250))

        box_width = 300
        box_x = WIDTH // 2 - box_width // 2
        pygame.draw.rect(screen, WHITE, (box_x, 300, box_width, 50), 2)

        ip_text = font.render(self.ip_input + "_", True, CYAN)
        screen.blit(ip_text, (box_x + 10, 310))

        hint = small_font.render("Press Enter to connect | Escape to go back", True, WHITE)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 400))

    def draw_shop(self):
        title = large_font.render("UPGRADE SHOP", True, YELLOW)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        credits_text = font.render(f"Credits: {self.credits}", True, GREEN)
        screen.blit(credits_text, (WIDTH // 2 - credits_text.get_width() // 2, 120))

        for i, item in enumerate(self.shop_items):
            color = YELLOW if i == self.shop_selection else WHITE
            text = font.render(f"{item['name']} - {item['cost']} credits", True, color)
            y = 200 + i * 60
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))

        hint = small_font.render("Enter to Buy | Escape to Return", True, WHITE)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 50))

    def draw_playing(self):
        # Draw particles
        for particle in self.particles:
            particle.draw(screen)

        # Draw power-ups
        for powerup in self.powerups:
            powerup.draw(screen)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(screen)

        # Draw boss
        if self.boss:
            self.boss.draw(screen)

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(screen)
        for bullet in self.enemy_bullets:
            bullet.draw(screen)

        # Draw players
        for player in self.players:
            if player.health > 0:
                player.draw(screen)

        # Draw HUD
        self.draw_hud()

    def draw_hud(self):
        wave_text = font.render(f"Wave: {self.wave}", True, WHITE)
        screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 10))

        for i, player in enumerate(self.players):
            x = 10 + i * 200
            y = HEIGHT - 60

            bar_width = 150
            bar_height = 15
            health_pct = max(0, player.health / player.max_health)

            pygame.draw.rect(screen, (50, 50, 50), (x, y, bar_width, bar_height))
            pygame.draw.rect(screen, CYAN, (x, y, bar_width * health_pct, bar_height))
            pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 1)

            label = small_font.render(f"P{i + 1}", True, CREAM)
            screen.blit(label, (x, y - 20))

            score_text = small_font.render(f"Score: {player.score}", True, WHITE)
            screen.blit(score_text, (x, y + 20))

    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        game_over_text = large_font.render("GAME OVER", True, RED)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, 150))

        total_score = sum(p.score for p in self.players)
        score_text = font.render(f"Total Score: {total_score}", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 250))

        wave_text = font.render(f"Reached Wave: {self.wave}", True, WHITE)
        screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 300))

        credits_earned = total_score // 10
        credits_text = font.render(f"Credits Earned: {credits_earned}", True, GREEN)
        screen.blit(credits_text, (WIDTH // 2 - credits_text.get_width() // 2, 350))

        continue_text = font.render("Press Enter to Continue", True, YELLOW)
        screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, 450))


async def main():
    game = Game()
    running = True

    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        game.update(events)
        game.draw()
        clock.tick(FPS)
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
