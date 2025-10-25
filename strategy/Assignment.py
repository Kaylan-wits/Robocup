import numpy as np
# Removed: from scipy.optimize import linear_sum_assignment

# --- Role Assignment (Greedy Algorithm - No SciPy Needed) ---
def role_assignment(player_positions, point_positions):
    """
    Assigns each player to a target point using a greedy algorithm
    based on minimizing distance iteratively. Does NOT require SciPy.

    Args:
        player_positions (list): List of current (x, y) numpy arrays for each player.
                                  Can contain None for missing players.
        point_positions (dict): Dictionary where keys are role IDs (e.g., player numbers)
                                and values are target (x, y) numpy arrays.

    Returns:
        dict: Dictionary mapping player number (1-based index + 1) to their assigned target point position.
    """
    
    # Create lists of available players (index, position) and targets (id, position)
    available_players = [(i + 1, pos) for i, pos in enumerate(player_positions) if pos is not None]
    available_targets = list(point_positions.items()) # List of (target_id, target_pos)

    assignments = {}
    
    # Keep track of which targets have been assigned
    assigned_target_indices = set()

    # --- Greedy Assignment Loop ---
    # Continue as long as there are players and targets to assign
    while available_players and available_targets:
        best_player_num = -1
        best_target_id = -1
        best_target_pos = None
        min_dist_sq = float('inf')
        
        player_to_remove_idx = -1
        target_to_remove_idx = -1

        # Iterate through all *currently available* players
        for player_idx, (player_num, player_pos) in enumerate(available_players):
            # Iterate through all *currently available* targets
            for target_idx, (target_id, target_pos) in enumerate(available_targets):
                
                dist_sq = np.sum((player_pos - target_pos)**2)
                
                # If this player/target pair is the closest found so far
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    best_player_num = player_num
                    best_target_id = target_id
                    best_target_pos = target_pos
                    player_to_remove_idx = player_idx
                    target_to_remove_idx = target_idx

        # If a best pair was found in this iteration
        if best_player_num != -1:
            # Assign the best player found to the best target found
            assignments[best_player_num] = best_target_pos
            
            # Remove the assigned player and target from the available lists
            # Remove by index safely (or create new lists excluding them)
            available_players.pop(player_to_remove_idx)
            available_targets.pop(target_to_remove_idx)
        else:
            # Should not happen if lists are not empty, but break just in case
            break 
            
    # --- Handle Leftover Players (if more players than targets) ---
    # Assign remaining players to their current position (stay put)
    for player_num, player_pos in available_players:
         if player_num not in assignments:
              assignments[player_num] = player_pos

    # --- Handle Players initially None or otherwise unassigned ---
    all_player_nums = set(range(1, len(player_positions) + 1))
    assigned_player_nums = set(assignments.keys())
    unassigned_player_nums = all_player_nums - assigned_player_nums

    for player_num in unassigned_player_nums:
        player_idx = player_num - 1
        if player_positions[player_idx] is not None:
             assignments[player_num] = player_positions[player_idx]
        # else: Add fallback like initial position if needed

    return assignments


