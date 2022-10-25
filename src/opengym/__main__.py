import argparse
import math
import numpy as np
import pygame
import pytweening
import sys

from gym import Env, spaces
from random import random, choice

from src.pygame.__main__ import Game
from src.pygame.settings import COMMON_ITEMS, CONSUMABLES, ENVIRONMENT_TEMPERATURE, PICKABLE_ITEMS, UNIQUE_ITEMS
from src.rl_algorithms.ppo import PPOAlgorithm, Defaults
from src.rl_algorithms.random import RandomAlgorithm
from src.rl_algorithms.controlled import ControlledAlgorithm
from src.utils.actions import Action


class GymGame(Env):

    def __init__(self):
        self.game = Game()
        #self.state = self.game.new()
        self._valid_actions = None
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Dict(
            {
                "environment_temperature": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
                "energy_stored": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
                "water_stored": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
                "sleepiness": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
                "objects_at_sight": spaces.Box(low=0, high=1, shape=(1,), dtype=np.int32),
                "objects_on_inventory": spaces.Box(low=0, high=1, shape=(1,), dtype=np.int32),
                "on_water_source": spaces.Box(low=0, high=1, shape=(1,), dtype=np.int32),
                "on_object": spaces.Box(low=0, high=1, shape=(1,), dtype=np.int32)
            }
        )
        #TODO wall positions?

    def reset(self):
        self.state = self.game.new()
        
        # Reset the cumulative reward (return)
        self.episodic_return = 0

        # Reset the episodic number of steps
        self.episodic_step = 1

        return self.game._get_obs()

    def step(self, action):
        # Flag that marks the termination of an episode
        done = False

        # Assert that it is a valid action 
        assert self.action_space.contains(action), "Invalid Action"
        
        # Compute for reward
        total_hours_pre = self.game.hours + (self.game.days * 24)

        # Compute for random spawn
        hours_pre = self.game.hours

        # Executes action behaviour 
        for avatar in self.game.avatar_sprites:
            if action == Action.RIGHT.value:
                avatar.movement(1, 0)
            elif action == Action.LEFT.value:
                avatar.movement(-1, 0)
            elif action == Action.DOWN.value:
                avatar.movement(0, 1)
            elif action == Action.UP.value:
                avatar.movement(0, -1)
            elif action == Action.EAT.value:
                avatar.eat()
            elif action == Action.DRINK.value:
                avatar.drink()
            elif action == Action.PICK_UP.value:
                avatar.pick_up(self.game.hitted_object.type)
                self.game.hitted_object.kill()
            elif action == Action.SLEEP.value:
                avatar.sleep()
            elif action == Action.STAND_STILL.value:
                avatar.stand_still()

        # Update information on the game >>>>>>>>>>>>>>>>>>>>>>
        for avatar in self.game.avatar_sprites:
            # Spawn random objects at empty locations stochastically
            self.game.n_trials = round(abs(hours_pre - self.game.hours), 1)
            if self.game.n_trials >= 12:
                self.game.n_trials = 24 - self.game.n_trials
            if self.game.n_trials != 0:
                rest = self.game.n_trials - math.floor(self.game.n_trials)
            else:
                rest = 0
            self.game.countdown += rest
            self.game.countdown = round(self.game.countdown, 1)
            for _ in range(math.floor(self.game.n_trials)):
                capacity_items = (len(self.game.object_sprites) - (len(UNIQUE_ITEMS) - 1)) / (self.game.max_items - (len(UNIQUE_ITEMS) - 1))
                if random() < pytweening.easeInQuad(1 - capacity_items):
                    x_r, y_r = choice(self.game.spawn_coordinates)
                    o_coordinates = []
                    for o in self.game.object_sprites:
                        if o.type in CONSUMABLES:
                            o_coordinates.append([o.rect.x, o.rect.y])
                    if (len(self.game.spawn_coordinates) == len(o_coordinates)):
                        break
                    while [int(x_r), int(y_r)] in o_coordinates:
                        x_r, y_r = choice(self.game.spawn_coordinates)
                    self.game.spawn_new_object(x_r, y_r, choice(COMMON_ITEMS))
            if self.game.countdown >= 1:
                for _ in range(math.floor(self.game.countdown)):
                    capacity_items = (len(self.game.object_sprites) - (len(UNIQUE_ITEMS) - 1)) / (self.game.max_items - (len(UNIQUE_ITEMS) - 1))
                    if random() < pytweening.easeInQuad(1 - capacity_items):
                        x_r, y_r = choice(self.game.spawn_coordinates)
                        o_coordinates = []
                        for o in self.game.object_sprites:
                            if o.type in CONSUMABLES:
                                o_coordinates.append([o.rect.x, o.rect.y])
                        if (len(self.game.spawn_coordinates) == len(o_coordinates)):
                            break
                        while [int(x_r), int(y_r)] in o_coordinates:
                            x_r, y_r = choice(self.game.spawn_coordinates)
                        self.game.spawn_new_object(x_r, y_r, choice(COMMON_ITEMS))
                self.game.countdown = 1 - math.floor(self.game.countdown)
            self.game.n_trials = 0

            # Restore game conditions
            self.game.on_water_source = False
            self.game.hitted_object = None

            # Updates camera position in accordance with the entity
            self.game.camera.update(avatar)

            # Avatar hits an object
            hits = pygame.sprite.spritecollide(avatar, self.game.object_sprites, False)
            for hit in hits:
                self.game.hit_interaction(hit)

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

        for avatar in self.game.avatar_sprites:
            # 1) Reward for executing the step
            total_hours_post = self.game.hours + (self.game.days * 24)
            time_elapsed = total_hours_post - total_hours_pre
            # 2) Reward in terms of arousal values (negative impact)
            drives_values = 0
            if avatar.drives.hunger > 0.5:
                drives_values += time_elapsed * 1/3
            if avatar.drives.thirst > 0.5:
                drives_values += time_elapsed * 1/3
            if avatar.drives.sleepiness > 0.8:
                drives_values += time_elapsed * 1/3
            # 3) Sum up (+1 per step)
            reward = time_elapsed - drives_values

        # Increment the episodic return
        self.episodic_return += reward

        # Increment the episodic step
        self.episodic_step += 1

        # Update observation objects at sight
        self.game.raycasting()
        
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
        if action == Action.RIGHT and not avatar.analyze_collisions(1, 0):
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
            return False
        elif action == Action.DRINK and self.game.on_water_source and avatar.inventory and avatar.drives.water < avatar.drives.basal_water:
            if "cup" in avatar.inventory:
                return True
        elif (action == Action.PICK_UP) and (self.game.hitted_object is not None) and (len(avatar.inventory) <= 4) and (self.game.hitted_object.type in PICKABLE_ITEMS):
            return True
        elif (action == Action.SLEEP) and (avatar.drives.sleepiness >= 0.2):
            return True
        elif action == Action.STAND_STILL:
            return True
        else:
            return False

    def valid_action_mask(self):
        "It returns the invalid action mask. True if the action is valid, False otherwise"
        for avatar in self.game.avatar_sprites:
            return [self._is_valid_action(avatar, action) for action in Action]

    def manual_run(self):
        self.state = self.reset()
        self.pressed_keys = []
        self.relevant_keys = {pygame.K_RIGHT: Action.RIGHT.value,
                              pygame.K_LEFT: Action.LEFT.value,
                              pygame.K_DOWN: Action.DOWN.value,
                              pygame.K_UP: Action.UP.value,
                              pygame.K_e: Action.EAT.value,
                              pygame.K_d: Action.DRINK.value,
                              pygame.K_p: Action.PICK_UP.value,
                              pygame.K_s: Action.SLEEP.value,
                              pygame.K_q: Action.STAND_STILL.value
                              }
        while True:
            print()
            print('>'*50)
            print(f'[Episodic Step] {self.episodic_step}')
            print(f"[State S_t-1] {self.state}")
            
            # Render the game
            self.render()

            # Get valid actions space
            self.get_valid_actions()
            print(f"[Action space A_t] {[self.get_action_meanings(action) for action in self._valid_actions]}")

            # Perform action
            action = self._process_event()
            while action not in self._valid_actions:
                action = self._process_event()
            print(f"[Action A_t] {self.get_action_meanings(action)}")
            state, reward, done, info = self.step(action)
            print(f"[State S_t] {state}")
            print(f"[Step reward R_t] {reward:.2f}")
            print(f"[Episodic return G_t so far] {self.episodic_return:.2f}")

            # Render the game
            self.render()

            # Check end conditions
            if done == True:
                print('<'*50)
                print(f'\nSUMMARY\n')
                data = [("Policy", "Total elapsed time", "Episodic return G_t"), ('Manual policy', f'{self.game.days} days, {self.game.hours:.2f} hours', f'{self.episodic_return:.2f}')]
                for x, y, sum in data:
                    print(f"{x:{25}} {y:{25}} {sum:{25}}")
                break
        
        self.close()
    
    def _process_event(self):
        pygame.event.clear()
        while True:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key in self.relevant_keys:
                    return self.relevant_keys[event.key]
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


