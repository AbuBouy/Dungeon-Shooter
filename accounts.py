import sqlite3
import hashlib
from datetime import datetime


class UserData:
    def __init__(self):
        # Database connection
        self.conn = sqlite3.connect("userdata.db")
        self.cursor = self.conn.cursor()

        # Create user and highscore tables if not already made
        self.cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS Users(
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
                );
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Highscores(
                highscore_id INTEGER PRIMARY KEY AUTOINCREMENT,
                highscore INTEGER NOT NULL,
                score_date TEXT NOT NULL,
                score_time TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            );
        """)
        # Commit database changes
        self.conn.commit()
        self.current_user = None  # no user currently logged in

    def create_user(self, username, password):
        # Hash password and obtain hex equivalent
        password = hashlib.sha256(password.encode()).hexdigest()
        # Attempts to create a new user account
        try:
            self.cursor.execute("""
                INSERT INTO Users(username, password) 
                VALUES(?, ?);
            """, (username, password))
            self.conn.commit()
        # Return True or False depending on if username is already taken
        except sqlite3.IntegrityError:
            return False
        return True

    @staticmethod
    def check_strength(password):
        has_upper = has_lower = has_digit = has_special = False # values for password conditions
        special_chars = "!#$%&'()*+,-./:;<=>?@[\]^_`{|}~"  # string of all special characters


        # Password should be at least 8 characters
        if len(password) >= 8:
            for char in password:
                # Check if the character meets a condition
                if char.islower():
                    has_lower = True
                if char.isupper():
                    has_upper = True
                if char.isdigit():
                    has_digit = True
                if char in special_chars:
                    has_special = True

            # Return True if password meets all conditions
            if has_upper and has_lower and has_digit and has_special:
                return True
        return False

    def check_login(self, username, password):
        password = hashlib.sha256(password.encode()).hexdigest()
        # Check for matching record in Users table
        self.cursor.execute("""
            SELECT user_id
            FROM Users 
            WHERE username = ? AND password = ?;
         """, (username, password))
        # fetch query result
        result = self.cursor.fetchone()
        # return True or False depending on if there is a match
        if result is not None:
            self.current_user = result[0]  # set as current user
            return True
        return False

    def update_highscore(self, score):
        # Score is not saved if a user is not signed in
        if self.current_user is None:
            return

        # Get date and time of score in text format
        now = datetime.now()
        score_date = now.strftime("%Y-%m-%d")
        score_time = now.strftime("%H:%M:%S")

        # Check for existing highscore
        self.cursor.execute("""
            SELECT highscore
            FROM Highscores
            WHERE user_id = ?;
        """, (self.current_user,))
        current_highscore = self.cursor.fetchone()

        # First ever highscore
        if current_highscore is None:
            self.cursor.execute("""
                INSERT INTO Highscores(highscore, score_date, score_time, user_id)
                VALUES (?, ?, ?, ?)
            """, (score, score_date, score_time, self.current_user))
            self.conn.commit()
        # New highscore
        elif score > current_highscore[0]:
            self.cursor.execute("""
                UPDATE Highscores
                SET highscore = ?,
                    score_date = ?,
                    score_time = ?
                WHERE user_id = ?;
            """, (score, score_date, score_time, self.current_user))
            self.conn.commit()

    def get_leaderboard(self):
        # Retrieve username and highscore of top 10 users and return as list
        self.cursor.execute("""
            SELECT Users.username, Highscores.highscore
            From Users
            JOIN Highscores ON Users.user_id = Highscores.user_id
            ORDER BY Highscores.highscore DESC, Highscores.score_date ASC, Highscores.score_time ASC
            LIMIT 10;
        """)
        leaderboard_list = self.cursor.fetchall()
        return leaderboard_list
