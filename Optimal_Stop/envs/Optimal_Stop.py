import gym
from gym import spaces, logger
from gym.utils import seeding
import numpy as np
import pygame
#Let's import the Car Class
WHITE = (255, 255, 255)

class Car(pygame.sprite.Sprite):
    #This class represents a car. It derives from the "Sprite" class in Pygame.

    def __init__(self, color, width, height, max_speed):
        # Call the parent class (Sprite) constructor
        super().__init__()

        # Pass in the color of the car, and its x and y position, width and height.
        # Set the background color and set it to be transparent
        self.image = pygame.Surface([width, height])
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)

        #Initialise attributes of the car.
        self.width = width
        self.height = height
        self.color = color
        self.max_speed = max_speed
        self.speed = 18

        # Draw the car (a rectangle!)
        pygame.draw.rect(self.image, self.color, [0, 0, self.width, self.height])

        # Instead we could load a proper picture of a car...
        # self.image = pygame.image.load("car.png").convert_alpha()

        # Fetch the rectangle object that has the dimensions of the image.
        self.rect = self.image.get_rect()

    def accelerate(self, speed, players_speed):
        self.rect.y += (-speed+players_speed)

    def changeSpeed(self, speed):
        self.speed = speed

    def repaint(self, color):
        self.color = color
        pygame.draw.rect(self.image, self.color, [0, 0, self.width, self.height])





class Optimal_Stop(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array']}
    def __init__(self):
        self.max_position = 10**4
        self.min_position = -10**2
        self.max_distance = 10**12
        self.min_distance = 0
        self.max_speed = 20
        self.min_speed = 0
        self.max_acceleration = 6
        self.min_acceleration = -0.5
        self.goal_position = 1800
        self.low = np.array([self.min_position, self.min_distance, self.min_speed, self.min_speed])
        self.high = np.array([self.max_position, self.max_distance, self.max_speed, self.max_speed])
        self.action_space = spaces.Box(low=self.min_acceleration, high=self.max_acceleration, shape=(1,))
        self.observation_space = spaces.Box(low=self.low, high=self.high)
        self.stop_prob = 0.01
        self.reset()
        self.seed()
        self.stuck_time = 30

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def step(self, action):
        action = np.clip(action, self.min_acceleration, self.max_acceleration)
        position, distance, speed, leader_speed = self.state
        speed += action
        speed = np.clip(speed, self.min_speed, self.max_speed)
        position += speed
        position = np.clip(position, self.min_position, self.max_position)
        if (position==self.min_position and speed<0): speed = 0
        reward = -1.0
        self.rand_stop()
        self.driver_position += self.driver_speed
        distance = (self.driver_position) - position
        crash = bool(distance <= 0)
        done = bool(position >= self.goal_position)
        if crash:
            print('Car Crash!')
            reward = -1000.0
            done = True
        self.state = (position, distance, speed, self.driver_speed)
        return np.array(self.state), reward, done, {}

    def reset(self):
        "state = position, distance, speed"
        self.random_number = np.random.uniform()
        self.random_stop = bool(self.random_number < self.stop_prob)
        if self.random_stop:
            print('stop True)
            self.stop_position = 1779 # right before end stop position
            #self.stop_position = np.random.uniform(1000,4*10**3) # random stop position
            print('Stop.... In the name of love, before you break my head!')
        else:
            self.stop_position = 3*self.goal_position
        self.driver_speed = 18
        self.state = np.array([0, 100, 6, self.driver_speed]) # postion, distance, speed, Leaders speed
        self.driver_position = 100
        self.stop_ticker = 0
        #Reset Sprites and speed before next rollout
        self.all_coming_cars = []
        self.all_sprites_list = []
        pygame.quit()
        return np.array(self.state)

    def rand_stop(self):
        if self.driver_position > self.stop_position and self.stop_ticker < (self.stuck_time+1):
            self.driver_speed = 0
            self.stop_ticker += 1
        elif (self.stuck_time+1) <= self.stop_ticker < (self.stuck_time+4):
            self.driver_speed += 6
            self.stop_ticker += 1
        else:
            self.driver_speed += np.random.normal(0,0.05)

    # makes the car sprites
    def make_sprites(self):
        self.playerCar = Car(self.BLUE, 60, 80, 10)
        self.playerCar.rect.x = self.start_x_agent
        self.playerCar.rect.y = self.start_y_agent
        car1 = Car(self.RED, 60, 80, 20)
        car1.rect.x = self.start_x_driver
        car1.rect.y = self.start_y_driver
        self.all_sprites_list = pygame.sprite.Group()
        self.all_sprites_list.add(self.playerCar)
        self.all_sprites_list.add(car1)
        self.all_coming_cars = pygame.sprite.Group()
        self.all_coming_cars.add(car1)
    # simulate an episode of optimal stopping
    # stop_prob the probability of random stop
    def open_pygame(self):
        pygame.init()
        pygame.display.set_caption("Safe Stopping")
        self.GREEN = (20, 255, 140)
        self.BLUE = (0,0,255)
        self.DARK_GREEN = (0,100,0)
        self.GREY = (210, 210 ,210)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        SCREENWIDTH = 220
        SCREENHEIGHT = 600
        size = (SCREENWIDTH, SCREENHEIGHT)
        self.start_x_agent = 80
        self.start_y_agent = SCREENHEIGHT - 100
        self.start_x_driver = 80
        self.start_y_driver = SCREENHEIGHT - 280
        self.make_sprites()
        self.background = pygame.image.load('background2.jpeg')
        w , self.h = self.background.get_size()
        self.clock=pygame.time.Clock()
        self.screen = pygame.display.set_mode(size)
        self.y0 = 0
        self.y1 = 0


    def render(self, close=False):
        # Scroll the background to make it seem
        # as if the blue car is moving
        self.y1 = (self.y1 + self.state[2]) % self.h
        self.screen.blit(self.background,(0,-(self.h-self.y1)))
        self.screen.blit(self.background,(0,self.y1))
        # Move the red car
        for car in self.all_coming_cars:
            car.accelerate(self.driver_speed, self.state[2])

        # Check for collisions
        car_collision_list = pygame.sprite.spritecollide(self.playerCar,self.all_coming_cars,False)
        for car in car_collision_list:
            print("Car crash! from render")
            #End Of Game
        self.all_sprites_list.update()

        #Draw Line painting on the road
        #pygame.draw.line(self.screen, self.WHITE, [140,0],[140,self.SCREENHEIGHT],5)


        #Now let's draw all the sprites in one go. (For now we only have 1 sprite!)
        self.all_sprites_list.draw(self.screen)

        #Refresh Screen
        pygame.display.flip()
        #Number of frames per secong e.g. 60
        self.clock.tick(60)
        self.y0 = self.y1
