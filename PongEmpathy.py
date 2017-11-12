import math
import random
import sys
import pygame as pg
import euclid
from shapely.geometry import Point, LineString
from shapely.geometry import box
from shapely.affinity import rotate


class Ball:
    def __init__(self, size, color=(255, 255, 255)):
        # Set attributes
        self.position = euclid.Vector2(screen_width / 2, screen_height / 2)
        self.size = size
        self.color = color
        self.velocity = get_random_velocity(math.pi * 3 / 10, math.pi * 7 / 10)

        # Set geometrical representation
        self.geometry = None

    def display(self):
        rx, ry = int(self.position.x), int(self.position.y)
        pg.draw.circle(screen, self.color, (rx, ry), self.size)
        pg.draw.circle(screen, black, (rx, ry), self.size, int(self.size/7))

    def update_geometry(self):
        p = Point(self.position.x, self.position.y)
        self.geometry = p.buffer(self.size)

    def move(self):
        self.position += self.velocity * dtime
        self.bounds()

    def bounds(self):
        # Horizontal bounds
        if self.position.x > screen_width + self.size or self.position.x + self.size < 0:
            if self.position.x > screen_width:
                opponent.set_emotion(score_need=opponent.score_need + 1, progress_need=250)
                agent.set_emotion(score_need=agent.score_need - 1)
            elif self.position.x < 0:
                agent.set_emotion(score_need=agent.score_need + 1, progress_need=250)
                opponent.set_emotion(score_need=opponent.score_need - 1)

            self.position.x = screen_width / 2
            self.position.y = screen_height / 2
            if random.randint(0, 1) == 0:
                self.velocity = -(self.position - agent.position).normalize() * initial_velocity
            else:
                self.velocity = -(self.position - opponent.position).normalize() * initial_velocity

            if self.paddle_collision(empathizer):
                self.position.x = self.position.x + empathizer.max_length + self.size / 2
                self.position.y = self.position.y + empathizer.max_length + self.size / 2

            return

        # Vertical bounds
        if self.position.y <= self.size:
            self.position.y = 2 * self.size - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))
        elif self.position.y >= screen_height - self.size:
            self.position.y = 2 * (screen_height - self.size) - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

        position_previous = self.position

        def unfreeze(pos):
            # Frozen ball
            if pos == position_previous:
                self.velocity = get_random_velocity(0, 2 * math.pi)

        # Paddle collisions
        if self.paddle_collision(agent):
            agent.set_emotion(return_need=agent.return_need + 1)
            opponent.set_emotion(return_need=opponent.return_need - 1)
            unfreeze(self.position)
        if self.paddle_collision(opponent):
            agent.set_emotion(return_need=agent.return_need - 1)
            opponent.set_emotion(return_need=opponent.return_need + 1)
            unfreeze(self.position)
        if self.paddle_collision(empathizer):
            unfreeze(self.position)

    def is_collision(self):
        # Vertical bounds
        if self.position.y <= self.size:
            return True
        elif self.position.y >= screen_height - self.size:
            return True

        # Function to test if there's a paddle collision
        def is_paddle_collision(other):
            if ball_in_paddle_range(self, other):
                #  Update geometries
                other.update_geometry()
                self.update_geometry()

                # If corner
                if self.geometry.intersects(other.geometry):
                    return True
                else:
                    return False

        # Paddle collisions
        return is_paddle_collision(agent) or is_paddle_collision(opponent) or is_paddle_collision(empathizer)

    # Collision between ball and paddle
    def paddle_collision(self, other):
        if ball_in_paddle_range(self, other):
            other.update_geometry()
            paddle_coords = other.geometry.exterior.coords

            self.update_geometry()

            # If corner
            for i in range(4):
                if self.geometry.contains(Point(paddle_coords[i])):
                    self.position -= self.velocity * dtime
                    self.velocity.x = self.position.x - paddle_coords[0][0]
                    self.velocity.y = self.position.y - paddle_coords[0][1]
                    self.velocity = self.velocity.normalize() * initial_velocity
                    return True

            # If side
            if LineString([paddle_coords[0], paddle_coords[1]]).intersects(self.geometry):
                normal_vector = euclid.Vector2(-paddle_coords[1][1] + paddle_coords[0][1],
                                               paddle_coords[1][0] - paddle_coords[0][0]).normalize()

                self.position -= self.velocity * dtime
                self.velocity = self.velocity.reflect(normal_vector)
                return True
            elif LineString([paddle_coords[1], paddle_coords[2]]).intersects(self.geometry):
                normal_vector = euclid.Vector2(-paddle_coords[2][1] + paddle_coords[1][1],
                                               paddle_coords[2][0] - paddle_coords[1][0]).normalize()
                self.position -= self.velocity * dtime
                self.velocity = self.velocity.reflect(normal_vector)
                return True
            elif LineString([paddle_coords[2], paddle_coords[3]]).intersects(self.geometry):
                normal_vector = euclid.Vector2(-paddle_coords[3][1] + paddle_coords[2][1],
                                               paddle_coords[3][0] - paddle_coords[2][0]).normalize()
                self.position -= self.velocity * dtime
                self.velocity = self.velocity.reflect(normal_vector)
                return True
            elif LineString([paddle_coords[3], paddle_coords[0]]).intersects(self.geometry):
                normal_vector = euclid.Vector2(-paddle_coords[0][1] + paddle_coords[3][1],
                                               paddle_coords[0][0] - paddle_coords[3][0]).normalize()
                self.position -= self.velocity * dtime
                self.velocity = self.velocity.reflect(normal_vector)
                return True

            # No collision
            return False


