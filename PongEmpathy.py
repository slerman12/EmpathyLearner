import math
import random
import sys
import pygame as pg
import euclid
import numpy as np
from shapely.geometry import Point, LineString
from shapely.geometry import box
from shapely.affinity import rotate


class Pong:
    def __init__(self, screen_size, fps_limit):
        self.state_space = dict(type='float', shape=screen_size)

        self.screen_width, self.screen_height = screen_size

        self.screen = pg.display.set_mode(screen_size)

        self.fps_limit = fps_limit

        self.clock = pg.time.Clock()

        self.dtime = None

        pg.display.set_caption('Empathy in Pong')

        self.empathizer = Paddle(self, [[0, 2], [0, 2], [0, 2]], euclid.Vector2(self.screen_width / 2, self.screen_width / 80),
                                 self.screen_width / 40, self.screen_height / 5,
                                 90, euclid.Vector3(250, 250, 250), (255, 0, 0), None)
        self.agent = Paddle(self, [[0, 0], [0, 2], [0, 2]], euclid.Vector2(self.screen_width - self.screen_height / 10, self.screen_height / 2),
                            self.screen_width / 40,
                            self.screen_height / 5, 0, euclid.Vector3(200, 200, 200), (0, 0, 0), None, None, True)
        self.opponent = Paddle(self, [[0, 0], [0, 2], [0, 2]], euclid.Vector2(self.screen_height / 10, self.screen_height / 2),
                               self.screen_width / 40, self.screen_height / 5,
                               0, euclid.Vector3(200, 200, 200), (0, 0, 0), None, self.agent, True)

        self.agent.my_opponent = self.opponent
        self.empathizer.others = [self.agent, self.opponent]
        self.agent.others = [self.empathizer, self.opponent]
        self.opponent.others = [self.agent, self.empathizer]

        self.ball = Ball(self, self.screen_width / 60, 400, (0, 0, 255))

        self.run_me = True

    def play(self):
        while self.run_me:
            self.execute([2, 2, 2], self.empathizer)

        self.close()

    def execute(self, action, who):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.run_me = False

        dtime_ms = self.clock.tick(self.fps_limit)
        self.dtime = dtime_ms / 1000.0

        self.screen.fill((255, 255, 255))

        self.ball.move()

        if self.ball.position.y > self.opponent.position.y + self.ball.size:
            self.opponent.move([0, 1, 0])
        elif self.ball.position.y < self.opponent.position.y - self.ball.size:
            self.opponent.move([0, --1, 0])
        else:
            self.opponent.move([0, 0, 0])

        # if self.ball.position.y > self.agent.position.y + self.ball.size:
        #     self.agent.move([0, 1, 0])
        # elif self.ball.position.y < self.agent.position.y - self.ball.size:
        #     self.agent.move([0, -1, 0])
        # else:
        #     self.agent.move([0, 0, 0])

        who.move(action)

        # for paddle in who.others:
        #     paddle.move(paddle.sample_action())

        keys = pg.key.get_pressed()

        if keys[pg.K_SPACE]:
            self.ball.position.x = self.screen_width / 2
            self.ball.position.y = self.screen_height / 2
            self.ball.velocity = self.ball.get_random_velocity(0, math.pi * 2)
            if self.ball.paddle_collision(self.empathizer):
                self.ball.position.x = self.ball.position.x + self.empathizer.max_length + self.ball.size / 2
                self.ball.position.y = self.ball.position.y + self.empathizer.max_length + self.ball.size / 2
        #
        # self.empathizer.move([
        #     -self.dtime * self.empathizer.speed.x if keys[pg.K_LEFT] else self.dtime * self.empathizer.speed.x if keys[
        #         pg.K_RIGHT] else 0,
        #     -self.dtime * self.empathizer.speed.y if keys[pg.K_UP] else self.dtime * self.empathizer.speed.y if keys[
        #         pg.K_DOWN] else 0,
        #     self.dtime * self.empathizer.speed.z if keys[pg.K_a] else -self.dtime * self.empathizer.speed.z if keys[
        #         pg.K_d] else 0])

        self.agent.set_emotion(score_need=self.agent.score_need - self.dtime * 0.4)
        self.agent.set_emotion(return_need=self.agent.return_need - self.dtime * 0.4)
        self.opponent.set_emotion(score_need=self.opponent.score_need - self.dtime * 0.4)
        self.opponent.set_emotion(return_need=self.opponent.return_need - self.dtime * 0.4)

        self.agent.display()
        self.opponent.display()
        self.empathizer.display()
        self.ball.display()

        self.screen.unlock()
        pg.display.flip()

        return self.get_state(), np.mean(who.emotion), False

    def get_state(self):
        return pg.surfarray.array3d(self.screen)

    def reset(self):
        self.ball.position.x = self.screen_width / 2
        self.ball.position.y = self.screen_height / 2
        self.ball.velocity = self.ball.get_random_velocity(0, math.pi * 2)
        if self.ball.paddle_collision(self.empathizer):
            self.ball.position.x = self.ball.position.x + self.empathizer.max_length + self.ball.size / 2
            self.ball.position.y = self.ball.position.y + self.empathizer.max_length + self.ball.size / 2
        self.empathizer.position = euclid.Vector2(self.screen_width / 2, self.screen_width / 80)
        self.agent = euclid.Vector2(self.screen_width - self.screen_height / 10, self.screen_height / 2)
        self.opponent = euclid.Vector2(self.screen_height / 10, self.screen_height / 2)

    def close(self):
        pg.quit()
        sys.exit()


