import pytest

from src.opengym.__main__ import GymGame
from src.rl_algorithms.__main__ import RLAlgorithm


@pytest.mark.gym_env
def test_gym_environment(example_actions):
    env = GymGame()
    RLAlgorithm(env)
    while example_actions:
            # Get valid actions space
            env.get_valid_actions()

            # Take test action
            action = example_actions.popleft()
            assert action in env._valid_actions

            # Run action
            state, reward, done, info = env.step(action)
            
            # Render the game (slow the process in order not to see a crazy fast video)
            env.render()
            
            # Check end of the episode conditions
            if done == True:
                assert env.episodic_step == 85
                break
    
    env.close()
