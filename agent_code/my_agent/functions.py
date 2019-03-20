
import numpy as np
from random import shuffle
from time import time, sleep
from collections import deque
import pickle
import copy
from agent_code.my_agent.features import *

from settings import s
from settings import e

############# USEFUL FUNCTIONS ##############

def estimate_blast_coords(arena,bombs):
    """
    is only an idea on how the bomb blast ranges may be computed
    """
    for bomb in bombs_xy:
        # compute patches in posible directions
        # up
        if bomb[1]-bomb_power <1:
            #patch = arena[1:bomb[1]+1,bomb[0]]
            patch = arena[bomb[0], 1:bomb[1]+1]
        else:
            #patch = arena[bomb[1]-bomb_power:bomb[1]+1, bomb[0]]
            patch = arena[bomb[0], bomb[1]-bomb_power:bomb[1]+1]

def compute_blast_coords(arena, bomb):
    """
    !! This function may be good for computations, as it takes to much time :/
    to compute
    Retrieve the blast of all bombs acording a given stage.
    The maximal power of the bomb (maximum range in each direction) is
    imported directly from the game settings. The blast range is
    adjusted according to walls, other agents and crates (immutable obstacles).
    Parameters:
    * game_state
    Return Value:
    * Array containing blast range coordinates of all bombs (list of tuples).

    May be useful for feature 2
    """
    bomb_power = s.bomb_power
    x, y = bomb[0], bomb[1] 
    blast_coords = []

    for i in range(1, bomb_power+1):
        if arena[x+i, y] == -1: break
        blast_coords.append((x+i,y))
    for i in range(1, bomb_power+1):
        if arena[x-i, y] == -1: break 
        blast_coords.append((x-i, y))
    for i in range(1, bomb_power+1):
        if arena[x, y+i] == -1: break 
        blast_coords.append((x, y+i))
    # moving to the right direction (like the song XD )
    for i in range(1, bomb_power+1):
        if arena[x, y-i] == -1: break 
        blast_coords.append((x, y-i))

    return blast_coords

def compute_patch(arena, p1, p2):
    """
    this function computes the patch of the arena between the points p1 and p2
    USEFUL FOR feat1
    """
    patch = arena[min(p1[1], p2[1]):max(p1[1], p2[1])+1,  min(p1[0], p2[0]):max(p1[0], p2[0])+1] 
    return patch

def manhattan_metric(p1, p2):
    """
    p1 or p2 may be an array of points in numpy format
    USEFUL FOR feat1
    """
    absdiff = np.abs(p1 - p2)
    sum_absdiff = np.sum(absdiff, axis=1)
    return sum_absdiff

def feat_1(game_state):
    """
        Feature extraction for coin detection
        Old implementation useful for ideas and maybe use at some point distance computations
    """
    coins = game_state['coins']
    x, y, _, bombs_left = game_state['self']
    directions = [(x,y-1), (x,y+1), (x-1,y), (x+1,y)]
    arena = game_state['arena']

    feature = [] # Desired feature

    # check if there are coins available if not return 0 as feature
    if coins == []: 
        return np.expand_dims(np.zeros(6), axis=0)

    for d in directions:
        # if invalid action set to zero
        if arena[d] != 0:
            feature.append(0)
            continue

        # compute manhattan distance between all visible coins and the agent
        manh_dist = manhattan_metric(np.asarray(coins), np.array(d))

        # find the nearest coins
        min_coin, dist2min_coin = np.argmin(manh_dist), np.min(manh_dist)
        indx_mincoins = list(np.where(manh_dist == dist2min_coin)[0])
        
        ## correct manhattan distance for special cases
        # compute patches between min_coins and agent 
        patches = [] 
        for m in indx_mincoins:
            p = compute_patch(arena, coins[m], d)
            patches.append(p)
        
        # look if there is a fast path to the closes coin
        FAST_PATH = False 
        for patch in patches:
            if patch.shape[0] == 1 or patch.shape[1] == 1:
                if np.count_nonzero(patch) == 0:
                    FAST_PATH=True
                    break
            else:
                FAST_PATH=True
                break
        if not FAST_PATH:
            dist2min_coin += 2

        # fill features
        
        #feature.append(f)
        feature.append(1000-dist2min_coin) #1000 random value
        
    feature.append(0)
    feature.append(0)
    
    # convert the maximum values of feature to 1 and the rest to 0
    help_list = []
    for f in feature:
        if f == max(feature):
            help_list.append(1)
        else:
            help_list.append(0)

    feature = help_list 
    # because this feature doesn't take in consideration using bombs
    #f_bomb = np.expand_dims(np.zeros(feature.shape[1]), axis=0)
    #feature = np.concatenate((feature,f_bomb), axis=0)

    #feature = np.expand_dims(feature, axis=0)
    return feature


def look_for_targets(free_space, start, targets, logger=None):
    """Find direction of closest target that can be reached via free tiles.

    Performs a breadth-first search of the reachable free tiles until a target is encountered.
    If no target can be reached, the path that takes the agent closest to any target is chosen.

    Args:
        free_space: Boolean numpy array. True for free tiles and False for obstacles.
        start: the coordinate from which to begin the search.
        targets: list or array holding the coordinates of all target tiles.
        logger: optional logger object for debugging.
    Returns:
        coordinate of first step towards closest target or towards tile closest to any target.

    USEFUL FOR feature1
    """
    if len(targets) == 0: return None

    frontier = [start]
    parent_dict = {start: start}
    dist_so_far = {start: 0}
    best = start
    best_dist = np.sum(np.abs(np.subtract(targets, start)), axis=1).min()

    while len(frontier) > 0:
        current = frontier.pop(0)
        # Find distance from current position to all targets, track closest
        d = np.sum(np.abs(np.subtract(targets, current)), axis=1).min()
        if d + dist_so_far[current] <= best_dist:
            best = current
            best_dist = d + dist_so_far[current]
        if d == 0:
            # Found path to a target's exact position, mission accomplished!
            best = current
            break
        # Add unexplored free neighboring tiles to the queue in a random order
        x, y = current
        neighbors = [(x,y) for (x,y) in [(x+1,y), (x-1,y), (x,y+1), (x,y-1)] if free_space[x,y]]
        shuffle(neighbors)
        for neighbor in neighbors:
            if neighbor not in parent_dict:
                frontier.append(neighbor)
                parent_dict[neighbor] = current
                dist_so_far[neighbor] = dist_so_far[current] + 1
    if logger: logger.debug(f'Suitable target found at {best}')
    # Determine the first step towards the best found target tile
    current = best
    while True:
        if parent_dict[current] == start: return current
        current = parent_dict[current]


def get_blast_coords(bomb, arena, arr):
    x, y = bomb[0], bomb[1]
    bomb_power = s.bomb_power
    if len(arr)== 0:
       arr = np.array([[x,y]])
       #np.append(a, [[0,1]], axis=0)
    
    for i in range(1, bomb_power+1):
        if arena[x+i,y] == -1: break
        arr = np.append(arr,[[x+i,y]], axis=0)
    for i in range(1, bomb_power+1):
        if arena[x-i,y] == -1: break
        arr = np.append(arr,[[x-i,y]], axis=0)            
    for i in range(1, bomb_power+1):
        if arena[x,y+i] == -1: break
        arr = np.append(arr,[[x,y+i]], axis=0)            
    for i in range(1, bomb_power+1):
        if arena[x,y-i] == -1: break
        arr = np.append(arr,[[x,y-i]], axis=0)
    return arr