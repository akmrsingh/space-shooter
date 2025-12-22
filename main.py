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

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter 2D - Classic Arcade")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 24)


class Star:
    """Background star for parallax effect"""
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.5, 2)
        self.size = random.randint(1, 3)
        brightness = int(100 + self.speed * 75)
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
        # Draw bullet with glow effect
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
    """Player ship class"""
    def __init__(self, x, y, player_num=0):
        self.x = x
        self.y = y
        self.player_num = player_num
        self.angle = -math.pi / 2  # Facing up
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.damage = 10
        self.fire_rate = 200  # ms between shots
        self.last_shot = 0
        self.score = 0
        self.radius = 20

        # Ship colors per player
        self.colors = [CYAN, GREEN, ORANGE, PINK]
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

        # Ship upgrades
        self.speed_level = 0
        self.damage_level = 0
        self.fire_rate_level = 0
        self.health_level = 0

    def update(self, keys, mouse_pos=None, local_player_num=0):
        """Update player movement and aiming"""
        dx, dy = 0, 0
        aim_dx, aim_dy = 0, 0

        if local_player_num == 0:
            # Player 1: WASD + Mouse
            if keys[pygame.K_w]: dy -= 1
            if keys[pygame.K_s]: dy += 1
            if keys[pygame.K_a]: dx -= 1
            if keys[pygame.K_d]: dx += 1
            if mouse_pos:
                aim_dx = mouse_pos[0] - self.x
                aim_dy = mouse_pos[1] - self.y
        elif local_player_num == 1:
            # Player 2: IJKL + Arrow keys
            if keys[pygame.K_i]: dy -= 1
            if keys[pygame.K_k]: dy += 1
            if keys[pygame.K_j]: dx -= 1
            if keys[pygame.K_l]: dx += 1
            if keys[pygame.K_UP]: aim_dy -= 1
            if keys[pygame.K_DOWN]: aim_dy += 1
            if keys[pygame.K_LEFT]: aim_dx -= 1
            if keys[pygame.K_RIGHT]: aim_dx += 1
        elif local_player_num == 2:
            # Player 3: TFGH + Numpad
            if keys[pygame.K_t]: dy -= 1
            if keys[pygame.K_g]: dy += 1
            if keys[pygame.K_f]: dx -= 1
            if keys[pygame.K_h]: dx += 1
            if keys[pygame.K_KP8]: aim_dy -= 1
            if keys[pygame.K_KP2]: aim_dy += 1
            if keys[pygame.K_KP4]: aim_dx -= 1
            if keys[pygame.K_KP6]: aim_dx += 1

        # Normalize movement
        if dx != 0 or dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length

        # Apply movement
        actual_speed = self.speed + self.speed_level * 0.5
        self.x += dx * actual_speed
        self.y += dy * actual_speed

        # Keep in bounds
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

        # Update aim angle
        if aim_dx != 0 or aim_dy != 0:
            self.angle = math.atan2(aim_dy, aim_dx)

        # Update power-up timers
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
        """Attempt to shoot"""
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
                    bullets.append(Bullet(self.x, self.y, self.angle + offset, damage, 12, self.color, self.player_num))
            else:
                bullets.append(Bullet(self.x, self.y, self.angle, damage, 12, self.color, self.player_num))
            return bullets
        return []

    def take_damage(self, amount):
        """Take damage if not shielded"""
        if not self.shield_active:
            self.health -= amount
            return True
        return False

    def apply_powerup(self, powerup_type):
        """Apply power-up effect"""
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
        """Draw the player ship"""
        # Ship body (triangle pointing in aim direction)
        points = []
        for i in range(3):
            angle = self.angle + i * (2 * math.pi / 3)
            if i == 0:
                dist = self.radius * 1.2
            else:
                dist = self.radius * 0.8
            px = self.x + math.cos(angle) * dist
            py = self.y + math.sin(angle) * dist
            points.append((px, py))

        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        # Cockpit
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 5)

        # Shield effect
        if self.shield_active:
            pygame.draw.circle(surface, (100, 200, 255), (int(self.x), int(self.y)), self.radius + 10, 3)

        # Power-up indicators
        indicator_y = self.y - self.radius - 15
        indicators = []
        if self.rapid_fire:
            indicators.append(("R", YELLOW))
        if self.spread_shot:
            indicators.append(("S", PURPLE))
        if self.damage_boost:
            indicators.append(("D", RED))

        for i, (text, color) in enumerate(indicators):
            x = self.x - 10 + i * 15
            txt = small_font.render(text, True, color)
            surface.blit(txt, (x, indicator_y))


class Enemy:
    """Base enemy class"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 30
        self.max_health = 30
        self.damage = 10
        self.speed = 2
        self.radius = 15
        self.color = RED
        self.points = 100
        self.last_shot = 0
        self.fire_rate = 2000

    def update(self, players):
        """Move toward nearest player"""
        if not players:
            return True

        # Find nearest player
        nearest = min(players, key=lambda p: math.hypot(p.x - self.x, p.y - self.y))
        angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
        self.x += math.cos(angle) * self.speed
        self.y += math.sin(angle) * self.speed
        return True

    def try_shoot(self, players):
        """Try to shoot at nearest player"""
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
        # Enemy body
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)

        # Health bar
        bar_width = self.radius * 2
        bar_height = 4
        health_pct = self.health / self.max_health
        pygame.draw.rect(surface, RED, (self.x - bar_width//2, self.y - self.radius - 10, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (self.x - bar_width//2, self.y - self.radius - 10, bar_width * health_pct, bar_height))


class FastEnemy(Enemy):
    """Fast but weak enemy"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 20
        self.max_health = 20
        self.speed = 4
        self.radius = 12
        self.color = YELLOW
        self.points = 75
        self.fire_rate = 3000


