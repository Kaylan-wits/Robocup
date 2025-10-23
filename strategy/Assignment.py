import numpy as np
import math 

def euclid_distance(pos1, pos2): 
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def role_assignment(teammate_positions, formation_positions): 

   
    num_players = len(teammate_positions)

    player_preferences = {}
    roles_preferences = {}

    
    for i in range(num_players):
        distances_to_roles = []

        for j in range(num_players):
            distance = euclid_distance(teammate_positions[i], formation_positions[j])
           
            distances_to_roles.append((distance, j))

        distances_to_roles.sort()

        preferred_roles_list = []
        for dist, role_index in distances_to_roles:
            preferred_roles_list.append(role_index)

        player_preferences[i] = preferred_roles_list

 

    for i in range(num_players):
        distances_to_players = []

        for j in range(num_players): 
            distance = euclid_distance(formation_positions[i], teammate_positions[j])

            distances_to_players.append((distance, j))

        distances_to_players.sort()


        preferred_players_list = []
        for dist, player_index in distances_to_players:
            preferred_players_list.append(player_index)

        roles_preferences[i] = preferred_players_list



    
    unmatched_players = list(range(num_players))
    
    current_assignments = {}
    player_next_proposal_index = {player_index: 0 for player_index in range(num_players)}


    while unmatched_players:
       
        player_index = unmatched_players.pop(0)

        preferred_roles = player_preferences[player_index]

        proposal_index = player_next_proposal_index[player_index]
        role_index = preferred_roles[proposal_index]


        if role_index not in current_assignments:
            current_assignments[role_index] = player_index

       
        else:
            current_player = current_assignments[role_index]
            preferred_players = roles_preferences[role_index]

            if preferred_players.index(player_index) < preferred_players.index(current_player):
                current_assignments[role_index] = player_index
                unmatched_players.append(current_player)

            else:
                unmatched_players.append(player_index)

        player_next_proposal_index[player_index] += 1


    
    point_preferences = {}
    
    final_player_to_role = {player: role for role, player in current_assignments.items()}

    for player_idx in range(num_players):
        player_unum = player_idx + 1
        
        assigned_role_idx = final_player_to_role[player_idx]
        
        assigned_position = formation_positions[assigned_role_idx]
        
        point_preferences[player_unum] = assigned_position

        #Hello friend

    return point_preferences