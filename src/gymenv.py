import numpy as np

from enum import Enum
from gym import Env, spaces

from main import Game
from settings import CONSUMABLES


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
        self.state = self.game.new()
        self._valid_actions = None
        self.action_space = spaces.Discrete(8)
        self.observation_space = spaces.Dict(
            {
                "avatar_position": spaces.Box(low=np.array([0, 0]), high=np.array([1984, 1472]), dtype=np.int32),
                "environment_temperature": spaces.Box(low=0, high=50, shape=(1,), dtype=np.int32),
                "energy_stored": spaces.Box(low=0, high=3000, shape=(1,), dtype=np.float32),
                "water_stored": spaces.Box(low=0, high=3, shape=(1,), dtype=np.float32),
                "sleepiness": spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
            }
        )

    def reset(self):
        self.state = self.game.new()
        # Reset the reward
        self.ep_return  = 0

    def step(self, action):
        # Flag that marks the termination of an episode
        done = False

        # Assert that it is a valid action 
        assert self.action_space.contains(action), "Invalid Action"

        # Reward for executing a step
        reward = 1

        # Increment the episodic return
        self.ep_return += 1

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

        # Return state
        self.state = self.game._get_obs()

        # Game conditions reset
        self.game.on_water_source = False
        self.game.hitted_object = None

        # Condition to end the episode
        for avatar in self.game.avatar_sprites:
            if avatar.drives.stored_energy <= 0 or avatar.drives.water <= 0 or avatar.drives.sleepiness > 0.9:
                done = True

        info = {}
        return self.state, reward, done, info

    def render(self):
        return self.game.draw_window()

    def get_action_meanings(self):
        return {0: "Right",
                1: "Left",
                2: "Down",
                3: "Up",
                4: "Eat",
                5: "Drink",
                6: "Pick up",
                7: "Sleep"
                }

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



# ---------- Main algorithm -----------
# -------------------------------------

def launch_random_actions_run():
    env = GymGame()
    state = env.reset()

    while True:
        # Get valid actions space
        env.get_valid_actions()

        # Take a random action
        action = env.action_space.sample()
        while action not in env._valid_actions:
            action = env.action_space.sample()

        # Run action
        state, reward, done, info = env.step(action)
        print(f'State: {state}')
        print(f'Reward: {reward}')
        
        # Render the game
        env.render()
        
        if done == True:
            break

    env.close()


if __name__ == "__main__":
    launch_random_actions_run()