if __name__ == "__main__":

    # Instantiate the parser
    parser = argparse.ArgumentParser(prog='AI OpenGym Driven Avatar Environment',
                                     description='Runs RL Driven Avatar as an Opengym environment.')
    
    # Optional positional arguments
    parser.add_argument('-m', '--manual', action='store_true', help='Runs on manual operation')
    parser.add_argument('-r', '--random', action='store_true', help='Runs on random actions operation')
    parser.add_argument('-c', '--controlled', action='store_true', help='Runs on basic rules actions operation')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('-a', '--algorithm', nargs='?', default='ppo', help='Runs an operation with a RL algorithm')
    parser.add_argument('-t', '--train', nargs='?', const=10000, type=int, help='Performs training on a RL algorithm')
    parser.add_argument('--vecenv', action='store_true', help='Performs training on a RL algorithm with vectorized environments')
    parser.add_argument('-e', '--evaluation', action='store_true', help='Performs evaluation on a RL algorithm')

    # Parse arguments
    args = parser.parse_args()

    # Operations
    if args.manual:
        GymGame().manual_run()
    elif args.random:
        env = GymGame()
        RandomAlgorithm(env).run()
    elif args.controlled:
        env = GymGame()
        ControlledAlgorithm(env).run()
    elif args.algorithm and args.train:
        Defaults.TOTAL_TIMESTEPS = int(args.train)
        if 'ppo' in args.algorithm:
            if args.vecenv:
                PPOAlgorithm(GymGame, use_vecenv=True).train()
            else:
                env = GymGame()
                PPOAlgorithm(env).train()
    elif args.algorithm and args.evaluation:
        if 'ppo' in args.algorithm:
            env = GymGame()
            PPOAlgorithm(env).evaluation()
