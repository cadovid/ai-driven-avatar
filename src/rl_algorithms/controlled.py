import time


from random import sample
from src.pygame.settings import CONSUMABLES, HARMFUL_ITEMS, PICKABLE_ITEMS, TILESIZE
from src.utils.actions import Action
from src.utils.pathfinding import a_star_algorithm


class ControlledAlgorithm():

    def __init__(self, environment):
        self.policy = 'Controlled policy'
        self.env = environment
        self.state = self.env.reset()
    
    def find_and_move_towards_closest_object(self, avatar, focus_on=None):
        if focus_on is None:
            # Ignore not pickable objects (create a shallow copy of the vision)
            new_sight_objects = dict()
            for s, d in self.env.game.sight_objects.items():
                if s.type in PICKABLE_ITEMS:
                    new_sight_objects[s] = d
        else:
            new_sight_objects = dict()
            for s, d in self.env.game.sight_objects.items():
                if s.type == focus_on:
                    new_sight_objects[s] = d

        # If objects at sight, go to the closest one
        if new_sight_objects:
            nearest_sprite = min(new_sight_objects, key=new_sight_objects.get)
            start = self.env.game.graph_map[int(avatar.pos.y / TILESIZE)][int(avatar.pos.x / TILESIZE)]
            end = self.env.game.graph_map[int(nearest_sprite.pos.y / TILESIZE)][int(nearest_sprite.pos.x / TILESIZE)]
            sequence_actions = a_star_algorithm(self.env.game.graph_map, start, end)
            if sequence_actions:
                action = sequence_actions.popleft()
            else:
                print("A* algorithm did not find an optimal path. Random movement executed")
                action = sample([action for action in self.env._valid_actions if action in [0, 1, 2, 3]], 1)[0]
        
        # If not objects at sight, then move in a continuous direction
        else:
            if self.last_action is not None and self.last_action not in self.env._valid_actions and self.last_action in [Action.LEFT.value, Action.RIGHT.value, Action.UP.value, Action.DOWN.value]:
                # Restrictions: Avoid going the opposite direction (where you came from) if possible
                restrictions = {str(Action.RIGHT.value): Action.LEFT.value,
                                str(Action.LEFT.value): Action.RIGHT.value,
                                str(Action.DOWN.value): Action.UP.value,
                                str(Action.UP.value): Action.DOWN.value
                                }
                valid_action_mov = []
                for action in self.env._valid_actions:
                    if action in [Action.LEFT.value, Action.RIGHT.value, Action.UP.value, Action.DOWN.value]:
                        valid_action_mov.append(action)
                if len(valid_action_mov) > 1:
                    action = restrictions[str(self.last_action)]
                    while action == restrictions[str(self.last_action)]:
                        action = sample([action for action in self.env._valid_actions if action in [Action.LEFT.value, Action.RIGHT.value, Action.UP.value, Action.DOWN.value]], 1)[0]
                else:
                    action = sample([action for action in self.env._valid_actions if action in [Action.LEFT.value, Action.RIGHT.value, Action.UP.value, Action.DOWN.value]], 1)[0]
            elif self.last_action is not None and self.last_action in self.env._valid_actions and self.last_action in [Action.LEFT.value, Action.RIGHT.value, Action.UP.value, Action.DOWN.value]:
                action = self.last_action
            else:
                action = sample([action for action in self.env._valid_actions if action in [Action.LEFT.value, Action.RIGHT.value, Action.UP.value, Action.DOWN.value]], 1)[0]
        return action

    def run(self):
        # Set initial conditions
        self.last_action = None
        
        while True:
            print()
            print('>'*50)
            print(f'[Episodic Step] {self.env.episodic_step}')
            print(f"[State S_t-1] {self.env.state}")

            # Get valid actions space
            self.env.get_valid_actions()
            print(f"[Action space A_t] {[self.env.get_action_meanings(action) for action in self.env._valid_actions]}")

            # Rules to perform actions
            for avatar in self.env.game.avatar_sprites:
                if avatar.drives.internal_state == 'satisfied':
                    if bool(self.env.game.hitted_object) and (self.env.game.hitted_object.type in PICKABLE_ITEMS): # If on object, try something
                        if len(avatar.inventory) <= 4:
                            action = Action.PICK_UP.value
                        elif len(avatar.inventory) > 4:
                            action = Action.STAND_STILL.value
                    else: # If not on object, go find them
                        action = self.find_and_move_towards_closest_object(avatar)
                elif avatar.drives.internal_state == 'hungry':
                    if avatar.inventory:
                        for object in avatar.inventory:
                            if object in CONSUMABLES:
                                action = Action.EAT.value
                            else:
                                if bool(self.env.game.hitted_object) and (self.env.game.hitted_object.type in PICKABLE_ITEMS):
                                    action = Action.PICK_UP.value
                                else:
                                    action = self.find_and_move_towards_closest_object(avatar)
                    else:
                        if bool(self.env.game.hitted_object) and (self.env.game.hitted_object.type in PICKABLE_ITEMS):
                            action = Action.PICK_UP.value
                        else:
                            action = self.find_and_move_towards_closest_object(avatar)
                elif avatar.drives.internal_state == 'thirsty':
                    if avatar.inventory and 'cup' in avatar.inventory:
                        if bool(self.env.game.hitted_object) and (self.env.game.on_water_source):
                            action = Action.DRINK.value
                        else:
                            action = self.find_and_move_towards_closest_object(avatar, focus_on='water-dispenser')
                    else:
                        if bool(self.env.game.hitted_object) and (self.env.game.hitted_object.type == 'cup'):
                            if len(avatar.inventory) <= 4:
                                action = Action.PICK_UP.value
                            else:
                                action = Action.EAT.value
                        else:
                            action = self.find_and_move_towards_closest_object(avatar, focus_on='cup')
                elif avatar.drives.internal_state == 'sleepy':
                    action = Action.SLEEP.value

            # Check action
            assert action in self.env._valid_actions, f"Action not in valid space of actions < {self.env.get_action_meanings(action)} >"
            print(f"[Action A_t] {self.env.get_action_meanings(action)}")

            # Run action
            state, reward, done, info = self.env.step(action)
            print(f"[State S_t] {state}")
            print(f"[Step reward R_t] {reward:.2f}")
            print(f"[Episodic return G_t so far] {self.env.episodic_return:.2f}")
            
            # Assign last action
            self.last_action = action
            
            # Render the game (slow the process in order not to see a crazy fast video)
            self.env.render()
            time.sleep(0.1)
            
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
