import numpy as np

BASE_FORMATION_PLAYON = [
    np.array([-14, 0]),
    np.array([-7, -4]),
    np.array([-7, 4]),
    np.array([-2, 0]),
    np.array([3, -5]),
    np.array([3, 5]),
    np.array([6, 0]),
    np.array([9, -3]),
    np.array([9, 3]),
    np.array([12, -1]),
    np.array([12, 1])
]

def GeneratePlayOn(ball_x=0.0): 

    shifted_formation = []

    clamped_ball_x = np.clip(ball_x, -14.0, 14.0)
    norm_ball_x = (clamped_ball_x + 14.0) / 28.0 

    max_forward_shift = 7.0 

    for i, base_pos in enumerate(BASE_FORMATION_PLAYON):
        
        if i == 0:
            shift = norm_ball_x * 1.0 
        
        elif base_pos[0] < -1:
            
            shift = norm_ball_x * (max_forward_shift * 0.8)
        
        else:
            shift = norm_ball_x * max_forward_shift

        
        new_x = np.clip(base_pos[0] + shift, -14.5, 14.5)
        new_y = base_pos[1] 

        shifted_formation.append(np.array([new_x, new_y]))

    
    if len(shifted_formation) < 11:
        dummy_pos = np.array([-100.0, -100.0]) 
        shifted_formation.extend([dummy_pos] * (11 - len(shifted_formation)))

    return shifted_formation[:11]


def GenerateDefense(opponents):
    
    formation = [ ]
    offset = 1.0 

    
    valid_opponents = [opp for opp in opponents if opp is not None and len(opp) == 2 and not np.array_equal(opp, np.array([-100.0, -100.0]))]


    
    for opponent in valid_opponents:
         
        mark_x = np.clip(opponent[0] - offset, -14.5, 14.5)
        mark_y = opponent[1]
        formation.append(np.array([mark_x, mark_y]))

    
    
    fallback_spots = BASE_FORMATION_PLAYON 

    
    num_players_to_add = 11 - len(formation)
    if num_players_to_add > 0:
        available_fallbacks = len(fallback_spots)
        if available_fallbacks > 0:
            
            for i in range(num_players_to_add):
                
                fallback_index = i % available_fallbacks
                formation.append(fallback_spots[fallback_index])
        else: 
            dummy_pos = np.array([-100.0, -100.0])
            formation.extend([dummy_pos] * num_players_to_add)

    return formation[:11]




BASE_DEFENSE_5 = [
    np.array([-14, 0]),
    np.array([-10, -5]),
    np.array([-10, 0]),
    np.array([-10, 5]),
    np.array([-5, 0])
]


BASE_MIDFIELD_5 = [
    np.array([-14, 0]),
    np.array([-8, 0]),
    np.array([-1, -4]),
    np.array([-1, 4]),
    np.array([2, 0])
]


BASE_ATTACK_5 = [
    np.array([-14, 0]),
    np.array([-9, 1]),
    np.array([-2, -1]),
    np.array([11, -2]),
    np.array([11, 2])
]

def GenerateFormation_5(ball_x=0.0):
    
    
    
    if ball_x < -4.0: 
        return BASE_DEFENSE_5
    elif ball_x < 2.0: 
        return BASE_MIDFIELD_5
    else: 
        return BASE_ATTACK_5