class HeavyEnemy(Enemy):
    """Slow but tough enemy"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 80
        self.max_health = 80
        self.speed = 1
        self.radius = 25
        self.color = PURPLE
        self.points = 200
        self.damage = 20
        self.fire_rate = 1500


class SniperEnemy(Enemy):
    """Long-range enemy"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 25
        self.max_health = 25
        self.speed = 1.5
        self.radius = 15
        self.color = ORANGE
        self.points = 150
        self.fire_rate = 1200
        self.preferred_distance = 300

    def update(self, players):
        if not players:
            return True

        nearest = min(players, key=lambda p: math.hypot(p.x - self.x, p.y - self.y))
        dist = math.hypot(nearest.x - self.x, nearest.y - self.y)
        angle = math.atan2(nearest.y - self.y, nearest.x - self.x)

        # Keep distance
        if dist < self.preferred_distance - 50:
            self.x -= math.cos(angle) * self.speed
            self.y -= math.sin(angle) * self.speed
        elif dist > self.preferred_distance + 50:
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed

        # Stay in bounds
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
        return True

    def try_shoot(self, players):
        if not players:
            return None

        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot >= self.fire_rate:
            nearest = min(players, key=lambda p: math.hypot(p.x - self.x, p.y - self.y))
            self.last_shot = current_time
            angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
            return EnemyBullet(self.x, self.y, angle, 10, 15)
        return None


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

        # Move side to side
        self.angle += 0.02
        self.x = WIDTH // 2 + math.sin(self.angle) * 200

        # Update attack pattern
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
            # Spread pattern
            if current_time - self.last_shot >= 300:
                self.last_shot = current_time
                for i in range(5):
                    angle = math.pi / 2 + (i - 2) * 0.3
                    bullets.append(EnemyBullet(self.x, self.y + self.radius, angle, 4, 15))
        elif self.attack_pattern == 1:
            # Aimed shots
            if current_time - self.last_shot >= 500:
                self.last_shot = current_time
                for p in players:
                    angle = math.atan2(p.y - self.y, p.x - self.x)
                    bullets.append(EnemyBullet(self.x, self.y + self.radius, angle, 6, 20))
        else:
            # Spiral pattern
            if current_time - self.last_shot >= 100:
                self.last_shot = current_time
                angle = self.angle * 5
                bullets.append(EnemyBullet(self.x, self.y + self.radius, angle, 3, 10))

        return bullets

    def draw(self, surface):
        # Boss body
        pygame.draw.circle(surface, PURPLE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius - 10)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 3)

        # Eyes
        eye_offset = 20
        pygame.draw.circle(surface, WHITE, (int(self.x - eye_offset), int(self.y - 10)), 12)
        pygame.draw.circle(surface, WHITE, (int(self.x + eye_offset), int(self.y - 10)), 12)
        pygame.draw.circle(surface, RED, (int(self.x - eye_offset), int(self.y - 10)), 6)
        pygame.draw.circle(surface, RED, (int(self.x + eye_offset), int(self.y - 10)), 6)

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
        # Pulsing effect
        pulse = abs(math.sin(self.angle)) * 5
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius + pulse))
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)

        # Icon
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
        self.stars = [Star() for _ in range(100)]

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
        """Main update loop"""
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        # Update stars
        for star in self.stars:
            star.update()

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

        # Check for pause
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "menu"
                return

        # Update players
        for i, player in enumerate(self.players):
            if player.health > 0:
                player.update(keys, mouse_pos, i)

                # Shooting
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
        # Player bullets vs enemies
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

            # Player bullets vs boss
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

        # Enemy bullets vs players
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

        # Players vs enemies (collision damage)
        for player in self.players:
            if player.health <= 0:
                continue
            for enemy in self.enemies:
                dist = math.hypot(player.x - enemy.x, player.y - enemy.y)
                if dist < player.radius + enemy.radius:
                    player.take_damage(20)

        # Players vs power-ups
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
        screen.fill(DARK_BLUE)

        # Draw stars
        for star in self.stars:
            star.draw(screen)

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

        # IP input box
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
        # Wave info
        wave_text = font.render(f"Wave: {self.wave}", True, WHITE)
        screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 10))

        # Player health bars and scores
        for i, player in enumerate(self.players):
            x = 10 + i * 200
            y = HEIGHT - 60

            # Health bar
            bar_width = 150
            bar_height = 15
            health_pct = max(0, player.health / player.max_health)

            pygame.draw.rect(screen, (50, 50, 50), (x, y, bar_width, bar_height))
            pygame.draw.rect(screen, player.color, (x, y, bar_width * health_pct, bar_height))
            pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 1)

            # Player label
            label = small_font.render(f"P{i + 1}", True, player.color)
            screen.blit(label, (x, y - 20))

            # Score
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
