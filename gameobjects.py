import pygame
import math
import time
import threading
import random
import heapq
from settings import *


class Player(pygame.sprite.Sprite):
    def __init__(self, obstacle_sprites):
        super().__init__()
        self.obstacle_sprites = obstacle_sprites
        # Sprite setup
        self.image = self.original_image = pygame.image.load("sprite images/player sprite.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)  # spawn position

        self.alive = True
        self.health = MAX_PLAYER_HEALTH
        self.speed = PLAYER_SPEED
        self.ammo = 50

        self.inventory = [Pistol(self)]
        self.equippedWeapon = self.inventory[0]  # primary weapon

        self.bullets_fired = pygame.sprite.Group()  # all bullets fired by player

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))

    def update(self):
        if self.health <= 0:
            self.alive = False
            return
        self.move()
        self.rotate()
        for weapon in self.inventory:
            self.bullets_fired.add(weapon.bullets_fired)  # add any new bullets fired

    def move(self):
        keys = pygame.key.get_pressed()  # returns boolean values for each key pressed
        dx, dy = 0, 0

        # Position changes based on pressing "WASD" keys
        if keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_s]:
            dy += self.speed
        if keys[pygame.K_d]:
            dx += self.speed
        if keys[pygame.K_a]:
            dx -= self.speed

        # Diagonal movement
        if dx != 0 and dy != 0:
            # Scale components to match resultant speed
            dx *= 1/math.sqrt(2)
            dy *= 1/math.sqrt(2)

        # Check for collision with obstacle and adjust movement accordingly
        dx, dy = self.check_collision(dx, dy)

        # Update position
        self.rect.centerx += dx
        self.rect.centery += dy

    def check_collision(self, dx, dy):
        for obstacle in self.obstacle_sprites:
            # Check for x and y collisions and set position change to 0 if obstacle is in the way
            if obstacle.rect.colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                dx = 0
            if obstacle.rect.colliderect(self.rect.x, self.rect.y + dy, self.rect.width, self.rect.height):
                dy = 0
        return dx, dy

    def rotate(self):
        angle = self.calc_angle()
        self.image = pygame.transform.rotate(self.original_image, math.degrees(angle))  # rotate image to face mouse
        new_rect = self.image.get_rect(center=self.rect.center)
        intersect = False
        for obstacle in self.obstacle_sprites:
            # Check if turning around will cause the player to be stuck
            if obstacle.rect.colliderect(new_rect):
                intersect = True
                break
        if not intersect:
            self.rect = new_rect  # adjust player rect

    def calc_angle(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()  # returns mouse position as a tuple (x, y)
        # Calculate relative x and y position of mouse from player
        relative_x = mouse_x - self.rect.centerx
        relative_y = -(mouse_y - self.rect.centery)  # adjust to pygame coordinates
        # Calculate angle in radians and return
        angle = math.atan2(relative_y, relative_x)
        return angle

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.shoot()
        elif event.type == pygame.KEYDOWN:
            if event.key == RELOAD_KEY:
                self.equippedWeapon.reload()
            elif event.key in INVENTORY_KEYS:
                if not self.equippedWeapon.reloading:  # cannot switch weapon while reloading
                    try:
                        key_num = int(event.unicode)  # integer representation of key
                        self.equippedWeapon = self.inventory[key_num - 1]  # equip corresponding weapon
                    except IndexError:
                        pass  # nothing happens if wrong key pressed

    def shoot(self):
        # Cannot shoot if weapon is reloading
        if self.equippedWeapon.reloading:
            return
        # Fire weapon if it has ammo loaded
        if self.equippedWeapon.ammo != 0:
            fire_angle = self.calc_angle()
            self.equippedWeapon.fire(fire_angle)
        # Auto reload weapon if player has ammo
        elif self.ammo != 0:
            self.equippedWeapon.reload()

    def handle_item(self, item):
        # Add weapon if space is available in the inventory
        if item.type == "weapon" and len(self.inventory) < INVENTORY_SIZE:
            if item.value == "assault rifle":
                if not self.in_inventory(AssaultRifle):
                    self.inventory.append(AssaultRifle(self))
            elif item.value == "shotgun":
                if not self.in_inventory(Shotgun):
                    self.inventory.append(Shotgun(self))

        elif item.type == "health points":
            self.health = min(self.health + item.value, MAX_PLAYER_HEALTH)  # health cannot exceed max health value

        elif item.type == "ammo":
            self.ammo += item.value

    def in_inventory(self, weapon_type):
        # Check if weapon type is present in the inventory
        for weapon in self.inventory:
            if isinstance(weapon, weapon_type):
                return True
        return False

    def take_damage(self, damage):
        self.health = max(0, self.health - damage)


class Weapon:
    def __init__(self, user, name, magazine_size, bullet_damage, fire_rate, reload_time):
        self.user = user  # weapon user
        self.name = name  # weapon name
        self.magazine_size = magazine_size  # max ammo the weapon can hold
        self.bullet_damage = bullet_damage
        self.fire_rate = fire_rate  # min time between each shot
        self.reload_time = reload_time  # seconds for reload

        self.ammo = magazine_size  # weapon currently holds a full magazine
        self.reloading = False  # reload state
        self.bullets_fired = pygame.sprite.Group()  # contains bullets that have been fired

        # Keep track of last time a bullet was fired
        self.last_fired = 0

    def fire(self, fire_angle):
        if self.ammo == 0:
            return
        current_time = time.time()
        # New bullet fired if shot within the fire rate
        if current_time - self.last_fired >= self.fire_rate:
            bullet = self.create_bullet(fire_angle)  # create new bullet
            self.bullets_fired.add(bullet)  # add bullet to group
            self.ammo -= 1  # reduce weapon ammo
            self.last_fired = current_time  # update last time weapon was fired

    def create_bullet(self, fire_angle):
        return Bullet(self.bullet_damage, fire_angle, start_pos=self.user.rect.center)

    def reload(self):
        # No need to reload if weapon holds a full magazine, is already reloading or user has no ammo
        if self.ammo == self.magazine_size or self.user.ammo == 0 or self.reloading:
            return
        reload_thread = threading.Thread(target=self._reload_method)
        reload_thread.start()

    # Private method
    def _reload_method(self):
        self.reloading = True
        time.sleep(self.reload_time)  # wait for reload time
        delta_ammo = self.magazine_size - self.ammo  # ammo needed to fill weapon
        ammo_taken = min(delta_ammo, self.user.ammo)  # ammo taken from user
        self.ammo += ammo_taken
        self.user.ammo -= ammo_taken
        self.reloading = False  # no longer reloading


class Pistol(Weapon):
    def __init__(self, user):
        super().__init__(user, "pistol", magazine_size=15, bullet_damage=15, fire_rate=0.2, reload_time=1)


class AssaultRifle(Weapon):
    def __init__(self, user):
        super().__init__(user, "assault rifle", magazine_size=30, bullet_damage=20, fire_rate=0.075, reload_time=1.75)


class Shotgun(Weapon):
    def __init__(self, user):
        super().__init__(user, "shotgun", magazine_size=12, bullet_damage=17, fire_rate=0.75, reload_time=1.2)
        self.spread = math.radians(10)  # angle of bullet spread
        self.num_pellets = 3  # number of bullets fired by shotgun

    # Override fire method for Weapon class
    def fire(self, fire_angle):
        if self.ammo == 0:
            return
        current_time = time.time()
        if current_time - self.last_fired >= self.fire_rate:
            for i in range(-1, self.num_pellets - 1):  # iterates for the number of pellets
                if self.ammo == 0:   # user may have less ammo than number of bullets fired
                    break
                bullet = self.create_bullet(fire_angle + self.spread * i)  # create bullet at appropriate angle
                self.bullets_fired.add(bullet)  # add bullet to group
                self.ammo -= 1  # reduce weapon ammo
                self.last_fired = current_time  # update last time weapon was fired


# Only used by the enemy
class Sniper(Weapon):
    def __init__(self, user):
        super().__init__(user, "sniper", magazine_size=1, bullet_damage=25, fire_rate=2.5, reload_time=2.5)


class Bullet(pygame.sprite.Sprite):
    IMAGE = pygame.image.load("sprite images/bullet.png")  # class level constant

    def __init__(self, damage, fire_angle, start_pos):
        super().__init__()
        self.image = pygame.transform.rotate(Bullet.IMAGE.convert_alpha(), math.degrees(fire_angle))
        self.direction = pygame.math.Vector2(math.cos(fire_angle), -math.sin(fire_angle)).normalize()  # fire direction

        # Set starting position of bullet and move outwards to give appearance of emerging from weapon
        self.rect = self.image.get_rect(center=start_pos)
        self.rect.center += self.direction * 30

        self.damage = damage
        self.speed = 20

    def update(self):
        # Move bullet in the correct direction at the correct speed
        self.rect.center += self.direction * self.speed

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))


