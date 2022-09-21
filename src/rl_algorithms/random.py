import time


class RandomAlgorithm():

    def __init__(self, environment):
        self.env = environment
        self.state = self.env.reset()
    
    def run(self):
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
