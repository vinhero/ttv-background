import pygame
import sys
import threading
# ----
import socket
# ----
import urllib.request
import urllib.parse
import json
# ----
import math
# ----

# #################################### SETTINGS - FILE #################################### #
with open("settings.json") as file:
    settings = json.load(file)

# #################################### PYGAME #################################### #
pygame.init()
clock = pygame.time.Clock()
running = True

# #################################### IMPORTANT VARIABLES #################################### #
THE_STREAMER = settings["streamer"]

WIDTH_WINDOW = settings["windows"]["start_window"]["width"]
HEIGHT_WINDOW = settings["windows"]["start_window"]["height"]
FPS = settings["windows"]["start_window"]["fps"]
MAX_PLANES = settings["actors"]["spawner"]["max_flying_planes"]
MAX_WAITING_PLANES = settings["actors"]["spawner"]["max_waiting_planes"]
TARGET_DELTATIME = int(1000 / FPS)

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
SKY_CORLOR = (96, 150, 202)

# #################################### initialization: DISPLAY #################################### #
stream_display = pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
pygame.display.set_caption(settings["title"])

icon_img = pygame.image.load(settings["windows"]["icon"]["img"])
icon_img_size_xy = settings["windows"]["icon"]["size"]
icon_img = pygame.transform.scale(icon_img, (icon_img_size_xy, icon_img_size_xy))
pygame.display.set_icon(icon_img)

background_img = pygame.image.load(settings["windows"]["start_window"]["background_img"]).convert_alpha(stream_display)

# #################################### Actor: PLANE #################################### #
p_size_xy = settings["actors"]["plane"]["size"]
plane_size = [p_size_xy, p_size_xy]

plane_img_streamer = pygame.image.load(settings["actors"]["plane_streamer"]["img_streamer"]).convert_alpha(
    stream_display)
plane_img_streamer = pygame.transform.smoothscale(plane_img_streamer, (plane_size[0], plane_size[1]))
plane_img_streamer = pygame.transform.rotate(plane_img_streamer, -90)
plane_img_streamer_flip = pygame.transform.flip(plane_img_streamer.copy(), False, True)

plane_img_viewer = pygame.image.load(settings["actors"]["plane"]["img_viewer"]).convert_alpha(stream_display)
plane_img_viewer = pygame.transform.smoothscale(plane_img_viewer, (plane_size[0], plane_size[1]))
plane_img_viewer = pygame.transform.rotate(plane_img_viewer, -90)
plane_img_viewer_flip = pygame.transform.flip(plane_img_viewer.copy(), False, True)

plane_img_vip = pygame.image.load(settings["actors"]["plane"]["img_vip"]).convert_alpha(stream_display)
plane_img_vip = pygame.transform.smoothscale(plane_img_vip, (plane_size[0], plane_size[1]))
plane_img_vip = pygame.transform.rotate(plane_img_vip, -90)
plane_img_vip_flip = pygame.transform.flip(plane_img_vip.copy(), False, True)

plane_img_mod = pygame.image.load(settings["actors"]["plane"]["img_mod"]).convert_alpha(stream_display)
plane_img_mod = pygame.transform.smoothscale(plane_img_mod, (plane_size[0], plane_size[1]))
plane_img_mod = pygame.transform.rotate(plane_img_mod, -90)
plane_img_mod_flip = pygame.transform.flip(plane_img_mod.copy(), False, True)