class Paddle:
    def __init__(self, position, width, height, degrees, speed, color, others, emotions=False):
        self.score_need = 1
        self.return_need = -1
        self.progress_need = 125

        self.position = position
        self.width = int(width)
        self.height = int(height)
        self.degrees = int(degrees)
        self.speed = speed
        self.color = color
        self.max_length = max(self.width, self.height)
        self.others = others
        self.emotions = emotions

        self.surf = None
        self.blit = None

        self.geometry = None

    def display(self):
        # Create surface
        self.surf = pg.Surface((int(self.width), int(self.height)))
        self.surf.fill(self.color)
        self.surf.set_colorkey((255, 255, 255))

        border_size = int(self.width / 7)

        for x in range(0, self.width + border_size, border_size):
            pg.draw.rect(self.surf, black, [x, 0, border_size, border_size])
            pg.draw.rect(self.surf, black, [x, self.height - 2, 2, 2])

        for x in range(0, self.height + border_size, border_size):
            pg.draw.rect(self.surf, black, [0, x, border_size, border_size])
            pg.draw.rect(self.surf, black, [self.width - border_size, x, border_size, border_size])

        # Set orientation
        self.surf = pg.transform.rotate(self.surf, self.degrees)

        # Add to screen
        self.blit = screen.blit(self.surf, (self.position.x - self.surf.get_width() // 2, self.position.y -
                                            self.surf.get_height() // 2))

    def set_emotion(self, score_need=None, return_need=None, progress_need=None):
        if self.emotions:
            if progress_need is not None:
                self.progress_need = progress_need
                if self.progress_need > 250:
                    self.progress_need = 250
                elif self.progress_need < 0:
                    self.progress_need = 0

            if return_need is not None:
                self.return_need = return_need
                if self.return_need > 5:
                    self.return_need = 5
                elif self.return_need < -5:
                    self.return_need = -5

            if score_need is not None:
                self.score_need = score_need
                if self.score_need > 5:
                    self.score_need = 5
                elif self.score_need < -5:
                    self.score_need = -5

        # Set emotion
        self.color = (int(self.progress_need), int(self.return_need + 5) * 25, int(self.score_need + 5) * 25)

    def update_geometry(self):
        # Update geometrical representation
        paddle_unoriented = box(self.position.x - self.width // 2, self.position.y - self.height // 2,
                                self.position.x +
                                self.width // 2, self.position.y + self.height // 2)
        self.geometry = rotate(paddle_unoriented, angle=360 - self.degrees, origin=(self.position.x, self.position.y))

    def move(self, right, down, counterclockwise):
        # Update position and orientation
        self.degrees = (self.degrees + counterclockwise) % 360
        self.position.x = self.position.x + right
        self.position.y = self.position.y + down

        # Test bounds
        if self.bounds(right, down, counterclockwise):
            # Update position and orientation
            self.degrees = (self.degrees - counterclockwise) % 360
            self.position.x = self.position.x - right
            self.position.y = self.position.y - down

    def bounds(self, right, down, counterclockwise):
        # Update geometrical representation
        self.update_geometry()

        # Horizontal and vertical bounds
        if LineString([(-1, -1), (-1, screen_height + 1), (screen_width + 1, screen_height + 1),
                       (screen_width + 1, -1), (-1, -1)]).intersects(self.geometry):
            return True

        # Update geometrical representation
        ball.update_geometry()

        if self.geometry.intersects(ball.geometry):
            ball.position.x += right
            ball.position.y += down

            if ball.is_collision():
                ball.position.x -= right
                ball.position.y -= down
                return True
            else:
                # Taking angle into account (need to consider each side independently)
                ball.velocity += euclid.Vector2(right /dtime, down / dtime)
                # TODO: Add more realistic force physics
                # paddle_coords = self.geometry.exterior.coords
                # if LineString([paddle_coords[0], paddle_coords[1]]).intersects(self.geometry):
                #     ball.velocity.x = right * math.cos(self.degrees)
                #     ball.velocity.y = down * math.sin(self.degrees)
                # elif LineString([paddle_coords[1], paddle_coords[2]]).intersects(self.geometry):
                #     ball.velocity.x = right * math.cos(self.degrees)
                #     ball.velocity.y = down * math.sin(self.degrees)
                # elif LineString([paddle_coords[2], paddle_coords[3]]).intersects(self.geometry):
                #     ball.velocity.x = right * math.cos(self.degrees)
                #     ball.velocity.y = down * math.sin(self.degrees)
                # elif LineString([paddle_coords[3], paddle_coords[0]]).intersects(self.geometry):
                #     ball.velocity.x = right * math.cos(self.degrees)
                #     ball.velocity.y = down * math.sin(self.degrees)

                ball.velocity = ball.velocity.normalize() * initial_velocity

        # Inter-paddle bounds
        for paddle in self.others:
            paddle.update_geometry()
            if paddle.geometry.intersects(self.geometry):
                return True

        # No bounds
        return False


def get_random_velocity(range_min, range_max):
    new_angle = random.uniform(range_min, range_max)
    new_x = math.sin(new_angle)
    new_y = math.cos(new_angle)
    new_vector = euclid.Vector2(new_x, new_y)
    new_vector.normalize()
    new_vector *= initial_velocity
    return new_vector


def ball_in_paddle_range(b, p):
    return p.position.x + p.max_length // 2 + b.size > b.position.x > p.position.x - p.max_length // 2 - b.size and \
           p.position.y + p.max_length // 2 + b.size > b.position.y > p.position.y - p.max_length // 2 - b.size


if __name__ == "__main__":
    black = 0, 0, 0
    white = 255, 255, 255
    red = 255, 0, 0
    green = 0, 255, 0
    blue = 0, 0, 255

    initial_velocity = 300

    screen_size = screen_width, screen_height = 600, 400

    screen = pg.display.set_mode(screen_size)

    clock = pg.time.Clock()

    pg.display.set_caption('Empathy in Pong')

    empathizer = Paddle(euclid.Vector2(screen_width / 2, screen_width / 80), screen_width / 40, screen_height / 5, 90,
                        euclid.Vector3(200, 200, 200), red, None)
    agent = Paddle(euclid.Vector2(screen_width - screen_height / 10, screen_height / 2), screen_width / 40,
                   screen_height / 5, 0, euclid.Vector3(200, 200, 200), black, None, True)
    opponent = Paddle(euclid.Vector2(screen_height / 10, screen_height / 2), screen_width / 40, screen_height / 5, 0,
                      euclid.Vector3(200, 200, 200), black, None, True)

    empathizer.others = [agent, opponent]
    agent.others = [empathizer, opponent]
    opponent.others = [agent, empathizer]

    ball = Ball(screen_width / 60, blue)

    fps_limit = 60
    run_me = True
    while run_me:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                run_me = False

        dtime_ms = clock.tick(fps_limit)
        dtime = dtime_ms / 1000.0

        screen.fill(white)

        ball.move()

        if ball.position.y > opponent.position.y + ball.size:
            opponent.move(0, dtime*opponent.speed.y, 0)
        elif ball.position.y < opponent.position.y - ball.size:
            opponent.move(0, -dtime*opponent.speed.y, 0)
        else:
            opponent.move(0, 0, 0)

        if ball.position.y > agent.position.y + ball.size:
            agent.move(0, dtime*agent.speed.y, 0)
        elif ball.position.y < agent.position.y - ball.size:
            agent.move(0, -dtime*agent.speed.y, 0)
        else:
            agent.move(0, 0, 0)

        keys = pg.key.get_pressed()

        if keys[pg.K_SPACE]:
            ball.position.x = screen_width / 2
            ball.position.y = screen_height / 2
            ball.velocity = get_random_velocity(0, math.pi * 2)
            if ball.paddle_collision(empathizer):
                ball.position.x = ball.position.x + empathizer.max_length + ball.size / 2
                ball.position.y = ball.position.y + empathizer.max_length + ball.size / 2

        empathizer.move(-dtime*empathizer.speed.x if keys[pg.K_LEFT] else dtime*empathizer.speed.x if keys[pg.K_RIGHT] else 0,
                        -dtime*empathizer.speed.y if keys[pg.K_UP] else dtime*empathizer.speed.y if keys[pg.K_DOWN] else 0,
                        dtime*empathizer.speed.z if keys[pg.K_a] else -dtime*empathizer.speed.z if keys[pg.K_d] else 0)

        if 20 < agent.degrees <= 180:
            agent.degrees = 20
        elif 180 < agent.degrees < 340:
            agent.degrees = 340

        if 20 < opponent.degrees <= 180:
            agent.degrees = 20
        elif 180 < opponent.degrees < 340:
            agent.degrees = 340

        agent.set_emotion(progress_need=agent.progress_need - .25)
        opponent.set_emotion(progress_need=opponent.progress_need - .25)

        agent.display()
        opponent.display()
        empathizer.display()
        ball.display()

        screen.unlock()
        pg.display.flip()

    pg.quit()
    sys.exit()
