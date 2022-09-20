import datetime
import numpy as np
import os
import pathlib
import time

from collections import deque
from gym import Env
from sb3_contrib.common.maskable.policies import MaskableMultiInputActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env


class RLAlgorithm():

    def __init__(self, environment):
        self.env = environment
        self.env.reset()
    
    def random_policy(self):
        while True:
            print()
            print('>'*50)
            print(f'[Random policy][Episodic Step] {self.env.episodic_step}')
            print(f"[Random policy][State S_t-1] {self.env.state}")

            # Get valid actions space
            self.env.get_valid_actions()
            print(f"[Random policy][Action space A_t] {[self.env.get_action_meanings(action) for action in self.env._valid_actions]}")

            # Take a random action
            action = self.env.action_space.sample()
            while action not in self.env._valid_actions:
                action = self.env.action_space.sample()
            print(f"[Random policy][Action A_t] {self.env.get_action_meanings(action)}")

            # Run action
            state, reward, done, info = self.env.step(action)
            print(f"[Random policy][State S_t] {state}")
            print(f"[Random policy][Step reward R_t] {reward:.2f}")
            print(f"[Random policy][Episodic return G_t so far] {self.env.episodic_return:.2f}")
            
            # Render the game (slow the process in order not to see a crazy fast video)
            self.env.render()
            time.sleep(0.2)
            
            # Check end of the episode conditions
            if done == True:
                print()
                print(f"[Random policy][Total elapsed time] {self.env.game.days} days, {self.env.game.hours:.2f} hours")
                print(f"[Random policy][Episodic return G_t] {self.env.episodic_return:.2f}")
                print('<'*50)
                break

            print('<'*50)
        
        self.env.close()

    def PPO_policy_train(self):
        # Save timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        # Save a checkpoint every 1000 steps
        root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        save_path = os.path.join(root_path, 'nn_models')
        pathlib.Path(save_path).mkdir(exist_ok=True) 
        checkpoint_callback = CheckpointCallback(save_freq=5000, save_path=save_path, name_prefix=timestamp+"_PPO_MlpPolicy")

        # Wrap environment to allow action masking
        # # Ref: https://github.com/Stable-Baselines-Team/stable-baselines3-contrib/pull/25
        def mask_fn(env: Env) -> np.ndarray:
            return env.valid_action_mask()

        self.env = ActionMasker(self.env, mask_fn)

        # Train model
        model = MaskablePPO(MaskableMultiInputActorCriticPolicy, self.env, verbose=1, seed=42)
        model.learn(total_timesteps=20000, callback=checkpoint_callback)

    def PPO_policy_eval(self):
        # Load last model
        root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        load_path = os.path.join(root_path, 'nn_models')
        models = [{'file': x, 'steps': int(x.split('_steps')[0].split('_')[-1])} for x in os.listdir(load_path)]
        latest_model = sorted(models, key=lambda x: -x['steps'])[0]['file']
        latest_model_path = os.path.join(load_path, latest_model)
        model = MaskablePPO.load(latest_model_path)

        # Eval model
        obs = self.env.reset()
        while True:
            print()
            print(f'[PPO policy][Episodic Step] {self.env.episodic_step}')
            print(f"[PPO policy][State S_t-1] {self.env.state}")
            action_masks = self.env.valid_action_mask()
            action, _states = model.predict(obs, action_masks=action_masks)
            print(f"[PPO policy][Action A_t] {self.env.get_action_meanings(action)}")
            obs, reward, done, info = self.env.step(action)
            print(f"[PPO policy][State S_t] {obs}")
            print(f"[PPO policy][Step reward R_t] {reward:.2f}")
            print(f"[PPO policy][Episodic return G_t so far] {self.env.episodic_return:.2f}")
            self.env.render()
            time.sleep(0.2)
            if done == True:
                print(f"[PPO policy][Total elapsed time] {self.env.game.days} days, {self.env.game.hours:.2f} hours")
                print(f"[PPO policy][Episodic return G_t] {self.env.episodic_return:.2f}")
                break
        self.env.close()