# #################################### CLASSES #################################### #
class Plane:
    def __init__(self, user_name, screen, x_pos, y_pos, degree, size, a_type, speed, index):
        self.TYPE = a_type

        self.DEAD = False
        self.LIFESPAN = settings["actors"]["plane"]["lifespan"]

        self.DEAD_ACCL = settings["actors"]["plane"]["d_acc"] / 100
        self.ALIVE_ACCL = 0
        self.F_SPEED = speed / 10
        self.TURNING_VEL = settings["actors"]["plane"]["t_vel"] / 1000

        self.SCREEN = screen
        self.DEGREE = degree
        self.X_POS = x_pos
        self.Y_POS = y_pos

        self.PLANE_SIZE = size

        self.PLANE_IMG = ""
        if index == 3:
            if self.TYPE == "MOD":
                self.PLANE_IMG = plane_img_mod_flip.convert_alpha(stream_display).copy()
            elif self.TYPE == "VIP":
                self.PLANE_IMG = plane_img_vip_flip.convert_alpha(stream_display).copy()
            else:
                self.PLANE_IMG = plane_img_viewer_flip.convert_alpha(stream_display).copy()
        else:
            if self.TYPE == "MOD":
                self.PLANE_IMG = plane_img_mod.convert_alpha(stream_display).copy()
            elif self.TYPE == "VIP":
                self.PLANE_IMG = plane_img_vip.convert_alpha(stream_display).copy()
            else:
                self.PLANE_IMG = plane_img_viewer.convert_alpha(stream_display).copy()

        self.FONT_SIZE = settings["actors"]["plane"]["font_size"]
        self.MAX_FONT_WIDTH = settings["actors"]["plane"]["font_width"]
        self.MAX_FONT_HEIGHT = settings["actors"]["plane"]["font_height"]

        self.ACTUAL_USERNAME = user_name
        self.U_NAME_FONT = pygame.font.SysFont("Arial, Times New Roman", self.FONT_SIZE)
        self.U_NAME = self.U_NAME_FONT.render(f"{user_name}", True, BLACK)
        while self.U_NAME.get_width() > self.MAX_FONT_WIDTH:
            self.FONT_SIZE -= 1
            self.U_NAME_FONT = pygame.font.SysFont("Arial, Times New Roman", self.FONT_SIZE)
            self.U_NAME = self.U_NAME_FONT.render(f"{user_name}", True, BLACK)

        self.U_NAME_DEGREE = self.DEGREE - int(self.DEGREE / 360) * 360

        self.TIMER = 0

    def draw(self, a_screen, _x_pos, _y_pos, _size_b):

        # Normalizes all DEGREES.
        self.U_NAME_DEGREE -= int(self.U_NAME_DEGREE / 360) * 360
        self.DEGREE -= int(self.DEGREE / 360) * 360

        if (90 < self.U_NAME_DEGREE < 270) or (-90 > self.U_NAME_DEGREE > -270):
            self.U_NAME_DEGREE += 180

        plane_img_copy = pygame.transform.rotate(self.PLANE_IMG, self.DEGREE)
        user_name_copy = pygame.transform.rotate(self.U_NAME, self.U_NAME_DEGREE)

        # draws the PLANE and then the USERNAME.
        a_screen.blit(plane_img_copy,
                      (_x_pos - int(plane_img_copy.get_width() / 2), _y_pos - int(plane_img_copy.get_height() / 2)))
        a_screen.blit(user_name_copy,
                      (_x_pos - int(user_name_copy.get_width() / 2), _y_pos - int(user_name_copy.get_height() / 2)))

    def behavior(self, delta_time):
        # True if the PLANE is still visible on the Screen.
        is_still_visible = (((self.Y_POS >= 0 - self.PLANE_SIZE) and (self.Y_POS <= HEIGHT_WINDOW + self.PLANE_SIZE))
                            and
                            ((self.X_POS >= 0 - self.PLANE_SIZE) and (self.X_POS <= WIDTH_WINDOW + self.PLANE_SIZE)))

        if self.LIFESPAN > 0:
            self.LIFESPAN -= delta_time

            if is_still_visible:
                # default forward - velocity added to position
                self.F_SPEED += self.ALIVE_ACCL
                self.X_POS += math.cos(math.radians(self.DEGREE)) * self.F_SPEED * delta_time
                self.Y_POS -= math.sin(math.radians(self.DEGREE)) * self.F_SPEED * delta_time

                # default turning added to current degree
                # self.DEGREE += self.TURNING_VEL * delta_time
                # self.U_NAME_DEGREE += self.TURNING_VEL * delta_time

                self.TIMER += delta_time
                if self.TIMER > 5000:
                    self.TURNING_VEL *= -1
                    self.TIMER = 0

            # Teleports the PLANE to the other side of the Screen if the PLANE is not visible anymore.
            else:
                self.teleport()

        else:
            # dead velocity added to position
            self.F_SPEED += self.DEAD_ACCL
            self.X_POS += math.cos(math.radians(self.DEGREE)) * self.F_SPEED * delta_time
            self.Y_POS -= math.sin(math.radians(self.DEGREE)) * self.F_SPEED * delta_time

            if not is_still_visible:
                self.DEAD = True

    def teleport(self):
        # if Y is too big or too small
        if self.Y_POS < 0 - self.PLANE_SIZE:
            self.Y_POS = HEIGHT_WINDOW + self.PLANE_SIZE / 2
        elif self.Y_POS > HEIGHT_WINDOW + self.PLANE_SIZE:
            self.Y_POS = 0 - self.PLANE_SIZE / 2

        # if X is too big or too small
        elif self.X_POS < 0 - self.PLANE_SIZE:
            self.X_POS = WIDTH_WINDOW + self.PLANE_SIZE / 2
        elif self.X_POS > WIDTH_WINDOW + self.PLANE_SIZE:
            self.X_POS = 0 - self.PLANE_SIZE / 2

    def __call__(self, delta_time):
        self.behavior(delta_time)
        self.draw(self.SCREEN, self.X_POS, self.Y_POS, self.PLANE_SIZE)


