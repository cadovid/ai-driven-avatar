import datetime
import numpy as np
import os
import pathlib
import tensorflow as tf
import time

from gym import Env
from sb3_contrib.common.maskable.policies import MaskableMultiInputActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from stable_baselines3.common.callbacks import CheckpointCallback


def gpu_detected():
    return bool(tf.config.list_physical_devices(device_type='GPU'))


class Defaults():

    TOTAL_TIMESTEPS = 10000
    SAVE_FREQ = 10000
    EVAL_FREQ = 10000
    EVAL_EPISODES = 10
    SEED = 42
    VERBOSITY = 1
    SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'nn_models')
    NAME_PREFIX = "_PPO_ActorCriticPolicy"
    POLICY = MaskableMultiInputActorCriticPolicy
    DEVICE = "cuda" if gpu_detected() else "cpu"


class PPOAlgorithm():

    def __init__(self, environment):
        self.env = environment
        self.state = self.env.reset()

    def train(self):
        # Save timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        # Save a checkpoint every N steps
        pathlib.Path(Defaults.SAVE_PATH).mkdir(exist_ok=True) 
        checkpoint_callback = CheckpointCallback(save_freq=Defaults.SAVE_FREQ,
                                                 save_path=Defaults.SAVE_PATH,
                                                 name_prefix=timestamp+Defaults.NAME_PREFIX
                                                 )

        # Wrap environment to allow action masking
        # # Ref: https://github.com/Stable-Baselines-Team/stable-baselines3-contrib/pull/25
        def mask_fn(env: Env) -> np.ndarray:
            return env.valid_action_mask()

        self.env = ActionMasker(self.env, mask_fn)

        # Train the model
        model = MaskablePPO(policy=Defaults.POLICY,
                            env=self.env,
                            verbose=Defaults.VERBOSITY,
                            seed=Defaults.SEED,
                            device=Defaults.DEVICE
                            )
        model.learn(total_timesteps=Defaults.TOTAL_TIMESTEPS, callback=checkpoint_callback)

    def evaluation(self):
        # Load the most recent model
        models = [{'file': x, 'steps': int(x.split('_steps')[0].split('_')[-1])} for x in os.listdir(Defaults.SAVE_PATH)]
        latest_model = sorted(models, key=lambda x: -x['steps'])[0]['file']
        model = MaskablePPO.load(os.path.join(Defaults.SAVE_PATH, latest_model), device=Defaults.DEVICE)

        # Evaluate the model
        obs = self.env.reset()
        while True:
            print()
            print('>'*50)
            print(f'[PPO policy][Episodic Step] {self.env.episodic_step}')
            print(f"[PPO policy][State S_t-1] {self.env.state}")

            # Perform prediction
            action_masks = self.env.valid_action_mask()
            action, _states = model.predict(obs, action_masks=action_masks)
            print(f"[PPO policy][Action A_t] {self.env.get_action_meanings(action)}")

            # Run action
            obs, reward, done, info = self.env.step(action)
            print(f"[PPO policy][State S_t] {obs}")
            print(f"[PPO policy][Step reward R_t] {reward:.2f}")
            print(f"[PPO policy][Episodic return G_t so far] {self.env.episodic_return:.2f}")

            # Render the game
            self.env.render()
            time.sleep(0.1)

            # Check end conditions
            if done == True:
                print(f"[PPO policy][Total elapsed time] {self.env.game.days} days, {self.env.game.hours:.2f} hours")
                print(f"[PPO policy][Episodic return G_t] {self.env.episodic_return:.2f}")
                break

        self.env.close()
