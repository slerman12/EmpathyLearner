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

    def display(self):
        rx, ry = int(self.position.x), int(self.position.y)
        pg.draw.circle(screen, self.color, (rx, ry), self.size)

    def move(self):
        self.position += self.velocity * dtime
        self.bounce()

    def bounce(self):
        # Horizontal bounds
        if self.position.x > screen_width + self.size or self.position.x + self.size < 0:
            # if self.position.x > screen_width:
            #     agent_score += 1
            #
            # elif self.position.x < 0:
            #     opponent_score += 1

            self.position.x = screen_width / 2
            self.position.y = screen_height / 2
            self.velocity = get_random_velocity(math.pi / 3, math.pi * 2 / 3)

        if self.position.y <= self.size:
            self.position.y = 2 * self.size - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

        elif self.position.y >= screen_height - self.size:
            self.position.y = 2 * (screen_height - self.size) - self.position.y
            self.velocity = self.velocity.reflect(euclid.Vector2(0, 1))

    # Collision between ball and paddle
    def collision(self, other):
        max_length = max(other.width, other.height)

        if not (other.position.x + max_length / 2 > self.position.x > other.position.x - max_length / 2 and other.position.y +
                max_length / 2 > self.position.y > other.position.y - max_length / 2):
            return False

        paddle_unoriented = box(other.position.x - other.width / 2, other.position.y - other.height / 2, other.position.x + other.width / 2,
                   other.position.y + other.height / 2)
        paddle_oriented = rotate(paddle_unoriented, angle=360 - other.degrees, origin=(other.position.x, other.position.y))
        paddle_coords = paddle_oriented.exterior.coords

        p = Point(self.position.x, self.position.y)
        c = p.buffer(self.size).boundary

        if Point(paddle_coords[0], paddle_coords[1]).intersects(c) or \
                Point(paddle_coords[1], paddle_coords[2]).intersects(c) or \
                Point(paddle_coords[2], paddle_coords[3]).intersects(c) or \
                Point(paddle_coords[3], paddle_coords[0]).intersects(c):
            self.position -= self.velocity * dtime
            self.velocity = -self.velocity
        else:
            if LineString([paddle_coords[0], paddle_coords[1]]).intersects(c):
                normal_vector = euclid.Vector2(-paddle_coords[1][1] + paddle_coords[0][1],
                                               paddle_coords[1][0] - paddle_coords[0][0]).normalize()
                self.position -= self.velocity * dtime
                self.velocity = self.velocity.reflect(normal_vector)
            if LineString([paddle_coords[1], paddle_coords[2]]).intersects(c):
                normal_vector = euclid.Vector2(-paddle_coords[2][1] + paddle_coords[1][1],
                                               paddle_coords[2][0] - paddle_coords[1][0]).normalize()
                self.position -= self.velocity * dtime
                self.velocity = self.velocity.reflect(normal_vector)
            if LineString([paddle_coords[2], paddle_coords[3]]).intersects(c):
                normal_vector = euclid.Vector2(-paddle_coords[3][1] + paddle_coords[2][1],
                                               paddle_coords[3][0] - paddle_coords[2][0]).normalize()
                self.position -= self.velocity * dtime
                self.velocity = self.velocity.reflect(normal_vector)
            if LineString([paddle_coords[3], paddle_coords[0]]).intersects(c):
                normal_vector = euclid.Vector2(-paddle_coords[0][1] + paddle_coords[3][1],
                                               paddle_coords[0][0] - paddle_coords[3][0]).normalize()
                self.position -= self.velocity * dtime
                self.velocity = self.velocity.reflect(normal_vector)