class BackGround:
    def __init__(self, a_display):
        self.DISPLAY = a_display
        self.BACKGROUND_COLOR = SKY_CORLOR
        self.BACKGROUND_IMG = background_img.copy()

        self.X_MAX = 0
        self.X_MIN = 0 + (WIDTH_WINDOW - self.BACKGROUND_IMG.get_width())

        self.POS_X = 0
        self.POS_Y = 0

        self.SPEED = 50

    def draw(self):
        self.DISPLAY.blit(self.BACKGROUND_IMG, (self.POS_X, self.POS_Y))

    def behavior(self, delta_time):

        if self.POS_X + self.SPEED * delta_time / 1000 > self.X_MAX \
                or self.POS_X + self.SPEED * delta_time / 1000 < self.X_MIN:
            self.SPEED *= -1

        self.POS_X += self.SPEED * delta_time / 1000

    def __call__(self, delta_time):
        self.behavior(delta_time)
        self.draw()


class TTVBot:
    def __init__(self):
        self.oauth = settings["twitch_bot"]["oauth"]
        self.nick_name = settings["twitch_bot"]["nick_name"]
        self.addr = settings["twitch_bot"]["adresse"]
        self.port = settings["twitch_bot"]["port"]
        self.channel = ""

        self.list_chatters_ignore = settings["twitch_bot"]["ingore_list"]
        self.list_chatters_ignore.append(f"{self.nick_name}")
        self.list_chatters_vip = list()
        self.list_chatters_mod = list()
        self.list_chatters_current = list()

        self.sock = socket.socket()

        # 5 min in ms
        self.PONGTIMER = 300000

        self.COUNTER = 0

    def get_chatter(self):
        twitch_message = self.recv(self.sock, 1024)

        if "PRIVMSG" in twitch_message and not self.COUNTER == 0:
            user = self.parse_name(twitch_message)
            try:
                if (self.list_chatters_ignore.count(user) < 1) \
                        and (len(user) > 0
                             and spawner.CHATTERS_WHICH_ARE_PILOTS.count(user) < 1):
                    self.list_chatters_current.append(user)
            except:
                print("BOT: I can't use this name.")

        elif "PONG" in twitch_message:
            self.send_pong()
            print("TWITCH: When i say \"PING\", you say..?")
            print("BOT: \"PONG!\"")

        self.COUNTER += 1

    def parse_name(self, msg):
        data = msg.split(" ")[0]
        try:
            index = data.index("!")
        except:
            return ""
        return data[1:index]

    def send(self, sock, msg):
        sock.send(bytes(msg + "\n", "ASCII"))

    def send_pong(self):
        self.send(self.sock, "PONG tmi.twitch.tv")
        self.PONGTIMER = 300000

    def recv(self, sock, buff_size):
        try:
            twitch_message = sock.recv(buff_size).decode("UTF-8")
            return twitch_message
        except:
            print("BOT: Couldn't receive message from TWITCH, please RESTART!")
            return ""

        # return twitch_message

    def connect_bot(self):
        self.sock.connect((self.addr, self.port))

        self.send(self.sock, f"PASS {self.oauth}")
        self.send(self.sock, f"NICK {self.nick_name}")
        print("BOT: I established a connection to Twitch.")

    def join_chat(self, channel_name):
        self.channel = channel_name
        if settings["ignore_stream"] == "True":
            self.list_chatters_ignore.append(self.channel)

        self.send(self.sock, f"JOIN #{self.channel}")
        print(f"BOT: I joined the chat of {self.channel}")

    def get_the_special_ones(self, a_url):
        request = urllib.request.Request(a_url)
        recieved_data = urllib.request.urlopen(request)

        json_data = json.loads(recieved_data.read().decode("utf-8"))

        self.list_chatters_vip = json_data['chatters']['vips']
        self.list_chatters_mod = json_data['chatters']['moderators']

    def reset_list(self):
        self.list_chatters_current = []

    def reconnect_bot(self):
        self.sock.connect((self.addr, self.port))

        self.send(self.sock, f"PASS {self.oauth}")
        self.send(self.sock, f"NICK {self.nick_name}")
        print("BOT: I reconnected to Twitch.")

    def disconnect_bot(self):
        if self.list_chatters_ignore.count(self.channel) == 1:
            self.list_chatters_ignore.pop(len(self.list_chatters_ignore) - 1)
        self.send(self.sock, f"PART {self.channel}")

        # leaves all current chats
        self.send(self.sock, "JOIN 0")
        # disconnects from twitch
        self.send(self.sock, "QUIT")

        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        print(f"BOT: I left chat of {self.channel} and disconnected from Twitch.")