# General tile class to be used by floors and walls
class Tile(pygame.sprite.Sprite):
    def __init__(self, image, x, y):
        super().__init__()
        self.image = image.convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))


class Chest(pygame.sprite.Sprite):
    IMAGE = pygame.transform.scale(pygame.image.load("tiles/chest.png"), (TILE_SIZE - 40, TILE_SIZE - 40))

    def __init__(self, x, y):
        super().__init__()
        self.image = Chest.IMAGE.convert_alpha()
        self.rect = self.image.get_rect(center=(x + TILE_SIZE/2, y + TILE_SIZE/2))  # place in the center of tile

        item_type = random.choice(["weapon", "health points", "ammo"])  # choose from different item types
        if item_type == "weapon":
            item_value = random.choice(["shotgun", "assault rifle"])  # choose from the available weapons
        else:
            item_value = random.randint(10, 80)  # random integer between 10 and 80

        self.item = Item(item_type, item_value)  # create item

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))


# Chest items
class Item:
    def __init__(self, type, value):
        self.type = type
        self.value = value


# Game Map
class Map:
    def __init__(self):
        self.array = [["w"] * MAP_WIDTH for _ in range(MAP_HEIGHT)]  # map is initially filled with walls
        self.rooms = []
        self.graph = {}  # graph implementation as adjacency list

        # generate map
        self.generate()

    def generate(self):
        # Random room generation
        MAX_ROOMS = 20
        for _ in range(MAX_ROOMS):
            current_room = self.generate_room()
            # Add room if it in a valid position
            if self.is_valid_room(current_room):
                self.add_room(current_room)
                if len(self.rooms) > 1:
                    self.add_tunnel(current_room, self.rooms[-2])  # add tunnel between current and previous rooms
        self.add_tunnel(self.rooms[0], self.rooms[-1])  # add tunnel between first and last rooms

        # Create graph representation of map array
        self.create_graph()

    @staticmethod
    def generate_room():
        # Random generation of room position and dimensions
        MIN_SIZE = 270
        MAX_SIZE = 810
        width = random.randrange(MIN_SIZE, MAX_SIZE + 1, TILE_SIZE)
        height = random.randrange(MIN_SIZE, MAX_SIZE + 1, TILE_SIZE)
        x = random.randrange(TILE_SIZE, MAP_WIDTH * TILE_SIZE - width - TILE_SIZE, TILE_SIZE)  # avoid map border
        y = random.randrange(TILE_SIZE, MAP_HEIGHT * TILE_SIZE - height - TILE_SIZE, TILE_SIZE)
        return pygame.Rect(x, y, width, height)

    def is_valid_room(self, room):
        # Check if room intersects with any existing rooms
        for existing_room in self.rooms:
            if existing_room.colliderect(room):
                return False
        return True

    def add_room(self, room):
        x_start, x_end = room.left // TILE_SIZE, room.right // TILE_SIZE
        y_start, y_end = room.top // TILE_SIZE, room.bottom // TILE_SIZE
        # Carve a rectangular room out of the walls
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                self.array[y][x] = " "  # set as floor tile
        self.rooms.append(room)

        # Random chest spawning
        num_chests = random.choices([0, 1, 2], weights=[0.25, 0.55, 0.2])[0]  # chances for number of chests in a room
        for _ in range(num_chests):
            # Make sure the chests are placed in unique positions
            while True:
                chest_x = random.randint(x_start, x_end - 1)
                chest_y = random.randint(y_start, y_end - 1)
                if self.array[chest_y][chest_x] == " ":
                    self.array[chest_y][chest_x] = "c"
                    break

    def add_tunnel(self, room1, room2):
        # Create a horizontal tunnel and then a vertical tunnel to connect two rooms
        x1, y1 = room1.center
        x2, y2 = room2.center
        self.add_horizontal_tunnel(x1, x2, y1)
        self.add_vertical_tunnel(y1, y2, x2)

    def add_horizontal_tunnel(self, x1, x2, y):
        # Carve a horizontal tunnel between two x coordinates
        x_start, x_end = [coord // TILE_SIZE for coord in sorted([x1, x2])]
        y //= TILE_SIZE
        for x in range(x_start, x_end + 1):  # iterates up to and including "x_end"
            self.array[y][x] = " "

    def add_vertical_tunnel(self, y1, y2, x):
        # Carve a vertical tunnel between two y coordinates
        y_start, y_end = [coord // TILE_SIZE for coord in sorted([y1, y2])]
        x //= TILE_SIZE
        for y in range(y_start, y_end + 1):
            self.array[y][x] = " "

    def create_graph(self):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.array[y][x] != "w":
                    # Add empty space as graph node
                    node = ((x + 0.5) * TILE_SIZE, (y + 0.5) * TILE_SIZE)  # center of floor tile
                    self.graph[node] = []
                    # Check surrounding tiles
                    for dy, dx in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        neighbor_y, neighbor_x = y + dy, x + dx
                        # Check if the neighbor is within the map dimensions:
                        if (0 <= neighbor_y < MAP_HEIGHT) and (0 <= neighbor_x < MAP_WIDTH):
                            # Add neighbor if it is an empty space
                            if self.array[neighbor_y][neighbor_x] != "w":
                                neighbor = ((neighbor_x + 0.5) * TILE_SIZE, (neighbor_y + 0.5) * TILE_SIZE)
                                self.graph[node].append(neighbor)

    def shift(self, camera_offset):
        # Shift map rooms
        for room in self.rooms:
            room.center -= camera_offset
        # Adjust graph data
        for node in list(self.graph.keys()):
            # Shift node to new position and obtain its neighbors
            new_node = (node[0] - camera_offset.x, node[1] - camera_offset.y)
            self.graph[new_node] = self.graph.pop(node)
            for i, neighbor in enumerate(self.graph[new_node]):
                self.graph[new_node][i] = (neighbor[0] - camera_offset.x, neighbor[1] - camera_offset.y)


class Enemy(pygame.sprite.Sprite):
    IMAGE = pygame.image.load("sprite images/zombie.png")

    def __init__(self, x, y, target, map, floor_tiles):
        super().__init__()
        self.target = target  # enemies will target the player
        self.map = map  # load map data
        self.floor_tiles = floor_tiles  # keep track of dungeon floor

        # Sprite setup
        self.image = self.original_image = self.IMAGE.convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))

        # Enemy attributes
        self.health = 40
        self.speed = 3
        self.accuracy = 0.6
        self.range = 300

        # Health bars
        self.healthbar = pygame.Rect(self.rect.x, self.rect.centery - 50, self.health, 10)
        self.max_healthbar = pygame.Rect(self.rect.x, self.rect.centery - 50, self.health, 10)

        # Equip enemy weapon
        self.ammo = math.inf  # infinite ammo
        self.weapon = Pistol(self)
        self.weapon.bullet_damage = 3
        self.weapon.fire_rate = 0.7

    def set_difficulty(self, level):
        # Calculate difficulty multipilier
        diff_multiplier = 1.05 ** (level - 1)
        # Apply multiplier to the enemy attributes
        self.health *= diff_multiplier
        self.speed *= diff_multiplier
        self.accuracy = min(1, self.accuracy * diff_multiplier)
        self.range *= diff_multiplier
        self.weapon.bullet_damage *= diff_multiplier

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))

    def update(self):
        # Update healthbar width and position
        self.healthbar.width = self.health
        self.healthbar.topleft = self.max_healthbar.topleft = (self.rect.x, self.rect.centery - 50)

        # Kill enemy if health falls to 0
        if self.health <= 0:
            self.kill()
            return

        self.move()
        self.rotate()
        # Shoot at player if in range
        if math.dist(self.rect.center, self.target.rect.center) <= self.range:
            self.shoot()

    def move(self):
        path = self.calculate_path()
        # First node is the start, so check if there is a path beyond it
        if len(path) >= 2:
            # Move the enemy within their speed
            next_node = pygame.math.Vector2(path[1])
            move_vector = next_node - self.rect.center
            if move_vector.magnitude() <= self.speed:
                self.rect.center = next_node
            else:
                direction = move_vector.normalize()
                self.rect.center += direction * self.speed

    def calculate_path(self):
        def heuristic(coord1, coord2):
            # Manhattan distance heuristic
            x1, y1 = coord1
            x2, y2 = coord2
            return abs(x1 - x2) + abs(y1 - y2)

        # Find floor tile occupied by player and enemy
        found_start = found_goal = False
        for floor in self.floor_tiles:
            if floor.rect.collidepoint(self.rect.center):
                start = floor.rect.center
                found_start = True
            if floor.rect.collidepoint(self.target.rect.center):
                goal = floor.rect.center
                found_goal = True
            if found_start and found_goal:
                break  # no longer need to search

        heap = [(0, start, [])]  # add start node's info to heap
        visited = set()

        # Iterate while heap is not empty
        while heap:
            # pop node with smallest f score from heap
            current_f_score, current_node, path = heapq.heappop(heap)

            # Return path to goal if reached
            if current_node == goal:
                return path + [current_node]

            # Calculate cost to current node
            current_g_score = current_f_score - heuristic(current_node, goal)

            # Check neighbors of current node
            for neighbor in self.map.graph[current_node]:
                # Can only check neighbors that haven't already been visited
                if neighbor not in visited:
                    g_score = current_g_score + 1  # distance between neighbors will always be 1 tile
                    f_score = g_score + heuristic(neighbor, goal)
                    heapq.heappush(heap, (f_score, neighbor, path + [current_node]))

            visited.add(current_node)  # mark node as visited

    def rotate(self):
        # Rotate to face player
        facing_angle = self.angle_to_player()
        self.image = pygame.transform.rotate(self.original_image, math.degrees(facing_angle))
        self.rect = self.image.get_rect(center=self.rect.center)

    def shoot(self):
        if self.weapon.reloading:
            return

        if self.weapon.ammo == 0:
            self.weapon.reload()
            return

        angle_to_player = self.angle_to_player()

        # Calculate uncertainty of shooting angle
        max_uncertainty = math.radians(10)  # maximum uncertainty value
        uncertainty = max_uncertainty * (1 - self.accuracy)

        # Select random angle within the uncertainty range and fire weapon
        shooting_angle = random.uniform(angle_to_player - uncertainty, angle_to_player + uncertainty)
        self.weapon.fire(shooting_angle)

    def angle_to_player(self):
        return math.atan2(
            -(self.target.rect.centery - self.rect.centery),
            self.target.rect.centerx - self.rect.centerx
            )

    def take_damage(self, damage):
        self.health = max(0, self.health - damage)  # health reduced no lower than 0

    def is_alive(self):
        return self.health > 0  # True or False


class ShotgunEnemy(Enemy):
    IMAGE = pygame.image.load("sprite images/shotgun zombie.png")

    def __init__(self, x, y, target, map, floor_tiles):
        super().__init__(x, y, target, map, floor_tiles)
        self.weapon = Shotgun(self)
        self.weapon.bullet_damage = 4
        self.range = 200  # close firing range


class SniperEnemy(Enemy):
    IMAGE = pygame.image.load("sprite images/sniper zombie.png")

    def __init__(self, x, y, target, map, floor_tiles):
        super().__init__(x, y, target, map, floor_tiles)
        self.weapon = Sniper(self)
        self.range = 350  # longer firing range
        self.accuracy = 0.8  # high accuracy
