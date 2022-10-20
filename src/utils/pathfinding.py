from collections import deque
from queue import PriorityQueue
from typing import Tuple, Dict, Deque, List, Union
from src.pygame.tilemap import Spot
from src.utils.actions import Action


def heuristic(p1: Tuple[int], p2: Tuple[int]) -> int:
    "Manhattan distance"
    y1, x1 = p1 # row, col
    y2, x2 = p2 # row, col
    return abs(x1 - x2) + abs(y1 - y2)

def get_movement_action(p1: Tuple[int], p2: Tuple[int]) -> int:
    y1, x1 = p1 # row, col
    y2, x2 = p2 # row, col
    if y1 == y2:
        if x1 > x2:
            return Action.LEFT.value
        elif x1 < x2:
            return Action.RIGHT.value
    elif x1 == x2:
        if y1 > y2:
            return Action.UP.value
        elif y1 < y2:
            return Action.DOWN.value

def reconstruct_path(came_from: Dict[Spot, Spot], current: Spot, start: Spot) -> Deque:
    sequence_pos = deque()
    sequence_actions = deque()
    while current in came_from:
        sequence_pos.appendleft(current.get_pos())
        current = came_from[current]
    pos_init = sequence_pos.popleft()
    sequence_actions.appendleft(get_movement_action(start.get_pos(), pos_init))
    while sequence_pos:
        next_pos = sequence_pos.popleft()
        sequence_actions.append(get_movement_action(pos_init, next_pos))
        pos_init = next_pos
    print(f"[A* Optimal path actions] {sequence_actions}")
    return sequence_actions

def a_star_algorithm(graph_map: List[List[Spot]], start: Spot, end: Spot) -> Union[Deque, None]:
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))
    came_from = dict()
    cost_so_far = {spot: float("inf") for row in graph_map for spot in row}
    cost_so_far[start] = 0
    priority = {spot: float("inf") for row in graph_map for spot in row}
    priority[start] = heuristic(start.get_pos(), end.get_pos())
    open_set_hash = {start}

    while not open_set.empty():
        current = open_set.get()[2]
        open_set_hash.remove(current)
        if current == end:
            return reconstruct_path(came_from, current, start)
        for neighbor in current.neighbors:
            new_cost_so_far = cost_so_far[current] + 1 # Here we assume all the edges are value 1, no cost moving
            if new_cost_so_far < cost_so_far[neighbor]:
                came_from[neighbor] = current
                cost_so_far[neighbor] = new_cost_so_far
                priority[neighbor] = new_cost_so_far + heuristic(neighbor.get_pos(), end.get_pos())
                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((priority[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
    return None
