import math
import pytweening

from src.pygame.settings import *


class BodyDrives:
    # Reference: https://www.jstor.org/stable/26444791?seq=3
    
    def __init__(self, environment_temperature,
                       avatar=None,
                       body_temperature=BODY_TEMPERATURE,
                       stored_energy=STORED_ENERGY,
                       stored_water=STORED_WATER,
                       body_area=BODY_AREA,
                       material_thickness=MATERIAL_THICKNESS,
                       basal_energy=BASAL_ENERGY,
                       basal_water=BASAL_WATER,
                       basal_metabolic_rate=BASAL_METABOLIC_RATE,
                       actions=ACTIONS):
        self.perceived_temperature = environment_temperature # [ºC]
        self.avatar = avatar
        self.body_temperature = body_temperature
        self.stored_energy = stored_energy # [kcal]
        self.basal_energy = basal_energy # [kcal]
        self.body_area = body_area # [m²]
        self.material_thickness = material_thickness # [m]
        self.actions = actions
        self.hunger = 0 # arousal
        self.thirst = 0 # arousal
        self.water = stored_water # [l]
        self.basal_water = basal_water # [l]
        self.basal_metabolic_rate = basal_metabolic_rate + (0.01 * (25 - environment_temperature) * basal_metabolic_rate) # [W]
        self.sleepiness = 0 # arousal
        self.biological_clock = 0 # [hours]
        self.internal_state = 'satisfied'
        self.resolved_state = True

    @staticmethod
    def watts_to_kcalh(units):
        """Conversion from Watt per second [W/s] to kcal per hour [kcal/h]
        (1 kcal -> 4186 Jules)
        """
        return units * 3600 / 4186

    @staticmethod
    def kilojoules_to_kcal(units):
        """Conversion from kilojoules [kJ] to kcal [kcal]
        """
        return units / 4.184

    @staticmethod
    def celsius_to_kelvin(units):
        """Conversion from ºC to K
        """
        return units + 273.15
    
    @staticmethod
    def standard_kcalh_production(watts_sleep=80, watts_awake=125, sleep_time=8, awake_time=16):
        total_kcal = (BodyDrives.watts_to_kcalh(watts_sleep) * sleep_time) + (BodyDrives.watts_to_kcalh(watts_awake) * awake_time)
        return total_kcal, total_kcal / 24

    @staticmethod
    def minimum_kcalh_production(watts=80, time=24):
        total_kcal = (BodyDrives.watts_to_kcalh(watts) * time)
        return total_kcal, total_kcal / 24

    def get_efficiency(self):
        """# Using the conservation of energy, ie, first law of thermodynamics: (dQ = dU + dW). Here Q1 = Q2 + W
            # Q1 energy input (food)
            # Q2 heat to be removed
            # W work done
        
        Efficiency of the machine: e = W /Q2 + W. Given that Q1 and Q2 are proportional to T1 and T2, (Q1/T1) and (Q2/T2).
        Then the efficiency of the human body, being T1 the higher temperature and T2 the lower one is 1 - T2/T1"""
        self.T1 = self.celsius_to_kelvin(self.body_temperature)
        self.T2 = self.celsius_to_kelvin(self.perceived_temperature)
        if self.T1 == self.T2 or self.perceived_temperature > self.body_temperature:
            self.T1 = self.T2 + 0.001
        self.efficiency = 1 - (self.T2 / self.T1)

    def get_heatgivenoff_and_usefulwork(self, total_heat):
        """From a given quantity produced of total heat, it returns the quantity of heat to give off and the
        quantity obtained as useful work in the system.
        """
        return (total_heat - (total_heat * self.efficiency)), total_heat * self.efficiency

    def get_heatgivenoff_rate(self):
        """It returns the heat given off rate in [kcal / s] through conductivity with the air.

        Conductivity of the air: 5.7e-6
        """
        self.T1 = max(self.celsius_to_kelvin(self.perceived_temperature), self.celsius_to_kelvin(self.body_temperature))
        self.T2 = min(self.celsius_to_kelvin(self.perceived_temperature), self.celsius_to_kelvin(self.body_temperature))
        if self.perceived_temperature > self.body_temperature:
            self.T1 = self.T2
        self.conductivity_rate = ( 5.7e-6 * self.body_area * (self.T1 - self.T2) ) / self.material_thickness

    def get_evaporation_water_mass(self, total_heat):
        """It returns the water mass needed to give off the quantity of heat indicated through evaporation of the body.
        Considering that 80 cal are required to evaporate 1 g of water.

        Inputs:
            total_heat [kcal]
        """
        return total_heat / 580

    def get_water_mass_consumed(self, action_heatgivenoff, time):
        """It returns the mass of water needed to be evaporated to evacuate the heat that conductivity can not eliminate.
        """
        if (action_heatgivenoff - (self.conductivity_rate * time * 3600)) >= 0:
            return self.get_evaporation_water_mass(action_heatgivenoff - (self.conductivity_rate * time * 3600))
        else:
            return 0

    def water_imbalance(self):
        if self.basal_water - self.water > 0:
            return self.basal_water - self.water
        else:
            return 0

    def get_maximum_kcal_per_meal(self, factor=1.5):
        standard_kcal, _ = self.standard_kcalh_production()
        return standard_kcal * factor / 3

    def energy_imbalance(self):
        if self.basal_energy - self.stored_energy > 0:
            if self.basal_energy - self.stored_energy > self.get_maximum_kcal_per_meal():
                return self.get_maximum_kcal_per_meal()
            else:
                return self.basal_energy - self.stored_energy
        else:
            return 0

    def update_sleepiness_arousal(self, hours, maximum_range=24):
        if hours >= 24:
            self.sleepiness = 1
        else:
            self.sleepiness = pytweening.easeInExpo((hours / maximum_range) - math.floor(hours / maximum_range))

    def update_hunger_arousal(self, value, maximum_range=None):
        if maximum_range is None:
            maximum_range = self.standard_kcalh_production()[0]
        if value > maximum_range:
            self.hunger = 0
        else:
            self.hunger = 1 - pytweening.easeInQuad((value / maximum_range) - math.floor(value / maximum_range))

    def update_thirst_arousal(self, value, maximum_range=None):
        if maximum_range is None:
            maximum_range = self.basal_water
        self.thirst = 1 - pytweening.easeInOutSine((value / maximum_range) - math.floor(value / maximum_range))

    def update_energy(self, quantity):
        if self.stored_energy + quantity > self.basal_energy:
            self.stored_energy = self.basal_energy
        else:
            self.stored_energy += quantity
        
    def update_water(self, quantity):
        if self.water + quantity > self.basal_water:
            self.water = self.basal_water
        else:
            self.water += quantity
    
    def update_bmr(self, environment_temperature):
        self.basal_metabolic_rate = BASAL_METABOLIC_RATE + (0.01 * (25 - environment_temperature) * BASAL_METABOLIC_RATE)

    def run_action(self, action, food_kcal=None):
        # Compute energy and water requirements
        self.get_efficiency()
        if action == "eat": # For eating it is necessary to include the energy required in digestion
            self.actions[action]["required_energy"] = self.watts_to_kcalh(self.basal_metabolic_rate) + (0.1 * food_kcal)
        if action == "sleep": # For sleeping it is necessary to calculate the amount of time needed
            self.actions[action]["required_time"] = (8 * round(self.sleepiness, 2))
        action_consumption = (self.watts_to_kcalh(self.basal_metabolic_rate) + self.watts_to_kcalh(self.actions[action]["required_energy"])) * self.actions[action]["required_time"]
        action_heatgivenoff, action_usefulwork = self.get_heatgivenoff_and_usefulwork(action_consumption)
        self.get_heatgivenoff_rate()
        action_water = self.get_water_mass_consumed(action_heatgivenoff, self.actions[action]["required_time"])
        if action == "sleep": # During sleep a fixed water amount is consumed
            action_water += self.actions[action]["required_time"] * 0.7 / 8
        self.update_water(-action_water)
        self.update_energy(-(action_heatgivenoff + action_usefulwork))
        
        # Update arousal values of the drives
        self.update_hunger_arousal(self.stored_energy)
        self.update_thirst_arousal(self.water)
        if action == "sleep":
            self.biological_clock = 0
            self.sleepiness = 0
        else:
            self.biological_clock += self.actions[action]["required_time"]
            self.update_sleepiness_arousal(self.biological_clock)
        
        # Update time of the game
        if self.avatar is not None:
            self.avatar.update_game_time(self.actions[action]["required_time"])
        
        # Update internal state of the avatar
        if self.internal_state == 'hungry':
            if self.hunger < 0.5 or self.sleepiness > 0.8 or self.thirst > 0.8:
                self.resolved_state = True
        elif self.internal_state == 'thirsty':
            if self.thirst < 0.2:
                self.resolved_state = True
        elif self.internal_state == 'sleepy':
            if self.sleepiness < 0.2:
                self.resolved_state = True
        if self.resolved_state:
            self.update_internal_state()
        
        # Print information about the game
        """ print(f'\n[Game Information][Action Executed] {action}'
              f'\n[Game Information][Energy consumption] Total: {action_consumption:.2f} kcal\tHeatOff: {action_heatgivenoff:.2f} kcal\tWater consumed: {action_water:.3f} l'
              f'\n[Game Information][Current arousal values] Hunger arousal: {self.hunger:.3f}\tSleepiness arousal: {self.sleepiness:.3f}\tThirst arousal: {self.thirst:.3f}'
              f'\n[Game Information][Internal state post action] {self.internal_state}'
              f'\n'
              ) """

    def update_internal_state(self):
        values = {}
        if self.hunger > 0.2:
            values.update({"hungry": self.hunger})
        if self.thirst > 0.2:
            values.update({"thirsty": self.thirst})
        if self.sleepiness > 0.2:
            values.update({"sleepy": self.sleepiness})
        if values:
            self.internal_state = max(values, key=values.get)
        else:
            self.internal_state = 'satisfied'
        if self.internal_state != 'satisfied':
            self.resolved_state = False

    def print_action_information(self):
        for action in self.actions:
            print(f'\n[{action}] required_energy: {self.watts_to_kcalh(self.basal_metabolic_rate) + self.watts_to_kcalh(self.actions[action]["required_energy"]):.2f} kcal/h, required_time: {self.actions[action]["required_time"]} h')
            action_consumption = (self.watts_to_kcalh(self.basal_metabolic_rate) + self.watts_to_kcalh(self.actions[action]["required_energy"])) * self.actions[action]["required_time"]
            print(f'[{action}] total consume {action_consumption:.2f} kcal in {self.actions[action]["required_time"]} h')
            action_heatgivenoff, action_usefulwork = self.get_heatgivenoff_and_usefulwork(action_consumption)
            action_water = self.get_water_mass_consumed(action_heatgivenoff, self.actions[action]["required_time"])
            print(f'[{action}] heat to give off: {action_heatgivenoff:.2f} kcal in {self.actions[action]["required_time"]} h')
            print(f'[{action}] useful work: {action_usefulwork:.2f} kcal in {self.actions[action]["required_time"]} h')
            print(f'[{action}] water mass needed to give off heat: {action_water:.2f} kg in {self.actions[action]["required_time"]} h')

    def print_general_information(self):
        print()
        print('******* Given rates *******')
        standard_total, standard_per_hour = self.standard_kcalh_production()
        print(f'Standard heat production rate: Total {standard_total:.2f} kcal, Per hour {standard_per_hour:.2f} kcal / h')
        minimum_total, minimum_per_hour = self.minimum_kcalh_production()
        print(f'Minimum heat production rate: Total {minimum_total:.2f} kcal, Per hour {minimum_per_hour:.2f} kcal / h')

        print()
        print('******* Environment *******')
        print(F'Temperature of the environment: {self.perceived_temperature} ºC')
        
        print()
        print('******* Body *******')
        print(F'Temperature of the body: {self.body_temperature} ºC')
        print(f'Initial energy through food: {standard_total:.2f} kcal')

        self.get_efficiency()
        print(f'Efficiency of the body: {self.efficiency:.3f}')
        
        heatgivenoff, useful_work = self.get_heatgivenoff_and_usefulwork(standard_total)
        print(f'Total energy disposal to work: {useful_work:.2f} kcal')
        print(f'Energy to be eliminated as heat: {heatgivenoff:.2f} kcal')

        print()
        print('******* Conductivity / Evaporation *******')
        self.get_heatgivenoff_rate()
        print(f'Heat given off rate through conductivity: {self.conductivity_rate*3600:.2f} kcal / h')
        if self.conductivity_rate != 0:
            print(f'Time to give off total heat in conductivity: {heatgivenoff / (self.conductivity_rate * 3600):.2f} hours')

        water_mass = self.get_evaporation_water_mass(heatgivenoff)
        print(f'Water mass to evaporate full heat quantity: {water_mass:.2f} kg')

        # Actions
        print()
        print('******* Actions *******')
        self.print_action_information()




if __name__ == "__main__":

    body = BodyDrives(ENVIRONMENT_TEMPERATURE)
    body.print_general_information()