class Spawner:
    def __init__(self, a_display):
        self.MAX_FLYING_PLANES = settings["actors"]["spawner"]["max_flying_planes"]
        self.MAX_WATING_PLANES = settings["actors"]["spawner"]["max_waiting_planes"]
        self.SPAWNTIMER = settings["actors"]["spawner"]["spawntimer_planes"]
        self.SPAWNS = settings["actors"]["spawner"]["spawns"]
        self.SPAWNINDEX = 0
        self.PLANESIZE = settings["actors"]["plane"]["size"]

        self.DISPLAY = a_display

        self.PLANES_WAITLIST = []
        self.LIST_OF_FLYING_PLANES = []
        self.CHATTERS_WHICH_ARE_PILOTS = []

    def create_plane(self, nickname, a_type):
        point_x = self.SPAWNS[f"spawn{self.SPAWNINDEX}"]["x"]
        point_y = self.SPAWNS[f"spawn{self.SPAWNINDEX}"]["y"]
        angle_deg = self.SPAWNS[f"spawn{self.SPAWNINDEX}"]["a"]
        speed = self.SPAWNS[f"spawn{self.SPAWNINDEX}"]["s"]

        a_new_plane = Plane(nickname,
                            self.DISPLAY,
                            point_x,
                            point_y,
                            angle_deg,
                            self.PLANESIZE,
                            a_type,
                            speed,
                            self.SPAWNINDEX)

        self.PLANES_WAITLIST.append(a_new_plane)
        self.CHATTERS_WHICH_ARE_PILOTS.append(a_new_plane.ACTUAL_USERNAME)

        self.SPAWNINDEX += 1
        if self.SPAWNINDEX > 3:
            self.SPAWNINDEX = 0

    def spawn_plane(self):
        self.LIST_OF_FLYING_PLANES.append(self.PLANES_WAITLIST[0])
        self.PLANES_WAITLIST.pop(0)
    
    # TODO: Clean up this terrible method 
    def delete_dead_planes(self):
        i_of_dead_plane = 0
        for a_plane in self.LIST_OF_FLYING_PLANES:
            if a_plane.DEAD:
                self.LIST_OF_FLYING_PLANES.pop(i_of_dead_plane)
                i_chatter = 0
                for a_chatter in self.CHATTERS_WHICH_ARE_PILOTS:
                    if a_plane.ACTUAL_USERNAME == a_chatter:
                        self.CHATTERS_WHICH_ARE_PILOTS.pop(i_chatter)
                        break
                    else:
                        i_chatter += 1
                break
            else:
                i_of_dead_plane += 1

    def reset_spawntimer(self):
        self.SPAWNTIMER = settings["actors"]["spawner"]["spawntimer_planes"]


