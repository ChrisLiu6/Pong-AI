import pygame
import time
import os
import neat
import random

pygame.font.init()
STAT_FONT = pygame.font.SysFont('comicsans', 30)

WIN_WIDTH = 600
WIN_HEIGHT = 700
BAR1_Y = 10
BAR2_Y = WIN_HEIGHT - 20
BAR_CENTER = int(WIN_WIDTH/2) - 50

BALL_VEL = 16
BALL_VEL_X = int(BALL_VEL*28/40)
BALL_VEL_Y = int(BALL_VEL)

IMG_BAR = pygame.image.load(os.path.join('imgs', 'bar.png'))
IMG_BG = pygame.image.load(os.path.join('imgs', 'osu.png'))
IMG_BALL = pygame.image.load(os.path.join('imgs', 'ball2.png'))

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Pong AI")

gen = 0
score_player = 0
score_AI = 0
num_alive = 0


class Bar1:
    global BAR1_Y, BAR_CENTER
    img = IMG_BAR
    VEL = 18

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dir_x = 0

    def draw(self, win):
        win.blit(self.img, (self.x, self.y))

    def move_left(self):
        self.x -= self.VEL

        if self.x <= 10:
            self.x = 10

    def move_right(self):
        self.x += self.VEL

        if self.x + self.img.get_width() >= WIN_WIDTH - 10:
            self.x = WIN_WIDTH - 10 - self.img.get_width()

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Bar2:
    global BAR2_Y, BAR_CENTER
    img = IMG_BAR
    VEL = 12

    def __init__(self):
        self.x = BAR_CENTER
        self.y = BAR2_Y
        self.dir_x = 0

    def draw(self, win):
        win.blit(self.img, (self.x, self.y))

    def move(self):
        self.x += self.VEL*self.dir_x

        if self.x <= 10:
            self.x = 10
        if self.x + self.img.get_width() >= WIN_WIDTH - 10:
            self.x = WIN_WIDTH - 10 - self.img.get_width()

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Ball:
    global score_player, score_AI
    img = IMG_BALL

    def __init__(self):
        self.x = 500
        self.y = BAR2_Y - 25
        self.vel_x = 0
        self.vel_y = 0
        self.dir_x = random.randint(0, 1)*2-1
        self.dir_y = -1

    def move(self):
        self.vel_x = BALL_VEL_X
        self.vel_y = BALL_VEL_Y
        self.x += self.vel_x * self.dir_x
        self.y += self.vel_y * self.dir_y

        if self.collide_x():
            self.dir_x *= -1
        if self.collide_y():
            self.dir_y *= -1

    def collide_x(self):
        if self.x <= 0 or self.x + self.img.get_width() >= WIN_WIDTH:
            return True
        return False

    def collide_y(self):
        if self.collide_y_top() or self.collide_y_bottom():
            return True
        return False

    def collide_y_top(self):
        if self.y <= 0:
            return True
        return False

    def collide_y_bottom(self):
        if self.y + self.img.get_height() > WIN_HEIGHT:
            return True
        return False

    def collide_bar2(self, bar2):
        bar2_mask = bar2.get_mask()
        ball_mask = pygame.mask.from_surface(self.img)

        bar2_offset = (self.x - bar2.x, self.y - round(bar2.y))
        bar2_overlap = bar2_mask.overlap(ball_mask, bar2_offset)

        if bar2_overlap:
            return True
        return False

    def collide_bar1(self, bar1s):
        ball_mask = pygame.mask.from_surface(self.img)

        for bar1 in bar1s:
            bar1_mask = bar1.get_mask()
            bar1_offset = (self.x - bar1.x, self.y - round(bar1.y))
            bar1_overlap = bar1_mask.overlap(ball_mask, bar1_offset)

            if bar1_overlap:
                return True
        return False

    def collide_check_bar1(self, bar1s):
        ball_mask = pygame.mask.from_surface(self.img)
        bar1_remove_list = []

        for bar1 in bar1s:
            bar1_mask = bar1.get_mask()
            bar1_offset = (self.x - bar1.x, self.y - round(bar1.y))
            bar1_overlap = bar1_mask.overlap(ball_mask, bar1_offset)

            if not bar1_overlap:
                bar1_remove_list.append(bar1)

        return bar1_remove_list

    def draw(self, win):
        win.blit(self.img, (self.x, self.y))


