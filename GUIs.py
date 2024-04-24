import pygame
from settings import *
from accounts import UserData


class Button:
    def __init__(self, image_path, x, y):
        self.image = pygame.image.load(image_path)  # load image
        self.rect = self.image.get_rect()  # returns rect object of the image
        self.rect.center = (x, y)  # sets position of the button center

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))  # draw button image at rect position

    def is_clicked(self):
        mouse_pos = pygame.mouse.get_pos()  # returns the current mouse position
        # check for mouse press and collision between button rect and mouse
        if (self.rect.collidepoint(mouse_pos)) and (pygame.mouse.get_pressed()[0]):
            return True
        else:
            return False


class TextBox:
    def __init__(self, x, y, width, height, hide_text):
        self._user_text = ""  # text entry from user, private attribute
        self.active = False  # current active state of textbox
        self.rect = pygame.Rect(x, y, width, height)  # textbox rect object
        self.font = pygame.font.SysFont("monospace", 30)  # text font
        self.char_limit = 27  # maximum number of text characters
        self.hide_text = hide_text  # boolean value for if text should be hidden

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):  # check whether mouse click was on the box
                self.active = True
            else:
                self.active = False

        elif event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self._user_text = self._user_text[:-1]  # pressing backspace removes a character
                # check if we are within the character limit
                elif len(self._user_text) < self.char_limit:
                    self._user_text += event.unicode  # add character to the text

    def draw(self, window):
        # Choose display conditions
        color = "white"
        text_output = self._user_text
        if self.active:
            color = "azure"  # color chosen depending on active state
        if self.hide_text:
            text_output = "*" * len(self._user_text)  # asterisks used in place of text

        # Display textbox
        pygame.draw.rect(window, color, self.rect)  # draws textbox as a rectangle
        text_surface = self.font.render(text_output, True, "black")  # creates text surface
        window.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))  # text surface displayed in textbox

    def get_text(self):
        return self._user_text

    def reset(self):
        self._user_text = ""


class Page:
    def __init__(self):
        self.background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.background.fill(BG_COLOUR)

    def draw_background(self, window):
        window.blit(self.background, (0, 0))


class SignInPage(Page):
    def __init__(self):
        super().__init__()
        # Create text boxes
        self.usernameTxtBox = TextBox(x=WINDOW_WIDTH / 2 - 250, y=150, width=500, height=50, hide_text=False)
        self.passwordTxtBox = TextBox(x=WINDOW_WIDTH / 2 - 250, y=300, width=500, height=50, hide_text=True)
        # Create buttons
        self.registerBtn = Button("buttons/register.png", x=WINDOW_WIDTH / 2 - 150, y=500)
        self.signInBtn = Button("buttons/sign in.png", x=WINDOW_WIDTH / 2 + 150, y=500)
        # Load registration note
        self.registration_note = pygame.image.load("registration note.png")
        # Create page headings
        heading_font = pygame.font.SysFont("Arial", 50)
        self.username_heading = heading_font.render("Username", True, "black")
        self.password_heading = heading_font.render("Password", True, "black")
        # Create variables for status message
        self.message_font = pygame.font.SysFont("Arial", 40)  # font for status message
        self.status_message = ""  # message updating the user about register/login status

    def draw(self, window):
        self.draw_background(window)
        self.draw_headings(window)
        # Draw textboxes
        self.usernameTxtBox.draw(window)
        self.passwordTxtBox.draw(window)
        # Draw buttons
        self.registerBtn.draw(window)
        self.signInBtn.draw(window)

        window.blit(self.registration_note, (820, 150))  # draw registration note
        self.display_message(window)  # display current status message

    def draw_headings(self, window):
        # Display headings onto window
        window.blit(self.username_heading, (290, 90))
        window.blit(self.password_heading, (290, 240))

    def handle_event(self, event):
        # Update the conditions of the text boxes depending on user input
        self.usernameTxtBox.handle_event(event)
        self.passwordTxtBox.handle_event(event)

    def reset(self):
        # Reset text input
        self.usernameTxtBox.reset()
        self.passwordTxtBox.reset()

    def set_message(self, message):
        self.status_message = message

    def display_message(self, window):
        if len(self.status_message) != 0:  # check that message is not an empty string
            # display status message
            message_surface = self.message_font.render(self.status_message, True, "red")
            window.blit(message_surface, (270, 650))