class Paddle:
    def __init__(self, position, width, height, degrees, color, velocity):
        self.position = position
        self.width = width
        self.height = height
        self.degrees = degrees
        self.color = color
        self.velocity = velocity

        self.surf = None
        self.blit = None

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
        max_length = max(self.width, self.height)

        if (self.position.x + max_length / 2 > ball.position.x > self.position.x - max_length / 2 and self.position.y +
                max_length / 2 > ball.position.y > self.position.y - max_length / 2) or (self.position.x + max_length / 2 > ball.position.x > self.position.x - max_length / 2 and self.position.y +
                max_length / 2 > ball.position.y > self.position.y - max_length / 2):
            paddle_unoriented = box(self.position.x - self.width / 2, self.position.y - self.height / 2, self.position.x +
                                    self.width / 2, self.position.y + self.height / 2)
            paddle_oriented = rotate(paddle_unoriented, angle=360 - self.degrees, origin=(self.position.x, self.position.y))

            p = Point(ball.position.x, ball.position.y)
            c = p.buffer(ball.size).boundary

            if paddle_oriented.intersects(c):
                self.degrees = (self.degrees - counterclockwise) % 360
                self.position.x = self.position.x - right
                self.position.y = self.position.y - down
            
        # Horizontal and vertical bounds
        if self.position.x - max_length / 2 < 0:
            self.position.x = max_length / 2
        if self.position.x + max_length / 2 > screen_width:
            self.position.x = screen_width - max_length / 2
        if self.position.y - max_length / 2 < 0:
            self.position.y = max_length / 2
        if self.position.y + max_length / 2 > screen_height:
            self.position.y = screen_height - max_length / 2


def get_random_velocity(range_min, range_max):
    new_angle = random.uniform(range_min, range_max)
    new_x = math.sin(new_angle)
    new_y = math.cos(new_angle)
    new_vector = euclid.Vector2(new_x, new_y)
    new_vector.normalize()
    new_vector *= initial_velocity  # pixels per second
    return new_vector


if __name__ == "__main__":
    # Defining some basic colors
    black = 0, 0, 0
    white = 255, 255, 255
    red = 255, 0, 0
    green = 0, 255, 0
    blue = 0, 0, 255

    colors = [black, red, green, blue]

    initial_velocity = 200

    # Defining the screen size
    screen_size = screen_width, screen_height = 300, 200

    # Setting the display and getting the Surface object
    screen = pg.display.set_mode(screen_size)
    # Getting the Clock object
    clock = pg.time.Clock()
    # Setting a title to the window

    pg.display.set_caption('Empathy in Pong')

    # ball = Ball(euclid.Vector2(screen_width / 2, screen_height / 2), 10, random.choice(colors),
    #             get_random_velocity(math.pi / 3, math.pi * 2 / 3))

    ball = Ball(euclid.Vector2(screen_width / 2, screen_height / 2), screen_width / 40, blue,
                get_random_velocity(math.pi / 3, math.pi * 2 / 3))

    agent = Paddle(euclid.Vector2(screen_width / 20, screen_height / 2), screen_width / 40, screen_height / 5, 0, black,
                   euclid.Vector2(5, 5))
    opponent = Paddle(euclid.Vector2(screen_width - screen_width / 20, screen_height / 2), screen_width / 40,
                      screen_height / 5, 0, black, euclid.Vector2(5, 5))
    empathizer = Paddle(euclid.Vector2(screen_width / 2, screen_height / 30), screen_width / 40, screen_height / 5, 90,
                        red, euclid.Vector2(10, 10))

    # Defining variables for fps and continued running
    fps_limit = 60
    run_me = True
    while run_me:

        # Get any user input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                run_me = False

        # Limit the framerate
        dtime_ms = clock.tick(fps_limit)
        dtime = dtime_ms / 1000.0

        # Clear the screen
        screen.fill(white)

        ball.move()
        ball.display()
        agent.display()

        if ball.position.y > agent.position.y:
            agent.move(0, 0.8, 0)
        elif ball.position.y < agent.position.y:
            agent.move(0, -0.8, 0)
        else:
            agent.move(0, 0, 0)

        opponent.display()

        if ball.position.y > opponent.position.y + 10:
            opponent.move(0, 0.8, 0)
        elif ball.position.y < opponent.position.y + 10:
            opponent.move(0, -0.8, 0)
        else:
            opponent.move(0, 0, 0)

        empathizer.display()

        keys = pg.key.get_pressed()

        if keys[pg.K_UP]:
            empathizer.move(0, -1, 0)
        if keys[pg.K_DOWN]:
            empathizer.move(0, 1, 0)
        if keys[pg.K_LEFT]:
            empathizer.move(-1, 0, 0)
        if keys[pg.K_RIGHT]:
            empathizer.move(1, 0, 0)
        if keys[pg.K_a]:
            empathizer.move(0, 0, 1)
        if keys[pg.K_d]:
            empathizer.move(0, 0, -1)

        ball.collision(agent)
        ball.collision(opponent)
        ball.collision(empathizer)

        screen.unlock()
        # Display everything in the screen.
        pg.display.flip()

    # Quit the game
    pg.quit()
    sys.exit()
