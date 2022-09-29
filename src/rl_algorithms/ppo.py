import datetime
import numpy as np
import os
import pathlib
import tensorflow as tf
import time
import wandb

from gym import Env
from stable_baselines3.common.env_util import make_vec_env
from sb3_contrib.common.maskable.policies import MaskableMultiInputActorCriticPolicy
from stable_baselines3.common.monitor import Monitor
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from stable_baselines3.common.callbacks import CheckpointCallback
from wandb.integration.sb3 import WandbCallback


def n_cpus():
    return os.cpu_count()


def gpu_detected():
    return bool(tf.config.list_physical_devices(device_type='GPU'))


class CustomPolicy(MaskableMultiInputActorCriticPolicy):
    def __init__(self, *args, **kwargs):
        super(CustomPolicy, self).__init__(*args, **kwargs,
                                           net_arch=[dict(pi=[128, 128, 128], vf=[128, 128, 128])]
                                           )


class Defaults():

    TOTAL_TIMESTEPS = 100000
    SAVE_FREQ = 10000
    SAVE_GRAD_FREQ = 100
    EVAL_FREQ = 10000
    EVAL_EPISODES = 10
    SEED = 42
    VERBOSITY = 2
    LOGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs/ppo')
    SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'nn_models')
    NAME_PREFIX = "_PPO_ActorCriticPolicy"
    POLICY = CustomPolicy
    DEVICE = "cuda" if gpu_detected() else "cpu"
    NUM_THREADS = n_cpus()


class PPOAlgorithm():

    def __init__(self, environment, use_vecenv=False, use_wandb=True):
        self.env = environment
        self.use_vecenv = use_vecenv
        self.use_wandb = use_wandb
        if not self.use_vecenv:
            self.state = self.env.reset()

    def train(self):
        # Save tags
        if self.use_vecenv:
            tag = "_Vectorized"
        else:
            tag = "_Vanilla"

        # Save timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        # Monitor and log assignment        
        #self.env = Monitor(self.env)
        pathlib.Path(Defaults.LOGS_PATH).mkdir(exist_ok=True)
        pathlib.Path(Defaults.SAVE_PATH).mkdir(exist_ok=True)

        if self.use_wandb:
            # W&B log metrics interface
            wandb_run = wandb.init(project="ai-driven-avatar",
                                   entity="academic-david",
                                   name=timestamp + Defaults.NAME_PREFIX + tag,
                                   sync_tensorboard=True,  # auto-upload sb3's tensorboard metrics
                                   monitor_gym=True,  # auto-upload the videos of agents playing the game
                                   save_code=False,  # optional
                                   anonymous="allow",
                                   )

            # W&B log callback
            callback = WandbCallback(verbose=Defaults.VERBOSITY,
                                     model_save_path=Defaults.SAVE_PATH + "/" + f"{wandb_run.name}",
                                     model_save_freq=Defaults.SAVE_FREQ,
                                     gradient_save_freq=Defaults.SAVE_GRAD_FREQ
                                     )
        else:
            # Checkpoint callback every N steps
            #TODO Replace with EvalCallback
            callback = CheckpointCallback(save_freq=Defaults.SAVE_FREQ,
                                          save_path=Defaults.SAVE_PATH,
                                          name_prefix=timestamp + Defaults.NAME_PREFIX + tag
                                         )

        # Callbacks
        callbacks = [callback]

        # Wrap environment to allow action masking
        # # Ref: https://github.com/Stable-Baselines-Team/stable-baselines3-contrib/pull/25
        def mask_fn(env: Env) -> np.ndarray:
            return env.valid_action_mask()

        def get_wrapper(env: Env) -> Env:
            return ActionMasker(env, mask_fn)

        # Vectorize environment
        if self.use_vecenv:
            self.env = make_vec_env(self.env,
                                    n_envs=Defaults.NUM_THREADS,
                                    seed=Defaults.SEED,
                                    wrapper_class=get_wrapper
                                    )
        else:
            self.env = ActionMasker(self.env, mask_fn)

        # Build the model
        model = MaskablePPO(policy=Defaults.POLICY,
                            env=self.env,
                            tensorboard_log=Defaults.LOGS_PATH,
                            verbose=Defaults.VERBOSITY,
                            seed=Defaults.SEED,
                            device=Defaults.DEVICE
                            )

        # Train the model
        model.learn(total_timesteps=Defaults.TOTAL_TIMESTEPS,
                    callback=callbacks,
                    tb_log_name=timestamp + Defaults.NAME_PREFIX + tag
                    )
        
        if self.use_wandb:
            # End logging session
            wandb.finish()

    def evaluation(self):
        # Load the most recent model
        if self.use_wandb:
            models = [{'file': x, 'timestamp': str(x.split(Defaults.NAME_PREFIX)[0].split(Defaults.NAME_PREFIX)[0])} for x in os.listdir(Defaults.SAVE_PATH)]
            latest_model = sorted(models, reverse=True, key=lambda x: datetime.datetime.strptime(x["timestamp"], "%Y-%m-%d_%H:%M:%S"))[0]['file']
            model = MaskablePPO.load(os.path.join(Defaults.SAVE_PATH, latest_model + "/model.zip"), device=Defaults.DEVICE)
        else:
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
