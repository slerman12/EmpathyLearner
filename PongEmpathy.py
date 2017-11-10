import math
import random
import sys
import pygame as pg
import euclid
from shapely.geometry import Point, LineString
from shapely.geometry import box
from shapely.affinity import rotate


class Ball:
    def __init__(self, position, size, color=(255, 255, 255), velocity=euclid.Vector2(0, 0)):
        self.position = position
        self.size = size
        self.color = color
        self.velocity = velocity
        self.position_previous = None

    def display(self):
        rx, ry = int(self.position.x), int(self.position.y)
        pg.draw.circle(screen, self.color, (rx, ry), self.size)

    def change_position(self, new_position):
        self.position_previous = self.position
        self.position = new_position

    def move(self):
        self.change_position(self.position + self.velocity * dtime)
        self.bounce()

    def bounce(self):
        # Horizontal bounds
        if self.position.x > screen_width + self.size or self.position.x + self.size < 0:
            # if self.position.x > screen_width:
            #     agent_score += 1
            #
            # elif self.position.x < 0:
            #     opponent_score += 1

            self.position.x = screen_width / 3
            self.position.y = screen_height / 2
            self.velocity = -(self.position - agent.position).normalize() * initial_velocity
            self.position_previous = None

            if self.paddle_collision(empathizer):
                self.position.x = self.position.x + empathizer.max_length + self.size / 2
                self.position.y = self.position.y + empathizer.max_length + self.size / 2

        # Vertical bounds
        if self.position.y <= self.size:
            self.position.y = 2 * self.size - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))
        elif self.position.y >= screen_height - self.size:
            self.position.y = 2 * (screen_height - self.size) - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

        # Paddle collisions
        self.paddle_collision(agent)
        self.paddle_collision(opponent)
        self.paddle_collision(empathizer)

        # Frozen ball
        if self.position_previous is not None and self.position == self.position_previous:
            self.velocity = get_random_velocity(0, 2 * math.pi)

    # Collision between ball and paddle
    def paddle_collision(self, other):
        if (other.position.x + other.max_length / 2 > self.position.x > other.position.x - other.max_length / 2 and
                other.position.y + other.max_length / 2 > self.position.y > other.position.y - other.max_length / 2):
            paddle_unoriented = box(other.position.x - other.width / 2, other.position.y - other.height / 2,
                                    other.position.x + other.width / 2,
                                    other.position.y + other.height / 2)
            paddle_oriented = rotate(paddle_unoriented, angle=360 - other.degrees,
                                     origin=(other.position.x, other.position.y))
            paddle_coords = paddle_oriented.exterior.coords

            p = Point(self.position.x, self.position.y)
            c = p.buffer(self.size)

            if c.contains(Point(paddle_coords[0])) or \
                    c.contains(Point(paddle_coords[1])) or \
                    c.contains(Point(paddle_coords[2])) or \
                    c.contains(Point(paddle_coords[3])):
                if c.contains(LineString([paddle_coords[0], paddle_coords[1]])):
                    normal_vector = euclid.Vector2(-paddle_coords[1][1] + paddle_coords[0][1],
                                                   paddle_coords[1][0] - paddle_coords[0][0]).normalize()
                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = self.velocity.reflect(normal_vector)
                elif c.contains(LineString([paddle_coords[1], paddle_coords[2]])):
                    normal_vector = euclid.Vector2(-paddle_coords[2][1] + paddle_coords[1][1],
                                                   paddle_coords[2][0] - paddle_coords[1][0]).normalize()
                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = self.velocity.reflect(normal_vector)
                elif c.contains(LineString([paddle_coords[2], paddle_coords[3]])):
                    normal_vector = euclid.Vector2(-paddle_coords[3][1] + paddle_coords[2][1],
                                                   paddle_coords[3][0] - paddle_coords[2][0]).normalize()
                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = self.velocity.reflect(normal_vector)
                elif c.contains(LineString([paddle_coords[3], paddle_coords[0]])):
                    normal_vector = euclid.Vector2(-paddle_coords[0][1] + paddle_coords[3][1],
                                                   paddle_coords[0][0] - paddle_coords[3][0]).normalize()
                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = self.velocity.reflect(normal_vector)
                else:
                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = get_random_velocity(0, 2 * math.pi)
                    return True
            else:
                if LineString([paddle_coords[0], paddle_coords[1]]).intersects(c):
                    normal_vector = euclid.Vector2(-paddle_coords[1][1] + paddle_coords[0][1],
                                                   paddle_coords[1][0] - paddle_coords[0][0]).normalize()

                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = self.velocity.reflect(normal_vector)
                    return True
                elif LineString([paddle_coords[1], paddle_coords[2]]).intersects(c):
                    normal_vector = euclid.Vector2(-paddle_coords[2][1] + paddle_coords[1][1],
                                                   paddle_coords[2][0] - paddle_coords[1][0]).normalize()
                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = self.velocity.reflect(normal_vector)
                    return True
                elif LineString([paddle_coords[2], paddle_coords[3]]).intersects(c):
                    normal_vector = euclid.Vector2(-paddle_coords[3][1] + paddle_coords[2][1],
                                                   paddle_coords[3][0] - paddle_coords[2][0]).normalize()
                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = self.velocity.reflect(normal_vector)
                    return True
                elif LineString([paddle_coords[3], paddle_coords[0]]).intersects(c):
                    normal_vector = euclid.Vector2(-paddle_coords[0][1] + paddle_coords[3][1],
                                                   paddle_coords[0][0] - paddle_coords[3][0]).normalize()
                    self.change_position(self.position - self.velocity * dtime)
                    self.velocity = self.velocity.reflect(normal_vector)
                    return True

            return False


