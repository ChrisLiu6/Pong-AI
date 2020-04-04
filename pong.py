import pygame
import os
import neat
import random

pygame.font.init()
pygame.mixer.init()

# Game Speed
BALL_VEL = 20
BALL_VEL_X = int(BALL_VEL * 28 / 40)
BALL_VEL_Y = int(BALL_VEL)

STAT_FONT = pygame.font.SysFont('comicsans', 20)
BIG_FONT = pygame.font.SysFont('comicsans', 50, italic=True, bold=True)
NAME_FONT1 = pygame.font.SysFont('comicsans', 30, italic=False)
NAME_FONT2 = pygame.font.SysFont('comicsans', 14, italic=True)
NAME_FONT3 = pygame.font.SysFont('comicsans', 20, italic=True)

WIN_WIDTH = 615
WIN_HEIGHT = 700
BAR1_Y = 0
BAR2_Y = WIN_HEIGHT - 10
BAR_CENTER = int(WIN_WIDTH / 2) - 50

IMG_BAR = pygame.image.load(os.path.join('imgs', 'bar.png'))
IMG_BG = pygame.image.load(os.path.join('imgs', 'osu2.png'))
IMG_BALL = pygame.image.load(os.path.join('imgs', 'ball2.png'))

pygame.mixer.music.load(os.path.join('sound', 'bomb.mp3'))
pygame.mixer.music.play(-1)

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Pong.AI")

gen = 0
score_player = 0
score_AI = 0
num_alive = 0

DRAW_LINES = True


class Bar1:
    global BAR1_Y, BAR_CENTER, BALL_VEL
    img = IMG_BAR
    VEL = int(BALL_VEL * 1.1)

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dir_x = 0

    def draw(self, win):
        win.blit(self.img, (self.x, self.y))

    def move_left(self):
        self.x -= self.VEL

        if self.x <= 0:
            self.x = 0

    def move_right(self):
        self.x += self.VEL

        if self.x + self.img.get_width() >= WIN_WIDTH:
            self.x = WIN_WIDTH - self.img.get_width()

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Bar2:
    global BAR2_Y, BAR_CENTER, BALL_VEL
    img = IMG_BAR
    VEL = BALL_VEL

    def __init__(self):
        self.x = BAR_CENTER
        self.y = BAR2_Y
        self.dir_x = 0

    def draw(self, win):
        win.blit(self.img, (self.x, self.y))

    def move(self):
        self.x += self.VEL * self.dir_x

        if self.x <= 0:
            self.x = 0
        if self.x + self.img.get_width() >= WIN_WIDTH:
            self.x = WIN_WIDTH - self.img.get_width()

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
        self.dir_x = random.randint(0, 1) * 2 - 1
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

        bar2_offset = (round(self.x - bar2.x), round(self.y + self.img.get_height() / 2 - bar2.y))
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
    # Background
    win.blit(IMG_BG, (-110, -200))

    # Bar 1 and lines
    for bar in bar1s:
        bar.draw(win)
        if DRAW_LINES:
            pygame.draw.line(win, (100, 250, 100),
                                 (bar.x + bar.img.get_width() / 2, bar.y + bar.img.get_height() / 2),
                                 (ball.x + ball.img.get_width() / 2, ball.y + ball.img.get_height() / 2), 1)

    # Bar 2
    bar2.draw(win)

    # Ball
    ball.draw(win)

    # generations
    score_label = STAT_FONT.render("Gens: " + str(gen - 1), 1, (255, 255, 0))
    win.blit(score_label, (10, 30))

    # alive
    num_alive = STAT_FONT.render("Alive: " + str(len(bar1s)), 1, (255, 255, 0))
    win.blit(num_alive, (10, 50))

    # score
    score_label_player = STAT_FONT.render("Player Score: " + str(score_player), 1, (255, 255, 255))
    score_label_AI = STAT_FONT.render("AI Score: " + str(score_AI), 1, (255, 255, 255))
    win.blit(score_label_player, (10, 70))
    win.blit(score_label_AI, (10, 90))

    if not run:
        # press key to start
        text = BIG_FONT.render("Press Any Key to Start! ", 1, (0, 255, 0))
        win.blit(text, (80, 330))

        # Controls
        c1 = STAT_FONT.render('Control Keys:', 1, (255, 255, 0))
        c2 = STAT_FONT.render('A: Left', 1, (255, 255, 255))
        c3 = STAT_FONT.render('D: Right', 1, (255, 255, 255))
        c4 = STAT_FONT.render('L: Toggle Lines', 1, (255, 255, 255))
        win.blit(c1, (500, 30))
        win.blit(c2, (500, 50))
        win.blit(c3, (500, 70))
        win.blit(c4, (500, 90))

        # Players
        p1 = NAME_FONT3.render('You', 1, (0, 255, 255))
        p2 = NAME_FONT3.render('Evolving AI', 1, (0, 255, 255))
        win.blit(p1, (ball.x+30, 640))
        win.blit(p2, (310, 30))

    # Game name:
    logo = NAME_FONT1.render("Pong.AI", 1, (255, 255, 255))
    name = NAME_FONT2.render("A Boring Game Made Impossible", 1, (255, 255, 255))
    win.blit(logo, (490, 590))
    win.blit(name, (450, 615))

    pygame.display.update()


