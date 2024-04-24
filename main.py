import pygame
import sys
import random
from settings import *
from GUIs import *
from accounts import UserData
from gameobjects import *


class Application:
    def __init__(self):
        pygame.init()
        # general setup
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)

        # Initialise all the page objects
        self.signInPage = SignInPage()
        self.menu = Menu()
        self.controlsPage = ControlsPage()
        self.leaderboardPage = LeaderboardPage()

        # Create dictionary matching "current_page" values to page objects
        self.pages = {
            "sign in": self.signInPage,
            "menu": self.menu,
            "controls": self.controlsPage,
            "leaderboard": self.leaderboardPage
        }
        self.current_page = "sign in"  # sign in page is opened first by default

        # Connect to database
        self.userData = UserData()
        # Set the game as not yet started
        self.game_started = False

    def run(self):
        # Stay in the pre-game until the game has started
        while not self.game_started:
            self.check_events()
            self.pages[self.current_page].draw(self.window)  # matching page is drawn to the window
            pygame.display.update()

        # Running the game
        game = Game()
        score = game.run()

        # Update user score and leaderboard then return to menu
        self.userData.update_highscore(score)
        self.leaderboardPage.update()
        self.game_started = False
        self.run()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # update sign in page for keyboard entry if open
            elif event.type == pygame.KEYDOWN:
                if self.current_page == "sign in":
                    self.signInPage.handle_event(event)

            # update pages based on mouse clicks
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.current_page == "sign in":
                    self.signInPage.handle_event(event)
                    # User clicked the register button
                    if self.signInPage.registerBtn.is_clicked():
                        self.handle_registration()
                    # User clicked the sign-in button
                    elif self.signInPage.signInBtn.is_clicked():
                        self.handle_sign_in()

                # Check for interactions with menu page
                elif self.current_page == "menu":
                    if self.menu.playBtn.is_clicked():
                        self.game_started = True
                    elif self.menu.controlsBtn.is_clicked():
                        self.current_page = "controls"
                    elif self.menu.leaderboardBtn.is_clicked():
                        self.current_page = "leaderboard"
                    elif self.menu.signOutBtn.is_clicked():
                        self.current_page = "sign in"
                        self.userData.current_user = None  # no user logged in

                # Check for interactions with leaderboard/controls page
                elif self.current_page == "controls" or self.current_page == "leaderboard":
                    # Clicking the back button takes us to the menu
                    if self.pages[self.current_page].backBtn.is_clicked():
                        self.current_page = "menu"

    def handle_registration(self):
        # Retrieve username and password entries from textboxes
        username = self.signInPage.usernameTxtBox.get_text()
        password = self.signInPage.passwordTxtBox.get_text()
        # Check if the fields were filled in
        if len(username) == 0 or len(password) == 0:
            self.signInPage.set_message("Please fill in all fields")
        # Check password strength
        elif self.userData.check_strength(password):
            # Check for successful account creation
            if self.userData.create_user(username, password):
                self.signInPage.set_message("Account creation successful")
                self.signInPage.reset()  # reset the page
            else:
                self.signInPage.set_message("Username is already taken")
        else:
            self.signInPage.set_message("Password is not strong enough")

    def handle_sign_in(self):
        username = self.signInPage.usernameTxtBox.get_text()
        password = self.signInPage.passwordTxtBox.get_text()
        # Check if the fields were filled in
        if len(username) == 0 or len(password) == 0:
            self.signInPage.set_message("Please fill in all fields")
        # Check if login was successful
        elif self.userData.check_login(username, password):
            # Clear data for sign in page
            self.signInPage.reset()
            self.signInPage.set_message("")
            # Direct user to menu
            self.current_page = "menu"
        else:
            self.signInPage.set_message("Username or password does not match")


