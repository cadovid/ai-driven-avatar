import argparse
import numpy as np
import pygame

from enum import Enum, unique
from gym import Env, spaces

from py_main import Game
from rl_algorithms import RLAlgorithm
from settings import CONSUMABLES, ENVIRONMENT_TEMPERATURE


@unique
class Action(Enum):
    RIGTH = 0
    LEFT = 1
    DOWN = 2
    UP = 3
    EAT = 4
    DRINK = 5
    PICK_UP = 6
    SLEEP = 7


class GymGame(Env):

    def __init__(self):
        self.game = Game()
        #self.state = self.game.new()
        self._valid_actions = None
        self.action_space = spaces.Discrete(8)
        self.observation_space = spaces.Dict(
            {
                "avatar_position": spaces.Box(low=np.array([0, 0]), high=np.array([1984, 1472]), dtype=np.int32),
                "environment_temperature": spaces.Box(low=0, high=50, shape=(1,), dtype=np.int32),
                "energy_stored": spaces.Box(low=0, high=130000, shape=(1,), dtype=np.float32),
                "water_stored": spaces.Box(low=0, high=4, shape=(1,), dtype=np.float32),
                "sleepiness": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
            }
        )

    def reset(self):
        self.state = self.game.new()
        
        # Reset the cumulative reward (return)
        self.episodic_return = 0

        # Reset the episodic number of steps
        self.episodic_step = 0

        return self.game._get_obs()

    def step(self, action):
        # Flag that marks the termination of an episode
        done = False

        # Assert that it is a valid action 
        assert self.action_space.contains(action), "Invalid Action"
        
        # Compute for reward
        total_hours_pre = self.game.hours + (self.game.days * 24)

        # Executes action behaviour 
        for avatar in self.game.avatar_sprites:
            if action == 0:
                avatar.movement(1, 0)
            elif action == 1:
                avatar.movement(-1, 0)
            elif action == 2:
                avatar.movement(0, 1)
            elif action == 3:
                avatar.movement(0, -1)
            elif action == 4:
                avatar.eat()
            elif action == 5:
                avatar.drink()
            elif action == 6:
                avatar.pick_up(self.game.hitted_object.type)
                self.game.hitted_object.kill()
            elif action == 7:
                avatar.sleep()

        # Update information on the game >>>>>>>>>>>>>>>>>>>>>>
        for avatar in self.game.avatar_sprites:
            
            # Restore game conditions
            self.game.on_water_source = False
            self.game.hitted_object = None

            # Updates camera position in accordance with the entity
            self.game.camera.update(avatar)

            # Avatar hits an object
            hits = pygame.sprite.spritecollide(avatar, self.game.object_sprites, False)
            for hit in hits:
                self.game.hit_interaction(hit, avatar)
            
            # Update day/night cycle conditions
            if self.game.hours >= 22 or self.game.hours < 6:
                self.game.environment_temperature = ENVIRONMENT_TEMPERATURE - 10
            else:
                self.game.environment_temperature = ENVIRONMENT_TEMPERATURE
            avatar.drives.update_bmr(self.game.environment_temperature)
        
        # Update objects
        for object in self.game.object_sprites:
            object.update()

        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

        # Reward for executing the step
        total_hours_post = self.game.hours + (self.game.days * 24)
        reward = total_hours_post - total_hours_pre

        # Increment the episodic return
        self.episodic_return += reward

        # Increment the episodic step
        self.episodic_step += 1

        # Return state
        self.state = self.game._get_obs()

        # Conditions to end the episode
        for avatar in self.game.avatar_sprites:
            if avatar.drives.stored_energy <= 0 or avatar.drives.water <= 0 or avatar.drives.sleepiness > 0.9:
                done = True

        info = {}
        return self.state, reward, done, info

    def render(self):
        return self.game.draw_window()

    def get_action_meanings(self, number):
        return Action(number)

    def get_valid_actions(self):
        for avatar in self.game.avatar_sprites:
            self._valid_actions = [action.value for action in Action if self._is_valid_action(avatar, action)]

    def _is_valid_action(self, avatar, action):
        if action == Action.RIGTH and not avatar.analyze_collisions(1, 0):
            return True
        elif action == Action.LEFT and not avatar.analyze_collisions(-1, 0):
            return True
        elif action == Action.DOWN and not avatar.analyze_collisions(0, 1):
            return True
        elif action == Action.UP and not avatar.analyze_collisions(0, -1):
            return True
        elif action == Action.EAT and avatar.inventory and avatar.drives.stored_energy < avatar.drives.basal_energy:
            for o in avatar.inventory:
                if o in CONSUMABLES:
                    return True
        elif action == Action.DRINK and self.game.on_water_source and avatar.inventory and avatar.drives.water < avatar.drives.basal_water:
            if "cup" in avatar.inventory:
                return True
        elif action == Action.PICK_UP and self.game.hitted_object is not None:
            return True
        elif action == Action.SLEEP:
            return True
        else:
            return False


if __name__ == "__main__":

    # Instantiate the parser
    parser = argparse.ArgumentParser(prog='AI OpenGym Driven Avatar Environment',
                                     description='Runs RL Driven Avatar as an Opengym environment.')
    
    # Optional positional arguments
    parser.add_argument('-m', '--manual', action='store_true', help='Runs on manual operation')
    parser.add_argument('-r', '--random', action='store_true', help='Runs on random actions operation')
    parser.add_argument('-t', '--test', action='store_true', help='Runs test operations')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    
    # Parse arguments
    args = parser.parse_args()

    # Operations
    if args.manual:
        env = GymGame()
        while True:
            obs = env.reset()
            env.game.run()
            env.game.end_screen()
    elif args.random:
        env = GymGame()
        RLAlgorithm(env).random_policy()
    elif args.test:
        env = GymGame()
        RLAlgorithm(env).test_policy()