def main(genomes, config):
    global WIN, gen, score_player, score_AI, num_alive, DRAW_LINES
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
    run = False
    twitch = 0

    for _, g in genomes:
        g.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        bar1s.append(Bar1(BAR_CENTER, BAR1_Y))
        ge.append(g)

    draw_window(WIN, bar1s, bar2, ball, score_player, score_AI, run)

    # Start Manue
    while not run:
        draw_window(WIN, bar1s, bar2, ball, score_player, score_AI, run)
        bar2.move()
        ball.x = bar2.x + int(bar2.img.get_width() / 2) - int(ball.img.get_width() / 2)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    bar2.dir_x = -1
                elif event.key == pygame.K_d:
                    bar2.dir_x = 1
                elif event.key == pygame.K_l:
                    DRAW_LINES = False if DRAW_LINES else True
                else:
                    run = True
            else:
                bar2.dir_x = 0

            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

    # Main Loop
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
                    # Decrease fitness if die and being far away from ball
                    ge[bar1s.index(bar)].fitness -= (5 + 0.01 * abs(bar.x + bar.img.get_width() / 2 - ball_center))
                    nets.pop(bar1s.index(bar))
                    ge.pop(bar1s.index(bar))
                    bar1s.pop(bar1s.index(bar))

                for bar in bar1s:
                    # Increase fitness for hitting ball and being close
                    ge[bar1s.index(bar)].fitness += 30 - 0.01 * abs(bar.x + bar.img.get_width() / 2 - ball_center)

                bar1_remove.clear()

        if ball.collide_y_top():
            # Decrease fitness if die and being far away from ball
            ge[bar1s.index(bar)].fitness -= (5 + 0.01 * abs(bar.x + bar.img.get_width() / 2 - ball_center))
            bar1s.clear()
            nets.clear()
            ge.clear()
            score_player += 1

        if ball.collide_y_bottom():
            bar1s.clear()
            nets.clear()
            ge.clear()
            score_AI += 1

        for x, bar in enumerate(bar1s):
            # NN Inputs
            output = nets[bar1s.index(bar)].activate((ball_center, bar.x - ball_center, \
                                                      bar.x + bar.img.get_width() - ball_center, \
                                                      ball.y - (bar.y + bar.img.get_height()), ball.dir_y))

            if output[0] > 0.6:
                bar.move_left()
                if twitch == 1:
                    # Punish bar twitching for better visual
                    ge[bar1s.index(bar)].fitness -= 0.01
                twitch = 0
            if output[1] > 0.6:
                bar.move_right()
                if twitch == 0:
                    # Punish bar twitching for better visual
                    ge[bar1s.index(bar)].fitness -= 0.01
                twitch = 1

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    bar2.dir_x = -1
                elif event.key == pygame.K_d:
                    bar2.dir_x = 1
                elif event.key == pygame.K_l:
                    DRAW_LINES = False if DRAW_LINES else True
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
