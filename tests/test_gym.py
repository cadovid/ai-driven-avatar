import pytest

from src.opengym.__main__ import GymGame


@pytest.mark.gym_env
def test_gym_environment(example_actions):
    env = GymGame()
    env.reset()
    while example_actions:
            # Get valid actions space
            env.get_valid_actions()

            # Take test action
            action = example_actions.popleft()
            if (action == 6 or action == 5) and (action not in env._valid_actions):
                action = 8
            assert action in env._valid_actions

            # Run action
            state, reward, done, info = env.step(action)
            
            # Render the game (slow the process in order not to see a crazy fast video)
            env.render()

            # Check end of the episode conditions
            if done == True:
                assert env.episodic_step == 147 or env.episodic_step == 148
                break
    
    env.close()