class Ball:
    def __init__(self, pong, size, speed, color=(255, 255, 255)):
        self.pong = pong

        # Set attributes
        self.position = euclid.Vector2(self.pong.screen_width / 2, self.pong.screen_height / 2)
        self.size = size
        self.color = color
        self.speed = speed
        self.velocity = self.get_random_velocity(math.pi * 3 / 10, math.pi * 7 / 10)

        # Set geometrical representation
        self.geometry = None

    def display(self):
        rx, ry = int(self.position.x), int(self.position.y)
        pg.draw.circle(self.pong.screen, self.color, (rx, ry), self.size)
        pg.draw.circle(self.pong.screen, (0, 0, 0), (rx, ry), self.size, int(self.size / 7))

    def update_geometry(self):
        p = Point(self.position.x, self.position.y)
        self.geometry = p.buffer(self.size)

    def move(self):
        self.position += self.velocity * self.pong.dtime
        self.bounds()

    def bounds(self):
        # Horizontal bounds
        if self.position.x > self.pong.screen_width + self.size or self.position.x + self.size < 0:
            if self.position.x > self.pong.screen_width:
                self.pong.opponent.score += 1
                self.pong.opponent.set_emotion(score_need=self.pong.opponent.score_need + 5)
                self.pong.agent.set_emotion(score_need=self.pong.agent.score_need - 3)
                self.pong.agent.set_emotion()
            elif self.position.x < 0:
                self.pong.agent.score += 1
                self.pong.agent.set_emotion(score_need=self.pong.agent.score_need + 5)
                self.pong.opponent.set_emotion(score_need=self.pong.opponent.score_need - 3)

            self.position.x = self.pong.screen_width / 2
            self.position.y = self.pong.screen_height / 2
            if random.randint(0, 1) == 0:
                self.velocity = -(self.position - self.pong.agent.position).normalize() * self.speed
            else:
                self.velocity = -(self.position - self.pong.opponent.position).normalize() * self.speed

            if self.paddle_collision(self.pong.empathizer):
                self.position.x = self.position.x + self.pong.empathizer.max_length + self.size / 2
                self.position.y = self.position.y + self.pong.empathizer.max_length + self.size / 2

            return

        # Vertical bounds
        if self.position.y <= self.size:
            self.position.y = 2 * self.size - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))
        elif self.position.y >= self.pong.screen_height - self.size:
            self.position.y = 2 * (self.pong.screen_height - self.size) - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

        position_previous = self.position

        def unfreeze(pos):
            # Frozen ball
            if pos == position_previous:
                self.velocity = self.get_random_velocity(0, 2 * math.pi)

        # Paddle collisions
        if self.paddle_collision(self.pong.agent):
            self.pong.agent.set_emotion(return_need=self.pong.agent.return_need + 2)
            unfreeze(self.position)
        if self.paddle_collision(self.pong.opponent):
            self.pong.opponent.set_emotion(return_need=self.pong.opponent.return_need + 2)
            unfreeze(self.position)
        if self.paddle_collision(self.pong.empathizer):
            unfreeze(self.position)

    def is_collision(self):
        # Vertical bounds
        if self.position.y <= self.size:
            return True
        elif self.position.y >= self.pong.screen_height - self.size:
            return True

        # Function to test if there's a paddle collision
        def is_paddle_collision(other):
            if self.ball_in_paddle_range(other):
                #  Update geometries
                other.update_geometry()
                self.update_geometry()

                # If corner
                if self.geometry.intersects(other.geometry):
                    return True
                else:
                    return False

        # Paddle collisions
        return is_paddle_collision(self.pong.agent) or is_paddle_collision(self.pong.opponent) or is_paddle_collision(
            self.pong.empathizer)

    def ball_in_paddle_range(self, p):
        return p.position.x + p.max_length // 2 + self.size > self.position.x > p.position.x - p.max_length // 2 - self.size and \
               p.position.y + p.max_length // 2 + self.size > self.position.y > p.position.y - p.max_length // 2 - self.size

    def get_random_velocity(self, range_min, range_max):
        new_angle = random.uniform(range_min, range_max)
        new_x = math.sin(new_angle)
        new_y = math.cos(new_angle)
        new_vector = euclid.Vector2(new_x, new_y)
        new_vector.normalize()
        new_vector *= self.speed
        return new_vector

    # Collision between ball and paddle
    def paddle_collision(self, other):
        if self.ball_in_paddle_range(other):
            other.update_geometry()
            paddle_coords = other.geometry.exterior.coords

            self.update_geometry()

            # If corner
            for i in range(4):
                if self.geometry.contains(Point(paddle_coords[i])):
                    self.position -= self.velocity * self.pong.dtime
                    self.velocity.x = self.position.x - paddle_coords[0][0]
                    self.velocity.y = self.position.y - paddle_coords[0][1]
                    self.velocity = self.velocity.normalize() * self.speed
                    return True

            # If side
            if LineString([paddle_coords[0], paddle_coords[1]]).intersects(self.geometry):
                normal_vector = euclid.Vector2(-paddle_coords[1][1] + paddle_coords[0][1],
                                               paddle_coords[1][0] - paddle_coords[0][0]).normalize()

                self.position -= self.velocity * self.pong.dtime
                self.velocity = self.velocity.reflect(normal_vector)
                return True
            elif LineString([paddle_coords[1], paddle_coords[2]]).intersects(self.geometry):
                normal_vector = euclid.Vector2(-paddle_coords[2][1] + paddle_coords[1][1],
                                               paddle_coords[2][0] - paddle_coords[1][0]).normalize()
                self.position -= self.velocity * self.pong.dtime
                self.velocity = self.velocity.reflect(normal_vector)
                return True
            elif LineString([paddle_coords[2], paddle_coords[3]]).intersects(self.geometry):
                normal_vector = euclid.Vector2(-paddle_coords[3][1] + paddle_coords[2][1],
                                               paddle_coords[3][0] - paddle_coords[2][0]).normalize()
                self.position -= self.velocity * self.pong.dtime
                self.velocity = self.velocity.reflect(normal_vector)
                return True
            elif LineString([paddle_coords[3], paddle_coords[0]]).intersects(self.geometry):
                normal_vector = euclid.Vector2(-paddle_coords[0][1] + paddle_coords[3][1],
                                               paddle_coords[0][0] - paddle_coords[3][0]).normalize()
                self.position -= self.velocity * self.pong.dtime
                self.velocity = self.velocity.reflect(normal_vector)
                return True

            # No collision
            return False