def draw_window(win, bar1s, bar2, ball, score_player, score_AI, run):
    win.blit(IMG_BG, (-120, -200))

    for bar1 in bar1s:
        bar1.draw(win)

    bar2.draw(win)
    ball.draw(win)

    # score
    score_label_player = STAT_FONT.render("Player Score: " + str(score_player), 1, (255, 255, 255))
    score_label_AI = STAT_FONT.render("AI Score: " + str(score_AI), 1, (255, 255, 255))
    win.blit(score_label_player, (10, 400))
    win.blit(score_label_AI, (10, 430))

    # generations
    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 300))

    # alive
    num_alive = STAT_FONT.render("Alive: " + str(len(bar1s)), 1, (255, 255, 255))
    win.blit(num_alive, (10, 330))

    # press G to start
    if not run:
        text = STAT_FONT.render("Press G to Start! ", 1, (255, 255, 255))
        win.blit(text, (215, 300))

    pygame.display.update()


def main(genomes, config):
    global WIN, gen, score_player, score_AI, num_alive
    gen += 1
    clock = pygame.time.Clock()

    # start by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    # bird object that uses that network to play
    nets = []
    bar1s = []
    ge = []
    bar2 = Bar2()
    ball = Ball()
    bar1_remove = []
    run = False

    for _, g in genomes:
        g.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        bar1s.append(Bar1(BAR_CENTER, BAR1_Y))
        ge.append(g)

    draw_window(WIN, bar1s, bar2, ball, score_player, score_AI, run)

    while not run:
        draw_window(WIN, bar1s, bar2, ball, score_player, score_AI, run)
        bar2.move()
        ball.x = bar2.x + int(bar2.img.get_width()/2) - int(ball.img.get_width()/2)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    run = True
                if event.key == pygame.K_a:
                    bar2.dir_x = -1
                elif event.key == pygame.K_d:
                    bar2.dir_x = 1
            else:
                bar2.dir_x = 0

            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

    while run and len(bar1s) > 0:
        clock.tick(100)
        ball_center = ball.x + ball.img.get_width() / 2

        ball.move()
        bar2.move()

        # if collide bar, change ball y direction
        if ball.collide_bar1(bar1s) or ball.collide_bar2(bar2):
            ball.dir_y *= -1
            if ball.collide_bar1(bar1s):
                bar1_remove = ball.collide_check_bar1(bar1s)

        for bar in bar1_remove:
            ge[bar1s.index(bar)].fitness -= 1
            ge[bar1s.index(bar)].fitness += 1-0.002 * abs(bar.x + bar.img.get_width() / 2 - ball_center)
            nets.pop(bar1s.index(bar))
            ge.pop(bar1s.index(bar))
            bar1s.pop(bar1s.index(bar))

        for bar in bar1s:
            ge[bar1s.index(bar)].fitness += 1

        bar1_remove.clear()

        if ball.collide_y_top():
            ge[bar1s.index(bar)].fitness -= 11
            bar1s.clear()
            nets.clear()
            ge.clear()
            score_player += 1

        if ball.collide_y_bottom():
            bar1s.clear()
            nets.clear()
            ge.clear()
            score_AI += 1

        for x, bar in enumerate(bar1s):  # give each bird a fitness of 0.1 for each frame it stays alive
            ge[x].fitness += 0.01
            bar_center = bar.x+bar.img.get_width()/2
            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[bar1s.index(bar)].activate((abs(bar_center - ball_center), abs(ball.y-BAR1_Y+bar.img.get_height())))

            if output[0] > 0.3:  # tanh activation function
                bar.move_left()
            if output[1] > 0.3:
                bar.move_right()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    bar2.dir_x = -1
                if event.key == pygame.K_d:
                    bar2.dir_x = 1
            else:
                bar2.dir_x = 0

            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        draw_window(WIN, bar1s, bar2, ball, score_player, score_AI, run)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)

    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'NEAT_config.txt')
    run(config_path)