class Game:
    def __init__(self):
        # General setup
        self.window = pygame.display.get_surface()
        self.clock = pygame.time.Clock()

        # Hide the mouse and initialise the crosshair
        pygame.mouse.set_visible(False)
        self.crosshair = Crosshair()

        # Game sprite groups
        self.dynamic_sprites = pygame.sprite.Group()  # contains sprites that are moving and updating
        self.obstacle_sprites = pygame.sprite.Group()  # contains map obstacles
        self.chest_sprites = pygame.sprite.Group()  # contains map chest

        # Enemy management
        self.enemy_sprites = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()

        # Map
        self.map = Map()
        self.floor_tiles = pygame.sprite.Group()

        # Game variables
        self.level = 1
        self.player_score = 0

        # Time variables
        self.elapsed_time = 0
        self.last_min = 0

        # Create player and add to group
        self.player = Player(self.obstacle_sprites)
        self.dynamic_sprites.add(self.player)

        self.HUD = GameHUD(self)  # Initialise heads up display
        self.screenTransitions = ScreenTransitions()

    def run(self):
        self.generate_dungeon()
        while self.player.alive:
            self.check_events()
            self.camera_scroll()
            self.handle_collisions()
            self.draw()
            self.update()

        # Return score after game finishes running
        self.screenTransitions.game_over(self.window, self.player_score)
        return self.player_score

    def generate_dungeon(self):
        # Translate game map into corresponding objects
        self.player.rect.center = self.map.rooms[0].center  # player spawns in the middle of the first room
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if self.map.array[y][x] == "w":  # wall already takes up the whole tile space
                    self.obstacle_sprites.add(Tile(WALL_IMAGE, x * TILE_SIZE, y * TILE_SIZE))
                else:
                    # Add a floor tile and check if there should be a chest in that position
                    self.floor_tiles.add(Tile(FLOOR_IMAGE, x * TILE_SIZE, y * TILE_SIZE))
                    if self.map.array[y][x] == "c":
                        self.chest_sprites.add(Chest(x * TILE_SIZE, y * TILE_SIZE))
        self.spawn_enemies()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Player only needs to deal with mouse and keyboard presses
            elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                self.player.handle_event(event)

    def camera_scroll(self):
        screen_center = pygame.math.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        camera_offset = self.player.rect.center - screen_center  # calculate offset of player from middle of the screen
        self.player.rect.center = screen_center  # keep the player at the screen center

        # Adjust map data
        self.map.shift(camera_offset)

        # Shift game sprites to keep at same position relative to player
        for sprite_group in (self.dynamic_sprites, self.floor_tiles, self.obstacle_sprites, self.chest_sprites):
            for sprite in sprite_group:
                if sprite != self.player:
                    sprite.rect.center -= camera_offset

    def handle_collisions(self):
        # Bullet-obstacle collision deletes bullet
        pygame.sprite.groupcollide(self.player.bullets_fired, self.obstacle_sprites, True, False)
        pygame.sprite.groupcollide(self.enemy_bullets, self.obstacle_sprites, True, False)

        # Player-chest collisions
        chests_collided = pygame.sprite.spritecollide(self.player, self.chest_sprites, True)
        for chest in chests_collided:
            self.player.handle_item(chest.item)

        # Player collision with enemy bullet
        bullets_collided = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for bullet in bullets_collided:
            self.player.take_damage(bullet.damage)

        # Enemy collision with player bullet
        collisions_dict = pygame.sprite.groupcollide(self.enemy_sprites, self.player.bullets_fired, False, True)
        for enemy, bullets_collided in collisions_dict.items():
            for bullet in bullets_collided:
                enemy.take_damage(bullet.damage)

    def draw(self):
        # Fill the window and draw the map floor
        self.window.fill("burlywood")
        self.floor_tiles.draw(self.window)

        # Draw game sprites
        self.obstacle_sprites.draw(self.window)
        self.chest_sprites.draw(self.window)
        self.dynamic_sprites.draw(self.window)

        # Draw enemy health bars
        for enemy in self.enemy_sprites:
            pygame.draw.rect(self.window, "red", enemy.max_healthbar)
            pygame.draw.rect(self.window, "green", enemy.healthbar)

        # Draw heads up display and crosshair
        self.HUD.draw(self.window)
        self.crosshair.draw(self.window)

    def update(self):
        # Player score update
        self.update_score()

        # Add new bullets fired
        for enemy in self.enemy_sprites:
            self.enemy_bullets.add(enemy.weapon.bullets_fired)
        self.dynamic_sprites.add(self.player.bullets_fired, self.enemy_bullets)

        # Spawn new enemies after all are killed
        if len(self.enemy_sprites) == 0:
            self.level += 1
            # New dungeon generated every 5 levels
            if self.level % 5 == 0:
                self.new_dungeon()
            else:
                self.spawn_enemies()

        # Display update
        self.crosshair.update()
        self.dynamic_sprites.update()
        pygame.display.update()
        self.clock.tick(FPS)  # restrict frame rate

    def update_score(self):
        # Update score for every minute passed
        self.elapsed_time += self.clock.get_time()  # update elapsed time
        current_min = self.elapsed_time // 60000  # convert from milliseconds to the current minute
        if current_min > self.last_min:
            self.player_score += MINUTE_POINTS  # increment score
            self.last_min = current_min  # update to the next minute

        # Update score for enemy eliminations
        for enemy in self.enemy_sprites:
            if not enemy.is_alive():
                self.player_score += ELIM_POINTS

    def spawn_enemies(self):
        # Default enemy spawned in the first level
        if self.level == 1:
            num_enemies = 1
            enemyClass = Enemy
        else:
            num_enemies = random.randint(3, 5)  # 3 to 5 enemies spawned per wave
            enemyClass = random.choice([Enemy, ShotgunEnemy, SniperEnemy])  # enemy type chosen randomly

        occupied_rooms = []
        # Add the player's current room to the list of occupied rooms
        for room in self.map.rooms:
            if room.collidepoint(self.player.rect.center):
                occupied_rooms.append(room)
                break

        # Spawn enemies in different rooms
        for _ in range(num_enemies):
            room = random.choice(self.map.rooms)
            # Make sure room is not occupied
            while room in occupied_rooms:
                room = random.choice(self.map.rooms)
            occupied_rooms.append(room)
            spawn_x, spawn_y = room.center
            enemy = enemyClass(spawn_x, spawn_y, self.player, self.map, self.floor_tiles)  # create instance of enemy
            enemy.set_difficulty(self.level)
            self.enemy_sprites.add(enemy)
            self.dynamic_sprites.add(enemy)

    def new_dungeon(self):
        self.screenTransitions.new_dungeon(self.window)
        level, score = self.level, self.player_score
        self.__init__()
        self.level, self.player_score = level, score
        self.generate_dungeon()


# Running the program
if __name__ == "__main__":
    app = Application()
    app.run()