class Paddle:
    def __init__(self, pong, action_space, position, width, height, degrees, paddle_speed, color, others, my_opponent=None,
                 emotions=False):
        self.pong = pong
        self.action_space = action_space

        self.score = 0

        self.score_need = 0
        self.return_need = 0

        self.position = position
        self.width = int(width)
        self.height = int(height)
        self.degrees = int(degrees)
        self.speed = paddle_speed
        self.color = color
        self.max_length = max(self.width, self.height)
        self.others = others
        self.my_opponent = my_opponent
        self.emotions = emotions
        self.emotion = 0, 0, 0

        self.surf = None
        self.blit = None

        self.geometry = None

    def display(self):
        # Create surface
        self.surf = pg.Surface((int(self.width), int(self.height)))
        self.surf.fill(self.color)
        self.surf.set_colorkey((255, 255, 255))

        border_size = int(self.width / 7)
        if border_size < 1:
            border_size = None

        if border_size is not None:
            for x in range(0, self.width + border_size, border_size):
                pg.draw.rect(self.surf, (0, 0, 0), [x, 0, border_size, border_size])
                pg.draw.rect(self.surf, (0, 0, 0), [x, self.height - border_size, border_size, border_size])

            for x in range(0, self.height + border_size, border_size):
                pg.draw.rect(self.surf, (0, 0, 0), [0, x, border_size, border_size])
                pg.draw.rect(self.surf, (0, 0, 0), [self.width - border_size, x, border_size, border_size])

        # Set orientation
        self.surf = pg.transform.rotate(self.surf, self.degrees)

        # Add to screen
        self.blit = self.pong.screen.blit(self.surf, (self.position.x - self.surf.get_width() // 2, self.position.y -
                                                      self.surf.get_height() // 2))

    def sample_action(self):
        return [random.randint(x[0], x[1]) for x in self.action_space]

    def set_emotion(self, score_need=None, return_need=None):
        if self.emotions:
            if self.score > 0 or self.my_opponent.score > 0:
                score_ratio = self.score / float(self.score + self.my_opponent.score)
            else:
                score_ratio = 0.5

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
            self.color = (int((self.score_need + 5) * 25), int(score_ratio * 250), int((self.return_need + 5) * 25))
            self.emotion = self.score_need, self.return_need, (-0.5 + score_ratio) * 10

    def update_geometry(self):
        # Update geometrical representation
        paddle_unoriented = box(self.position.x - self.width // 2, self.position.y - self.height // 2,
                                self.position.x +
                                self.width // 2, self.position.y + self.height // 2)
        self.geometry = rotate(paddle_unoriented, angle=360 - self.degrees,
                               origin=(self.position.x, self.position.y))

    def move(self, action):
        # Set actions
        right = self.pong.dtime * self.speed.x if action[0] == 2 else -self.pong.dtime * self.speed.x if action[0] == 1 else 0
        down = self.pong.dtime * self.speed.y if action[1] == 2 else -self.pong.dtime * self.speed.y if action[1] == 1 else 0
        counterclockwise = self.pong.dtime * self.speed.z if action[2] == 2 else -self.pong.dtime * self.speed.z if action[2] == 1 else 0

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

        if self != self.pong.empathizer:
            if 20 < self.degrees <= 180:
                self.degrees = 20
            elif 180 < self.degrees < 340:
                self.degrees = 340

            if 20 < self.degrees <= 180:
                self.degrees = 20
            elif 180 < self.degrees < 340:
                self.degrees = 340

    def bounds(self, right, down, counterclockwise):
        # Update geometrical representation
        self.update_geometry()

        # Horizontal and vertical bounds
        if LineString(
                [(-1, -1), (-1, self.pong.screen_height + 1), (self.pong.screen_width + 1, self.pong.screen_height + 1),
                 (self.pong.screen_width + 1, -1), (-1, -1)]).intersects(self.geometry) or self.position.x < 0 \
                or self.position.x > self.pong.screen_width or self.position.y < 0 or self.position.y > self.pong.screen_height:
            return True

        # Update geometrical representation
        self.pong.ball.update_geometry()

        if self.geometry.intersects(self.pong.ball.geometry):
            self.pong.ball.position.x += right
            self.pong.ball.position.y += down

            if self.pong.ball.is_collision():
                self.pong.ball.position.x -= right
                self.pong.ball.position.y -= down
                return True
            else:
                # Taking angle into account (need to consider each side independently)
                self.pong.ball.velocity += euclid.Vector2(right / self.pong.dtime, down / self.pong.dtime)
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

                self.pong.ball.velocity = self.pong.ball.velocity.normalize() * self.pong.ball.speed

        # Inter-paddle bounds
        for paddle in self.others:
            paddle.update_geometry()
            if paddle.geometry.intersects(self.geometry):
                return True

        # No bounds
        return False


# p = Pong((600, 400), 30)
# p.execute([2, 2, 2], p.empathizer)
# p.play()