class Menu(Page):
    def __init__(self):
        super().__init__()
        # Create the different menu buttons
        self.playBtn = Button("buttons/play.png", x=WINDOW_WIDTH / 2, y=300)
        self.controlsBtn = Button("buttons/controls.png", x=WINDOW_WIDTH / 2, y=400)
        self.leaderboardBtn = Button("buttons/leaderboard.png", x=WINDOW_WIDTH / 2, y=500)
        self.signOutBtn = Button("buttons/sign out.png", x=120, y=670)
        # Create title
        title_font = pygame.font.SysFont("algerian", 34)
        self.title = title_font.render(GAME_TITLE, True, "red")

    def draw(self, window):
        self.draw_background(window)
        # Render title and draw buttons
        self.draw_title(window)
        self.playBtn.draw(window)
        self.controlsBtn.draw(window)
        self.signOutBtn.draw(window)
        self.leaderboardBtn.draw(window)

    def draw_title(self, window):
        window.blit(self.title, (WINDOW_WIDTH / 3, 100))


class ControlsPage(Page):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load("controls.png"), (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.backBtn = Button("buttons/back.png", x=50, y=30)

    def draw(self, window):
        self.draw_background(window)
        window.blit(self.image, (0, 0))
        self.backBtn.draw(window)


class LeaderboardPage(Page):
    def __init__(self):
        super().__init__()
        self.backBtn = Button("buttons/back.png", x=50, y=30)
        self.userData = UserData()
        self.leaderboard_list = self.userData.get_leaderboard()

        # Create title
        title_font = pygame.font.SysFont("algerian", 45)
        self.title = title_font.render("Leaderboard", True, "black")

    def draw(self, window):
        self.draw_background(window)
        self.draw_title(window)
        self.draw_leaderboard(window)
        self.backBtn.draw(window)

    def draw_title(self, window):
        window.blit(self.title, (390, 50))

    def draw_leaderboard(self, window):
        # Table constants
        TABLE_X, TABLE_Y = 100, 120
        ROW_COLORS = ("white", "khaki1")
        HEADERS = ("Rank", "Username", "Highscore")
        ROW_WIDTH, ROW_HEIGHT = 900, 50
        COL_WIDTH = ROW_WIDTH // len(HEADERS)
        HEADER_FONT = pygame.font.SysFont("Impact", 25)
        NUM_ROWS = len(self.leaderboard_list) + 1  # rows for users plus the headers row

        # Draw table rows
        rows = [(TABLE_X, TABLE_Y + ROW_HEIGHT * i, ROW_WIDTH, ROW_HEIGHT) for i in range(NUM_ROWS)]
        for i, row in enumerate(rows):
            pygame.draw.rect(window, ROW_COLORS[i % 2], row)  # alternate between row colors
            pygame.draw.line(window, "gold", (row[0], row[1]), (row[0] + row[2], row[1]))  # draw line to separate row

        # Draw table columns
        cols = [(TABLE_X + COL_WIDTH * i, TABLE_Y, COL_WIDTH, ROW_HEIGHT * NUM_ROWS) for i in range(len(HEADERS) + 1)]
        for col in cols:
            pygame.draw.line(window, "gold", (col[0], col[1]), (col[0], col[1] + col[3]))  # draw line to separate col

        # Draw headers
        for i, header in enumerate(HEADERS):
            text = HEADER_FONT.render(header, True, "black")
            window.blit(text, (TABLE_X + 10 + COL_WIDTH * i, TABLE_Y + 10))

        # Draw leaderboard rows
        for i, (username, highscore) in enumerate(self.leaderboard_list):
            username_text = HEADER_FONT.render(username, True, "black")
            highscore_text = HEADER_FONT.render(str(highscore), True, "black")
            rank_text = HEADER_FONT.render(str(i + 1), True, "black")
            x = TABLE_X + 10
            y = TABLE_Y + 10 + ROW_HEIGHT + ROW_HEIGHT * i  # first row is left for the headers
            window.blit(rank_text, (x, y))
            window.blit(username_text, (x + COL_WIDTH, y))
            window.blit(highscore_text, (x + COL_WIDTH * 2, y))

    def update(self):
        self.leaderboard_list = self.userData.get_leaderboard()  # get updated leaderboard


class PlayerGUI:
    def __init__(self, player):
        self.player = player
        self.font = pygame.font.SysFont("Impact", 14)  # text font
        self.healthbar = pygame.Rect(WINDOW_WIDTH - MAX_PLAYER_HEALTH * 2 - 20, 10, self.player.health * 2, 20)
        self.ammo_icon = pygame.image.load("icons/ammo.png").convert_alpha()
        self.weapon_icons = {
            "pistol": pygame.image.load("icons/pistol.png").convert_alpha(),
            "shotgun": pygame.image.load("icons/shotgun.png").convert_alpha(),
            "assault rifle": pygame.image.load("icons/assault rifle.png").convert_alpha(),
        }

    def draw(self, window):
        self.draw_health(window)
        self.draw_inventory(window)
        self.draw_ammo(window)

    def draw_health(self, window):
        # draw red bar to represent max player health
        pygame.draw.rect(window, "red", (WINDOW_WIDTH - MAX_PLAYER_HEALTH * 2 - 20, 10, MAX_PLAYER_HEALTH * 2, 20))
        # set length of healthbar as double the player's current health
        self.healthbar.width = self.player.health * 2
        pygame.draw.rect(window, "green", self.healthbar)  # draw healthbar as green rectangle

    def draw_inventory(self, window):
        x_separation = 75  # x separation of inventory boxes
        for i in range(INVENTORY_SIZE):
            box_x, box_y = 25 + x_separation * i, WINDOW_HEIGHT - 75  # set position of inventory box
            color = "white"  # default color of box
            if i == self.player.inventory.index(self.player.equippedWeapon):
                color = "azure"  # change color of inventory box for selected weapon
                box_y -= 10  # move selected box upwards
                if self.player.equippedWeapon.reloading:
                    color = "coral"  # color for weapon reload
            pygame.draw.rect(window, color, (box_x, box_y, 65, 65))  # draw box as a rectangle, dimensions 65x65
            # Check whether weapon slot is occupied
            if i < len(self.player.inventory):
                weapon = self.player.inventory[i]
                weapon_icon = self.weapon_icons[weapon.name]  # retrieve icon image from dictionary
                ammo_text_surface = self.font.render(f"x{weapon.ammo}", True, "black")   # create text for weapon ammo
                window.blit(ammo_text_surface, (box_x + 20, box_y + 40))  # display ammo text within the box
            else:
                weapon_icon = self.font.render("Empty", True, "red")   # icon set as text surface with string "Empty"
            window.blit(weapon_icon, (box_x + 5, box_y + 20))  # display icon inside inventory box

    def draw_ammo(self, window):
        window.blit(self.ammo_icon, (990, 670))
        text_surface = self.font.render(f"x{self.player.ammo}", True, "black")
        # display text next to ammo icon
        window.blit(text_surface, (995 + self.ammo_icon.get_width(), 670 + self.ammo_icon.get_height()//2))


# Game Heads Up Display
class GameHUD:
    def __init__(self, game):
        self.game = game
        self.playerGUI = PlayerGUI(self.game.player)
        self.font = pygame.font.SysFont("Impact", 18)

    def draw(self, window):
        self.playerGUI.draw(window)
        # Display current level and player score
        level_text = self.font.render(f"Level: {self.game.level}", True, "red")
        score_text = self.font.render(f"Score: {self.game.player_score}", True, "red")
        window.blit(level_text, (10, 10))
        window.blit(score_text, (90, 10))


class ScreenTransitions:
    def __init__(self):
        self.font = pygame.font.SysFont("Impact", 55)
        self.background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.background.set_alpha(100)

    def game_over(self, window, score):
        # Display background messages
        game_over_message = self.font.render("Game Over", True, "red")
        score_message = self.font.render(f"Score: {score}", True, "red")
        window.blit(self.background, (0, 0))
        window.blit(game_over_message, (425, 250))
        window.blit(score_message, (435, 350))

        # Update display and wait for 2.5 seconds
        pygame.mouse.set_visible(True)
        pygame.display.update()
        pygame.time.wait(2500)

    def new_dungeon(self, window):
        # Display background and message
        window.blit(self.background, (0, 0))
        message = self.font.render("Regenerating Dungeon...", True, "black")
        window.blit(message, (250, 300))

        # Update display and wait for 2 seconds
        pygame.mouse.set_visible(True)
        pygame.display.update()
        pygame.time.wait(2000)
        pygame.mouse.set_visible(False)
