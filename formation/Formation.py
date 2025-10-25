import numpy as np

def GenerateOffense(strategyData):
    """
    Generates dynamic offensive positions based on ball position.
    This keeps the team structure but shifts it with the play.
    """
    ball_x = strategyData.ball_2d[0]
    ball_y = strategyData.ball_2d[1]

    # Create a "neutral" x-position for the formation, clamped to our half
    # We want our formation to be "behind" the ball to support an attack
    base_x = np.clip(ball_x - 3.0, -14.0, 5.0) 
    
    # Shift y-positions to follow the ball, but less aggressively
    base_y = ball_y * 0.5 

    positions = {
        # (Role: [X_offset, Y_offset])
        # Goalie is static
        1: (-14, 0),  
        # Defenders push up with the play, but not too far
        2: (np.clip(base_x + 3, -13, 0), base_y + 5), 
        3: (np.clip(base_x + 3, -13, 0), base_y - 5),
        4: (np.clip(base_x + 2, -13, 0), base_y),      
        # Mids shift with the ball
        5: (base_x + 8, base_y + 6),
        6: (base_x + 8, base_y),
        7: (base_x + 8, base_y - 6),
        # Attackers stay ahead, creating space
        8: (base_x + 13, base_y + 7),
        9: (base_x + 13, base_y),
        10: (base_x + 13, base_y - 7),
        # Cherry Picker stays high, but shifts side-to-side
        11: (10, np.clip(ball_y, -5, 5)) 
    }

    # Clamp all positions to be on the field
    for unum, (x, y) in positions.items():
        positions[unum] = (np.clip(x, -15.0, 15.0), np.clip(y, -10.0, 10.0))

    return positions

def GenerateDefense(strategyData):
    """
    Generates dynamic defensive positions.
    Focuses on getting between the ball and the goal (ball-marking).
    """
    ball_pos = strategyData.ball_2d
    goal_pos = strategyData.own_goal_pos # (-15.5, 0)
    
    positions = {}
    
    # Goalie
    positions[1] = (-14, np.clip(ball_pos[1], -1.5, 1.5)) # Cover goal angle

    # Create defensive line X-positions
    # We want the line to be between the ball and goal
    # If ball is deep, line is deep. If ball is mid, line is mid.
    def_x_line = np.clip(ball_pos[0] - 2.0, -13.0, 0.0)

    # Defenders (2, 3, 4) form a line that blocks the ball
    positions[4] = (def_x_line, ball_pos[1]) # Closest defender marks ball y
    positions[2] = (def_x_line, ball_pos[1] + 4.0) # Side defender
    positions[3] = (def_x_line, ball_pos[1] - 4.0) # Side defender
    
    # Midfielders (5, 6, 7) form a second line
    mid_x_line = np.clip(ball_pos[0] + 1.0, -10.0, 5.0)
    positions[6] = (mid_x_line, ball_pos[1]) # Center mid
    positions[5] = (mid_x_line, ball_pos[1] + 5.0) # Side mid
    positions[7] = (mid_x_line, ball_pos[1] - 5.0) # Side mid

    # Attackers (8, 9, 10) drop back to cover passes
    att_x_line = np.clip(ball_pos[0] + 4.0, -5.0, 8.0)
    positions[9] = (att_x_line, ball_pos[1])
    positions[8] = (att_x_line, ball_pos[1] + 6.0)
    positions[10] = (att_x_line, ball_pos[1] - 6.0)

    # Cherry Picker (11) drops back to midfield
    positions[11] = (5, ball_pos[1])
    
    # Clamp all positions to be on the field
    for unum, (x, y) in positions.items():
        positions[unum] = (np.clip(x, -15.0, 15.0), np.clip(y, -10.0, 10.0))

    return positions

# This is the old function, which we are no longer using.
# You can delete it, but I'm leaving it here for reference.
def GeneratePlayOn():
    """
    Generates static 'Play On' positions.
    --- THIS IS DEPRECATED ---
    """
    positions = {
        1: (-14, 0),  # Goalie
        2: (-11, 4),  # Defender
        3: (-11, -4), # Defender
        4: (-11, 0),  # Defender
        5: (-5, -5),  # Mid
        6: (-5, 0),   # Mid
        7: (-5, 5),   # Mid
        8: (-1, -6),  # Attacker
        9: (-1, -2.5),# Attacker
        10: (-1, 2.5),# Attacker
        11: (10, 0)   # Cherry Picker
    }
    return positions