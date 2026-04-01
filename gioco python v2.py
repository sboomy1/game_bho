import arcade
import random
import math

# --- Costanti ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Super Fast Runner - Rival Edition"

GRAVITY = 0.8
PLAYER_JUMP_SPEED = 15
PLAYER_MOVEMENT_SPEED = 8

DASH_FORCE = 25         
DASH_DURATION = 0.15    
DASH_COOLDOWN = 1.0     

CLOUD_COUNT_INITIAL = 15   
CLOUD_PARALLAX_X = 0.3     
CLOUD_PARALLAX_Y = 0.1     

COYOTE_TIME = 0.15  

# --- Costanti Nemico ---
ENEMY_SPEED_BASE = 7.9
ENEMY_JUMP_SPEED = 15
ENEMY_DASH_DISTANCE = 350 # Distanza oltre la quale il nemico scatta
ENEMY_DASH_COOLDOWN = 2.0 # Il nemico scatta meno spesso del player

class DashAfterimage:
    def __init__(self, x, y, angle, color):
        self.x = x
        self.y = y
        self.angle = angle
        self.alpha = 180  
        self.scale = 1.0  
        self.color = color

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        self.player_list = None
        self.wall_list = None
        self.spike_list = None
        self.cloud_list = None 
        self.enemy_list = None
        
        self.player_sprite = None
        self.enemy_sprite = None
        self.physics_engine = None
        self.enemy_physics_engine = None 
        
        self.camera_mondo = None
        self.camera_nuvole = None 
        self.camera_ui = None 
        
        self.score = 0
        self.speed_multiplier = 1.0 
        self.last_platform_x = 0
        self.last_cloud_x = 0 
        
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        
        self.jump_count = 0
        self.coyote_timer = 0
        
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        
        # Variabili Dash Nemico
        self.enemy_is_dashing = False
        self.enemy_dash_timer = 0
        self.enemy_dash_cooldown_timer = 0
        
        self.dash_trail = [] 

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.spike_list = arcade.SpriteList()
        self.cloud_list = arcade.SpriteList() 
        self.enemy_list = arcade.SpriteList()
        
        self.camera_mondo = arcade.camera.Camera2D()
        self.camera_nuvole = arcade.camera.Camera2D() 
        self.camera_ui = arcade.camera.Camera2D()
        
        self.score = 0
        self.speed_multiplier = 1.0 
        self.jump_count = 0 
        self.coyote_timer = 0
        self.is_dashing = False
        self.dash_cooldown_timer = 0
        
        # Reset Dash Nemico
        self.enemy_is_dashing = False
        self.enemy_dash_timer = 0
        self.enemy_dash_cooldown_timer = 0
        
        self.dash_trail = []
        self.last_cloud_x = 0
        
        self.left_pressed = self.right_pressed = self.up_pressed = self.down_pressed = False

        try:
            self.player_sprite = arcade.Sprite(":resources:images/animated_characters/alien_green/alienGreen_jump.png", scale=0.5)
        except Exception:
            self.player_sprite = arcade.SpriteSolidColor(32, 48, arcade.color.GREEN)
        
        self.player_sprite.center_x = 200
        self.player_sprite.center_y = 450 
        self.player_list.append(self.player_sprite)

        self.enemy_sprite = arcade.SpriteSolidColor(100, 100, arcade.color.RED)
        self.enemy_sprite.center_x = -50 
        self.enemy_sprite.center_y = 450
        self.enemy_list.append(self.enemy_sprite)

        self.last_platform_x = 500
        self.create_platform(500, 150, 50, can_have_spike=False)

        self.last_cloud_x = SCREEN_WIDTH 
        for i in range(CLOUD_COUNT_INITIAL):
            x = random.randint(0, SCREEN_WIDTH * 2)
            self.create_cloud(x)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )
        
        self.enemy_physics_engine = arcade.PhysicsEnginePlatformer(
            self.enemy_sprite, gravity_constant=GRAVITY, walls=self.wall_list
        )

    def create_cloud(self, x_pos):
        try:
            cloud_types = [":resources:images/tiles/cloud1.png", ":resources:images/tiles/cloud2.png", ":resources:images/tiles/cloud3.png"]
            cloud_path = random.choice(cloud_types)
            scale = random.uniform(0.5, 1.2)
            cloud = arcade.Sprite(cloud_path, scale=scale)
        except Exception:
            cloud = arcade.SpriteSolidColor(random.randint(60, 150), random.randint(30, 80), arcade.color.WHITE)
        cloud.center_x = x_pos
        cloud.center_y = random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT + 100)
        cloud.alpha = random.randint(100, 200) 
        self.cloud_list.append(cloud)
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
        
        self.camera_nuvole.use()
        self.cloud_list.draw()
        
        self.camera_mondo.use()
        
        for fragment in self.dash_trail:
            # Usa il colore specifico del frammento (Bianco per player, Rosso per nemico)
            color = (fragment.color[0], fragment.color[1], fragment.color[2], int(fragment.alpha))
            arcade.draw_triangle_filled(
                fragment.x, fragment.y + (15 * fragment.scale),
                fragment.x - (15 * fragment.scale), fragment.y - (15 * fragment.scale),
                fragment.x + (15 * fragment.scale), fragment.y - (15 * fragment.scale),
                color
            )

        self.wall_list.draw()
        self.enemy_list.draw()
        
        for spike in self.spike_list:
            if isinstance(spike, arcade.SpriteSolidColor):
                arcade.draw_triangle_filled(spike.left, spike.bottom, spike.right, spike.bottom, spike.center_x, spike.top, arcade.color.GRAY)
            else:
                spike.draw()
        
        if self.is_dashing:
            self.player_sprite.draw_hit_box(arcade.color.WHITE, 2)
            
        self.player_list.draw()
        
        self.camera_ui.use()
        arcade.draw_text(f"DISTANZA: {int(self.score)}m", 30, SCREEN_HEIGHT - 50, arcade.color.BLACK, 24, bold=True)
        arcade.draw_text(f"VELOCITÀ: x{self.speed_multiplier:.2f}", 30, SCREEN_HEIGHT - 80, arcade.color.DARK_BLUE, 16, bold=True)
        
        testo_dash = "DASH PRONTO (C)" if self.dash_cooldown_timer <= 0 else "DASH IN RICARICA..."
        colore_dash = arcade.color.GREEN if self.dash_cooldown_timer <= 0 else arcade.color.RED
        arcade.draw_text(testo_dash, 30, SCREEN_HEIGHT - 110, colore_dash, 16, bold=True)

    def on_key_press(self, key, modifiers):
        if key in [arcade.key.W, arcade.key.UP]: self.up_pressed = True
        elif key in [arcade.key.S, arcade.key.DOWN]: self.down_pressed = True
        elif key in [arcade.key.A, arcade.key.LEFT]: self.left_pressed = True
        elif key in [arcade.key.D, arcade.key.RIGHT]: self.right_pressed = True
        
        if key in [arcade.key.W, arcade.key.SPACE, arcade.key.UP]:
            boosted_jump = PLAYER_JUMP_SPEED * (1 + (self.speed_multiplier - 1) * 0.2)
            if self.physics_engine.can_jump() or self.coyote_timer > 0:
                self.player_sprite.change_y = boosted_jump
                self.jump_count = 1
                self.coyote_timer = 0
            elif self.jump_count < 2:
                self.player_sprite.change_y = boosted_jump
                self.jump_count = 2

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
        
        self.player_sprite.change_x = dx * (DASH_FORCE * self.speed_multiplier)
        self.player_sprite.change_y = dy * (DASH_FORCE * self.speed_multiplier)
        self.is_dashing = True
        self.dash_timer = DASH_DURATION
        self.dash_cooldown_timer = DASH_COOLDOWN

    def on_update(self, delta_time):
        self.speed_multiplier = 1.0 + (self.score / 2000)
        self.physics_engine.gravity_constant = GRAVITY * self.speed_multiplier
        self.enemy_physics_engine.gravity_constant = GRAVITY * self.speed_multiplier

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= delta_time
        
        # Update cooldown dash nemico
        if self.enemy_dash_cooldown_timer > 0:
            self.enemy_dash_cooldown_timer -= delta_time

        # Coyote Time Player
        if self.physics_engine.can_jump():
            self.coyote_timer = COYOTE_TIME
            self.jump_count = 0
        else:
            self.coyote_timer -= delta_time

        # --- LOGICA IA DEL NEMICO CON DASH ---
        dist_x = self.player_sprite.center_x - self.enemy_sprite.center_x
        
        if not self.enemy_is_dashing:
            # Decide se scattare
            if abs(dist_x) > ENEMY_DASH_DISTANCE and self.enemy_dash_cooldown_timer <= 0:
                direction = 1 if dist_x > 0 else -1
                self.enemy_sprite.change_x = direction * (DASH_FORCE * self.speed_multiplier)
                self.enemy_is_dashing = True
                self.enemy_dash_timer = DASH_DURATION
                self.enemy_dash_cooldown_timer = ENEMY_DASH_COOLDOWN
            else:
                # Movimento Orizzontale Normale
                enemy_speed = ENEMY_SPEED_BASE * self.speed_multiplier
                if dist_x > 20: self.enemy_sprite.change_x = enemy_speed
                elif dist_x < -20: self.enemy_sprite.change_x = -enemy_speed
                else: self.enemy_sprite.change_x = 0
        else:
            # Gestione durante il dash
            self.enemy_dash_timer -= delta_time
            # Aggiungi scia rossa per il nemico
            self.dash_trail.append(DashAfterimage(self.enemy_sprite.center_x, self.enemy_sprite.center_y, 0, arcade.color.RED))
            if self.enemy_dash_timer <= 0:
                self.enemy_is_dashing = False
                self.enemy_sprite.change_x *= 0.5 # Frenata post-dash

        # Salto Nemico
        if self.enemy_physics_engine.can_jump():
            should_jump = False
            if self.player_sprite.bottom > self.enemy_sprite.top + 50:
                should_jump = True
            
            future_x = self.enemy_sprite.center_x + (self.enemy_sprite.change_x * 10)
            if should_jump or not arcade.get_sprites_at_point((future_x, self.enemy_sprite.bottom - 10), self.wall_list):
                 self.enemy_sprite.change_y = ENEMY_JUMP_SPEED * (1 + (self.speed_multiplier - 1) * 0.2)

        # Update scie (per entrambi)
        for fragment in self.dash_trail[:]:
            fragment.alpha -= 10  
            fragment.scale -= 0.05 
            if fragment.alpha <= 0 or fragment.scale <= 0:
                self.dash_trail.remove(fragment)

        if self.is_dashing:
            self.dash_trail.append(DashAfterimage(self.player_sprite.center_x, self.player_sprite.center_y, 0, arcade.color.WHITE))
            self.dash_timer -= delta_time
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.player_sprite.change_x *= 0.2 # Frenata player
        else:
            self.player_sprite.change_x = 0
            current_move_speed = PLAYER_MOVEMENT_SPEED * self.speed_multiplier
            if self.right_pressed and not self.left_pressed:
                self.player_sprite.change_x = current_move_speed
            elif self.left_pressed and not self.right_pressed:
                self.player_sprite.change_x = -current_move_speed

        self.physics_engine.update()
        self.enemy_physics_engine.update()
        
        # Camera
        target_x = max(self.player_sprite.center_x, SCREEN_WIDTH / 2)
        target_y = max(self.player_sprite.center_y + 80, SCREEN_HEIGHT / 2 - 100)
        cam_x, cam_y = self.camera_mondo.position
        
        lerp_speed = min(0.1 * self.speed_multiplier, 0.25)
        new_cam_x = arcade.math.lerp(cam_x, target_x, lerp_speed)
        new_cam_y = arcade.math.lerp(cam_y, target_y, lerp_speed)
        self.camera_mondo.position = (new_cam_x, new_cam_y)
        
        self.camera_nuvole.position = (new_cam_x * CLOUD_PARALLAX_X, new_cam_y) 

        if self.player_sprite.center_x / 10 > self.score:
            self.score = self.player_sprite.center_x / 10

        # Generazione piattaforme
        if self.player_sprite.center_x + SCREEN_WIDTH > self.last_platform_x:
            gap = random.randint(160, int(320 * self.speed_multiplier))
            new_y = random.randint(150, 500)
            num_tiles = random.randint(8, 15)
            self.last_platform_x += gap + (num_tiles * 32)
            self.create_platform(self.last_platform_x, new_y, num_tiles)
            
        if target_x + SCREEN_WIDTH > self.last_cloud_x:
            if random.random() < 0.05: 
                 self.create_cloud(target_x + SCREEN_WIDTH + random.randint(0, 300))

        # Controllo Sconfitta
        limite_inf = self.camera_mondo.position[1] - (SCREEN_HEIGHT / 2) - 100
        hit_enemy = arcade.check_for_collision(self.player_sprite, self.enemy_sprite)
        hit_spikes = arcade.check_for_collision_with_list(self.player_sprite, self.spike_list)
        
        if self.enemy_sprite.top < limite_inf:
            self.enemy_sprite.center_x = self.player_sprite.center_x - 400
            self.enemy_sprite.center_y = self.player_sprite.center_y + 200
            self.enemy_sprite.change_x = 0
            self.enemy_sprite.change_y = 0

        if hit_enemy or hit_spikes or self.player_sprite.top < limite_inf:
            self.setup()

def main():
    game = MyGame()
    game.setup()
    arcade.run()

if __name__ == "__main__":
    main()