# #################################### initialization: BACKGROUND #################################### #
Background = BackGround(stream_display)

# #################################### initialization: SPAWNER #################################### #
spawner = Spawner(stream_display)

# #################################### initialization: BOT #################################### #
twitch_bot = TTVBot()
twitch_bot.connect_bot()
twitch_bot.join_chat(THE_STREAMER)


# #################################### New Thread: TwitchBot #################################### #
def call_the_bot():
    url = f"https://tmi.twitch.tv/group/user/{THE_STREAMER}/chatters"
    while True:
        # Calls the TwitchBOT
        twitch_bot.get_the_special_ones(url)
        twitch_bot.get_chatter()

        pygame.time.delay(100)


TTVBot_THREAD = threading.Thread(target=call_the_bot)
TTVBot_THREAD.setDaemon(True)
TTVBot_THREAD.start()

print("""

Verschieben:  
"Windows-Taste" + "Shift" + "[PFEILTASTE]"

Schließen:
"Alt" + "F4"
"ENTF"
"BACKSLASH"
"ESC"

Der BOT trennt die Verbindung sobald das Programm sich schließt.
Wenn du es zu schnell / oft hintereinander startest kommt es zu einem Fehler..
einfach nochmal neustarten.

""")


# #################################### MAIN GAME LOOP #################################### #
while running:
    # Using Delta Time to get FPS independence
    current_dt = clock.tick(FPS)

    # Handles Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            twitch_bot.disconnect_bot()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                twitch_bot.disconnect_bot()
                sys.exit()

    # Draws the background-image
    Background(current_dt)

    # lets Bot send a Pong every 5 min
    if twitch_bot.PONGTIMER < 0:
        twitch_bot.send_pong()

    # Collects Chatters from the Bot
    # TODO: FIX that MAX_WAITING_PLAYERS is pypassed if list_current_current is too big
    if len(spawner.PLANES_WAITLIST) < MAX_WAITING_PLANES:
        if len(twitch_bot.list_chatters_current) > 0:
            for chatter in twitch_bot.list_chatters_current:
                chatter_status = "VIEWER"
                if twitch_bot.list_chatters_vip.count(chatter) > 0:
                    chatter_status = "VIP"
                elif twitch_bot.list_chatters_mod.count(chatter) > 0:
                    chatter_status = "MOD"

                # Creates a new plane and appends it to a list
                spawner.create_plane(chatter, chatter_status)
            twitch_bot.reset_list()

    # Spawns a PLANE
    if spawner.SPAWNTIMER < 0:
        if len(spawner.PLANES_WAITLIST) > 0 and len(spawner.LIST_OF_FLYING_PLANES) < spawner.MAX_FLYING_PLANES:
            spawner.spawn_plane()
            spawner.reset_spawntimer()
        elif len(spawner.PLANES_WAITLIST) == 0 and len(spawner.LIST_OF_FLYING_PLANES) < spawner.MAX_FLYING_PLANES:
            spawner.create_plane("   ", "EMPTY")
            spawner.spawn_plane()
            spawner.reset_spawntimer()

    # Updates all PLANES
    dead_plane = False
    for plane in spawner.LIST_OF_FLYING_PLANES:
        if plane.DEAD:
            dead_plane = True
        else:
            plane(current_dt)

    # Deletes "DEAD" PLANES
    if dead_plane:
        spawner.delete_dead_planes()

    # needed
    twitch_bot.PONGTIMER -= current_dt
    spawner.SPAWNTIMER -= current_dt
    pygame.display.update()