class Paddle:
    def __init__(self, position, width, height, degrees, color, opponent, empathizer):
        self.score = 0
        self.position = position
        self.width = width
        self.height = height
        self.degrees = degrees
        self.color = color
        self.max_length = max(self.width, self.height)
        self.opponent = opponent
        self.empathizer = empathizer

        self.surf = None
        self.blit = None

        paddle_unoriented = box(self.position.x - self.width / 2, self.position.y - self.height / 2, self.position.x +
                                self.width / 2, self.position.y + self.height / 2)
        self.paddle_oriented = rotate(paddle_unoriented, angle=360 - self.degrees,
                                      origin=(self.position.x, self.position.y))

    def display(self):
        # Create surface
        self.surf = pg.Surface((int(self.width), int(self.height)))
        self.surf.fill(self.color)
        self.surf.set_colorkey((255, 255, 255))

        # Set orientation
        self.surf = pg.transform.rotate(self.surf, self.degrees)

        # Add to screen
        self.blit = screen.blit(self.surf, (self.position.x - self.surf.get_width() // 2, self.position.y -
                                            self.surf.get_height() // 2))

    def move(self, right, down, counterclockwise):
        # Update position and orientation
        self.degrees = (self.degrees + counterclockwise) % 360
        self.position.x = self.position.x + right
        self.position.y = self.position.y + down
        self.bounds(right, down, counterclockwise)

    def bounds(self, right, down, counterclockwise):
        # TODO: write is_paddle_in_bounds() function
        if (self.position.x + self.max_length / 2 > ball.position.x > self.position.x - self.max_length / 2 and self.position.y + self.max_length / 2 > ball.position.y > self.position.y - self.max_length / 2) or (self.position.x + self.max_length / 2 > ball.position.x > self.position.x - self.max_length / 2 and self.position.y + self.max_length / 2 > ball.position.y > self.position.y - self.max_length / 2):
            paddle_unoriented = box(self.position.x - self.width / 2, self.position.y - self.height / 2,
                                    self.position.x +
                                    self.width / 2, self.position.y + self.height / 2)
            self.paddle_oriented = rotate(paddle_unoriented, angle=360 - self.degrees,
                                          origin=(self.position.x, self.position.y))

            p = Point(ball.position.x, ball.position.y)
            c = p.buffer(ball.size).boundary

            if self.paddle_oriented.intersects(c):
                self.degrees = (self.degrees - counterclockwise) % 360
                self.position.x = self.position.x - right
                self.position.y = self.position.y - down

        # Horizontal and vertical bounds
        if self.position.x - self.max_length / 2 < 0:
            self.position.x = self.max_length / 2
        if self.position.x + self.max_length / 2 > screen_width:
            self.position.x = screen_width - self.max_length / 2
        if self.position.y - self.max_length / 2 < 0:
            self.position.y = self.max_length / 2
        if self.position.y + self.max_length / 2 > screen_height:
            self.position.y = screen_height - self.max_length / 2

            # if self.paddle_oriented.intersects(agent.paddle_oriented) or self.paddle_oriented.intersects(opponent.paddle_oriented) or self.paddle_oriented.intersects(empathizer.paddle_oriented):
            #     self.degrees = (self.degrees - counterclockwise) % 360
            #     self.position.x = self.position.x - right
            #     self.position.y = self.position.y - down


def get_random_velocity(range_min, range_max):
    new_angle = random.uniform(range_min, range_max)
    new_x = math.sin(new_angle)
    new_y = math.cos(new_angle)
    new_vector = euclid.Vector2(new_x, new_y)
    new_vector.normalize()
    new_vector *= initial_velocity
    return new_vector


if __name__ == "__main__":
    black = 0, 0, 0
    white = 255, 255, 255
    red = 255, 0, 0
    green = 0, 255, 0
    blue = 0, 0, 255

    initial_velocity = 300

    screen_size = screen_width, screen_height = 300, 200

    screen = pg.display.set_mode(screen_size)

    clock = pg.time.Clock()

    pg.display.set_caption('Empathy in Pong')

    ball = Ball(euclid.Vector2(screen_width / 3, screen_height / 2), screen_width / 40, blue,
                get_random_velocity(math.pi * 2 / 5, math.pi * 3 / 5))

    empathizer = Paddle(euclid.Vector2(screen_width / 2, 0), screen_width / 40, screen_height / 5, 90,
                        red, None, None)
    agent = Paddle(euclid.Vector2(screen_width - screen_height / 10, screen_height / 2), screen_width / 40,
                   screen_height / 5, 0, black, None, empathizer)
    opponent = Paddle(euclid.Vector2(screen_height / 10, screen_height / 2), screen_width / 40, screen_height / 5, 0,
                      black, agent, None)

    agent.opponent = opponent

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
        ball.display()

        agent.display()
        opponent.display()
        empathizer.display()

        if ball.position.y > opponent.position.y + ball.size:
            opponent.move(0, 3, 0)
        elif ball.position.y < opponent.position.y - ball.size:
            opponent.move(0, -3, 0)
        else:
            opponent.move(0, 0, 0)

        # if ball.position.y > agent.position.y + ball.size:
        #     agent.move(0, 3, 0)
        # elif ball.position.y < agent.position.y - ball.size:
        #     agent.move(0, -3, 0)
        # else:
        #     agent.move(0, 0, 0)

        keys = pg.key.get_pressed()

        if keys[pg.K_UP]:
            agent.move(0, -3, 0)
        if keys[pg.K_DOWN]:
            agent.move(0, 3, 0)
        if keys[pg.K_LEFT]:
            empathizer.move(-3, 0, 0)
        if keys[pg.K_RIGHT]:
            empathizer.move(3, 0, 0)
        if keys[pg.K_a]:
            agent.move(0, 0, 1)
        if keys[pg.K_d]:
            agent.move(0, 0, -1)

        if 20 < agent.degrees <= 180:
                agent.degrees = 20
        elif 180 < agent.degrees < 340:
            agent.degrees = 340

        if 20 < opponent.degrees <= 180:
            agent.degrees = 20
        elif 180 < opponent.degrees < 340:
            agent.degrees = 340

        screen.unlock()
        pg.display.flip()

    pg.quit()
    sys.exit()
