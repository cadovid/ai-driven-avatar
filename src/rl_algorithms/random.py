import time


class RandomAlgorithm():

    def __init__(self, environment):
        self.policy = 'Random policy'
        self.env = environment
        self.state = self.env.reset()
    
    def run(self):
        while True:
            print()
            print('>'*50)
            print(f'[Episodic Step] {self.env.episodic_step}')
            print(f"[State S_t-1] {self.env.state}")

            # Get valid actions space
            self.env.get_valid_actions()
            print(f"[Action space A_t] {[self.env.get_action_meanings(action) for action in self.env._valid_actions]}")

            # Take a random action
            action = self.env.action_space.sample()
            while action not in self.env._valid_actions:
                action = self.env.action_space.sample()
            print(f"[Action A_t] {self.env.get_action_meanings(action)}")

            # Run action
            state, reward, done, info = self.env.step(action)
            print(f"[State S_t] {state}")
            print(f"[Step reward R_t] {reward:.2f}")
            print(f"[Episodic return G_t so far] {self.env.episodic_return:.2f}")
            
            # Render the game (slow the process in order not to see a crazy fast video)
            self.env.render()
            time.sleep(0.2)
            
            # Check end of the episode conditions
            if done == True:
                print('<'*50)
                print(f'\nSUMMARY\n')
                data = [("Policy", "Total elapsed time", "Episodic return G_t"), (self.policy, f'{self.env.game.days} days, {self.env.game.hours:.2f} hours', f'{self.env.episodic_return:.2f}')]
                for x, y, sum in data:
                    print(f"{x:{25}} {y:{25}} {sum:{25}}")
                break

            print('<'*50)
        
        self.env.close()
