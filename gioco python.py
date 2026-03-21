import arcade
import random
import math

# --- Costanti ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Infinite Runner: Dash, Scia e Nuvole"

GRAVITY = 0.8
PLAYER_JUMP_SPEED = 15
PLAYER_MOVEMENT_SPEED = 8

# Costanti Dash
DASH_FORCE = 25        # Potenza della spinta
DASH_DURATION = 0.15   # Quanto dura la spinta (secondi)
DASH_COOLDOWN = 1.0    # Tempo di ricarica tra un dash e l'altro

# Costanti Nuvole
CLOUD_COUNT_INITIAL = 15  # Numero di nuvole all'avvio
CLOUD_PARALLAX_X = 0.3    # Velocità orizzontale nuvole (0.3 = 30% della velocità del mondo)
CLOUD_PARALLAX_Y = 0.1    # Velocità verticale nuvole

class DashAfterimage:
    """Classe di supporto per gestire i singoli frammenti della scia."""
    def __init__(self, x, y, angle, color):
        self.x = x
        self.y = y
        self.angle = angle
        self.alpha = 180  # Trasparenza iniziale
        self.scale = 1.0  # Dimensione iniziale
        self.color = color

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        self.player_list = None
        self.wall_list = None
        self.spike_list = None
        self.cloud_list = None # Lista per le nuvole
        
        self.player_sprite = None
        self.physics_engine = None
        
        self.camera_mondo = None
        self.camera_nuvole = None # Telecamera separata per l'effetto parallasse
        self.camera_ui = None 
        
        self.score = 0
        self.last_platform_x = 0
        self.last_cloud_x = 0 # Traccia l'ultima nuvola generata
        
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        
        self.jump_count = 0
        
        # Variabili Dash
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_trail = [] # Lista per contenere i frammenti della scia

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.spike_list = arcade.SpriteList()
        self.cloud_list = arcade.SpriteList() # Inizializza la lista nuvole
        
        self.camera_mondo = arcade.camera.Camera2D()
        self.camera_nuvole = arcade.camera.Camera2D() # Inizializza telecamera nuvole
        self.camera_ui = arcade.camera.Camera2D()
        
        self.score = 0
        self.jump_count = 0 
        self.is_dashing = False
        self.dash_cooldown_timer = 0
        self.dash_trail = []
        self.last_cloud_x = 0
        
        self.left_pressed = self.right_pressed = self.up_pressed = self.down_pressed = False

        # --- Creazione Personaggio ---
        try:
            self.player_sprite = arcade.Sprite(":resources:images/animated_characters/alien_green/alienGreen_jump.png", scale=0.5)
        except Exception:
            self.player_sprite = arcade.SpriteSolidColor(32, 48, arcade.color.GREEN)
        
        self.player_sprite.center_x = 200
        self.player_sprite.center_y = 450 
        self.player_list.append(self.player_sprite)

        # --- Creazione Mondo Iniziale ---
        self.last_platform_x = 500
        self.create_platform(500, 150, 50, can_have_spike=False)

        # --- Creazione Nuvole Iniziali ---
        self.last_cloud_x = SCREEN_WIDTH # Inizia a generare oltre lo schermo
        for i in range(CLOUD_COUNT_INITIAL):
            # Posiziona le nuvole iniziali sparse per il mondo
            x = random.randint(0, SCREEN_WIDTH * 2)
            self.create_cloud(x)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def create_cloud(self, x_pos):
        """Crea una nuvola semitrasparente a una posizione X specifica."""
        try:
            # Usa una delle risorse nuvola disponibili
            cloud_types = [
                ":resources:images/tiles/cloud1.png",
                ":resources:images/tiles/cloud2.png",
                ":resources:images/tiles/cloud3.png"
            ]
            cloud_path = random.choice(cloud_types)
            scale = random.uniform(0.5, 1.2)
            cloud = arcade.Sprite(cloud_path, scale=scale)
        except Exception:
            # Fallback se le risorse non caricano
            width = random.randint(60, 150)
            height = random.randint(30, 80)
            cloud = arcade.SpriteSolidColor(width, height, arcade.color.WHITE)

        # Posizionamento
        cloud.center_x = x_pos
        # Le nuvole stanno nella parte alta dello schermo, ma con variazioni
        cloud.center_y = random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT + 100)
        
        # Trasparenza (molto importante per l'estetica)
        cloud.alpha = random.randint(100, 200) # Semitrasparente
        
        self.cloud_list.append(cloud)
        
        # Aggiorna l'X dell'ultima nuvola
        if x_pos > self.last_cloud_x:
            self.last_cloud_x = x_pos

    def create_platform(self, center_x, y, num_blocks, can_have_spike=True):
        tile_size = 32
        start_x = center_x - (num_blocks * tile_size) / 2
        for i in range(num_blocks):
            try:
                wall = arcade.Sprite(":resources:images/tiles/grassMid.png", scale=0.5)
            except Exception:
                wall = arcade.SpriteSolidColor(32, 32, arcade.color.BROWN)
            wall.center_x = start_x + (i * tile_size)
            wall.center_y = y
            self.wall_list.append(wall)

        if can_have_spike and random.random() < 0.4:
            try:
                spike = arcade.Sprite(":resources:images/tiles/spikesHigh.png", scale=0.8)
                spike.color = arcade.color.GRAY
            except Exception:
                spike = arcade.SpriteSolidColor(40, 50, arcade.color.GRAY)
            
            block_index = random.randint(2, num_blocks - 3)
            spike.center_x = start_x + (block_index * tile_size)
            spike.bottom = y + 16
            self.spike_list.append(spike)

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.SKY_BLUE)
        
        # --- 1. DISEGNO NUVOLE (con la loro telecamera parallasse) ---
        self.camera_nuvole.use()
        self.cloud_list.draw()
        
        # --- 2. DISEGNO MONDO (con telecamera principale) ---
        self.camera_mondo.use()
        
        # Disegno Scia (Sotto il giocatore)
        for fragment in self.dash_trail:
            color = (255, 255, 255, int(fragment.alpha))
            arcade.draw_triangle_filled(
                fragment.x, fragment.y + (15 * fragment.scale),
                fragment.x - (15 * fragment.scale), fragment.y - (15 * fragment.scale),
                fragment.x + (15 * fragment.scale), fragment.y - (15 * fragment.scale),
                color
            )

        self.wall_list.draw()
        for spike in self.spike_list:
            if isinstance(spike, arcade.SpriteSolidColor):
                arcade.draw_triangle_filled(spike.left, spike.bottom, spike.right, spike.bottom, spike.center_x, spike.top, arcade.color.GRAY)
            else:
                spike.draw()
        
        if self.is_dashing:
            self.player_sprite.draw_hit_box(arcade.color.WHITE, 2)
            
        self.player_list.draw()
        
        # --- 3. DISEGNO UI (statica) ---
        self.camera_ui.use()
        arcade.draw_text(f"DISTANZA: {int(self.score)}m", 30, SCREEN_HEIGHT - 50, arcade.color.BLACK, 24, bold=True)
        
        # Barra del Dash
        testo_dash = "DASH PRONTO (C)" if self.dash_cooldown_timer <= 0 else "DASH IN RICARICA..."
        colore_dash = arcade.color.GREEN if self.dash_cooldown_timer <= 0 else arcade.color.RED
        arcade.draw_text(testo_dash, 30, SCREEN_HEIGHT - 80, colore_dash, 16, bold=True)

    def on_key_press(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.UP]: self.up_pressed = True
        elif key in [arcade.key.S, arcade.key.DOWN]: self.down_pressed = True
        elif key in [arcade.key.A, arcade.key.LEFT]: self.left_pressed = True
        elif key in [arcade.key.D, arcade.key.RIGHT]: self.right_pressed = True
        
        # Salto
        if key in [arcade.key.W, arcade.key.SPACE, arcade.key.UP]:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.jump_count = 1
            elif self.jump_count < 2:
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.jump_count = 2

        # Tasto Dash
        if key == arcade.key.C and self.dash_cooldown_timer <= 0:
            self.start_dash()

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.UP]: self.up_pressed = False
        elif key in [arcade.key.S, arcade.key.DOWN]: self.down_pressed = False
        elif key in [arcade.key.A, arcade.key.LEFT]: self.left_pressed = False
        elif key in [arcade.key.D, arcade.key.RIGHT]: self.right_pressed = False

    def start_dash(self):
        dx, dy = 0, 0
        if self.right_pressed: dx = 1
        elif self.left_pressed: dx = -1
        
        if self.up_pressed: dy = 1
        elif self.down_pressed: dy = -1
        
        if dx == 0 and dy == 0: dx = 1
        
        self.player_sprite.change_x = dx * DASH_FORCE
        self.player_sprite.change_y = dy * DASH_FORCE
        
        self.is_dashing = True
        self.dash_timer = DASH_DURATION
        self.dash_cooldown_timer = DASH_COOLDOWN

    def on_update(self, delta_time):
        # Gestione Cooldown
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= delta_time

        # Gestione Scia
        for fragment in self.dash_trail[:]:
            fragment.alpha -= 10  # Svanisce
            fragment.scale -= 0.05 # Rimpicciolisce
            if fragment.alpha <= 0 or fragment.scale <= 0:
                self.dash_trail.remove(fragment)

        if self.is_dashing:
            # Crea un nuovo frammento di scia
            new_fragment = DashAfterimage(
                self.player_sprite.center_x, 
                self.player_sprite.center_y, 
                0, 
                arcade.color.WHITE
            )
            self.dash_trail.append(new_fragment)

            self.dash_timer -= delta_time
            if self.dash_timer <= 0:
                self.is_dashing = False
        else:
            # Movimento normale
            self.player_sprite.change_x = 0
            if self.right_pressed and not self.left_pressed:
                self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
            elif self.left_pressed and not self.right_pressed:
                self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
            
            if self.physics_engine.can_jump():
                self.jump_count = 0

        self.physics_engine.update()
        
        # --- Aggiorna Telecamera Principale ---
        target_x = max(self.player_sprite.center_x, SCREEN_WIDTH / 2)
        target_y = max(self.player_sprite.center_y + 80, SCREEN_HEIGHT / 2 - 100)
        cam_x, cam_y = self.camera_mondo.position
        # Lerp per inseguimento fluido
        new_cam_x = arcade.math.lerp(cam_x, target_x, 0.1)
        new_cam_y = arcade.math.lerp(cam_y, target_y, 0.1)
        self.camera_mondo.position = (new_cam_x, new_cam_y)
        
        # --- Aggiorna Telecamera Nuvole (Effetto Parallasse) ---
        # Spostiamo la telecamera nuvole solo di una frazione di quella principale
        cloud_cam_x = new_cam_x * CLOUD_PARALLAX_X
        #cloud_cam_y = new_cam_y * CLOUD_PARALLAX_Y # Opzionale, spesso il parallasse verticale è fastidioso nei platform
        self.camera_nuvole.position = (cloud_cam_x, new_cam_y) # Manteniamo l'Y originale o le nuvole scenderanno

        if self.player_sprite.center_x / 10 > self.score:
            self.score = self.player_sprite.center_x / 10

        # --- Mondo infinito (Piattaforme) ---
        if self.player_sprite.center_x + SCREEN_WIDTH > self.last_platform_x:
            gap = random.randint(160, 320)
            new_y = random.randint(150, 500)
            num_tiles = random.randint(8, 15)
            self.last_platform_x += gap + (num_tiles * 32)
            self.create_platform(self.last_platform_x, new_y, num_tiles)
            
        # --- Cielo Infinito (Nuvole) ---
        # Genera nuove nuvole man mano che il giocatore avanza
        # Usiamo target_x perché è dove la telecamera sta andando
        if target_x + SCREEN_WIDTH > self.last_cloud_x:
            # Aggiungi una nuvola ogni tanto
            if random.random() < 0.05: # 5% di probabilità per frame di generare una nuvola
                 # Genera la nuvola un po' oltre il bordo destro della telecamera del mondo
                 self.create_cloud(target_x + SCREEN_WIDTH + random.randint(0, 300))

        # --- Morte ---
        limite_inf = self.camera_mondo.position[1] - (SCREEN_HEIGHT / 2) - 50
        if arcade.check_for_collision_with_list(self.player_sprite, self.spike_list) or self.player_sprite.top < limite_inf:
            self.setup()

def main():
    game = MyGame()
    game.setup()
    arcade.run()

if __name__ == "__main__":
    main()