# --- Intelligent Pass Selector (from muzzaam/test34 - No SciPy Needed) ---
# (This function remains exactly the same as before)
def pass_reciever_selector(my_unum, teammate_positions, opponent_positions, goal_target, priority_target=None):
    """
    Selects the best teammate to pass to, prioritizing open players further forward.

    Args:
        my_unum (int): The player number of the agent making the pass.
        teammate_positions (list): List of numpy arrays for teammate positions.
        opponent_positions (list): List of numpy arrays for opponent positions.
        goal_target (tuple/np.array): Coordinates of the opponent's goal.
        priority_target (np.array, optional): A specific teammate position to prioritize if they are open.

    Returns:
        tuple: (best_target, second_best_target), where targets are numpy arrays or None.
    """
    best_target = None
    second_best_target = None
    best_score = -float('inf')
    second_best_score = -float('inf')

    # Ensure my_pos is accessed safely and is a numpy array if valid
    my_pos = None
    if my_unum > 0 and my_unum <= len(teammate_positions) and teammate_positions[my_unum - 1] is not None:
         my_pos = np.array(teammate_positions[my_unum - 1])
    
    if my_pos is None:
        return None, None # Cannot pass if my position is unknown

    # Ensure opponent positions are numpy arrays if not None
    valid_opponents = [np.array(opp_pos) for opp_pos in opponent_positions if opp_pos is not None]
    
    # Ensure priority target is a numpy array if provided
    priority_target_np = np.array(priority_target) if priority_target is not None else None

    # Check priority target first (e.g., Cherry Picker)
    if priority_target_np is not None:
         is_priority_safe = True
         min_dist_to_opp = float('inf')
         for opp_pos in valid_opponents:
              dist_to_opp = np.linalg.norm(priority_target_np - opp_pos)
              min_dist_to_opp = min(min_dist_to_opp, dist_to_opp)
              # Check if opponent is blocking the pass lane
              pass_vector = priority_target_np - my_pos
              pass_dist = np.linalg.norm(pass_vector)
              # Avoid division by zero or issues if pass distance is tiny
              if pass_dist > 1e-6: 
                   pass_midpoint = my_pos + pass_vector * 0.5
                   dist_opp_to_midpoint = np.linalg.norm(opp_pos - pass_midpoint)
                   if dist_opp_to_midpoint < pass_dist * 0.4: # Adjust 0.4 threshold as needed
                        is_priority_safe = False
                        break # Blocked
              else: # If target is too close, consider it unsafe if opponent is also close
                   if dist_to_opp < 1.0: 
                       is_priority_safe = False
                       break

         # If priority target is reasonably open (e.g., > 2m from nearest opp) and pass lane clear
         if min_dist_to_opp > 2.0 and is_priority_safe:
              # Basic score: prioritize being forward and distance from opponents
              score = priority_target_np[0] + min_dist_to_opp * 0.5 
              best_target = priority_target_np # Store as numpy array
              best_score = score
              
    # Iterate through other teammates
    for i, teammate_pos_orig in enumerate(teammate_positions):
        player_num = i + 1
        teammate_pos = np.array(teammate_pos_orig) if teammate_pos_orig is not None else None # Work with numpy array

        # Skip self, None positions, and the priority target if already assigned as best_target
        if teammate_pos is None or player_num == my_unum or \
           (best_target is not None and np.array_equal(teammate_pos, best_target)):
            continue

        min_dist_to_opp = float('inf')
        is_safe = True
        for opp_pos in valid_opponents:
            dist_to_opp = np.linalg.norm(teammate_pos - opp_pos)
            min_dist_to_opp = min(min_dist_to_opp, dist_to_opp)
            
            # Check pass lane blocking
            pass_vector = teammate_pos - my_pos
            pass_dist = np.linalg.norm(pass_vector)
            if pass_dist < 1e-6: continue # Avoid division by zero
            pass_midpoint = my_pos + pass_vector * 0.5
            dist_opp_to_midpoint = np.linalg.norm(opp_pos - pass_midpoint)
            if dist_opp_to_midpoint < pass_dist * 0.4:
                 is_safe = False
                 break 

        # Consider passing only if teammate is reasonably open and pass is safe
        if min_dist_to_opp > 1.5 and is_safe: # Minimum distance threshold for safety
            # Scoring: Prioritize forward position, openness, and moderate distance
            forward_bonus = teammate_pos[0] * 1.5 
            openness_bonus = min_dist_to_opp * 0.7 
            
            pass_distance = np.linalg.norm(teammate_pos - my_pos)
            distance_penalty = abs(pass_distance - 7.0) * 0.1 # Ideal pass around 7m?

            score = forward_bonus + openness_bonus - distance_penalty

            if score > best_score:
                second_best_score = best_score
                second_best_target = best_target # Already numpy array or None
                best_score = score
                best_target = teammate_pos # Store as numpy array
            elif score > second_best_score:
                second_best_score = score
                second_best_target = teammate_pos # Store as numpy array

    # Return results (already numpy arrays or None)
    return best_target, second_best_target

