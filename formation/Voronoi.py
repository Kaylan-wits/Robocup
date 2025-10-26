import numpy as np
from collections import deque
import math

# --- Field and Grid Constants ---
FIELD_MIN_X = -15.5
FIELD_MAX_X = 15.5
FIELD_MIN_Y = -10.5
FIELD_MAX_Y = 10.5
RESOLUTION = 1.5
GRID_ROWS = int((FIELD_MAX_X - FIELD_MIN_X) / RESOLUTION)
GRID_COLS = int((FIELD_MAX_Y - FIELD_MIN_Y) / RESOLUTION)
OWNER_NONE = -1
OWNER_TEAM = 0
OWNER_OPP = 1


# --- Helper Functions ---
def world_to_grid(world_pos):
    """Converts a continuous (x, y) world coordinate to a discrete (r, c) grid coordinate."""
    x, y = world_pos
    r = int((x - FIELD_MIN_X) / RESOLUTION)
    c = int((y - FIELD_MIN_Y) / RESOLUTION)
    r = max(0, min(r, GRID_ROWS - 1))
    c = max(0, min(c, GRID_COLS - 1))
    return r, c

def grid_to_world(grid_pos):
    """Converts a discrete (r, c) grid coordinate back to a continuous (x, y) world coordinate."""
    r, c = grid_pos
    x = (r * RESOLUTION) + FIELD_MIN_X + (RESOLUTION / 2.0)
    y = (c * RESOLUTION) + FIELD_MIN_Y + (RESOLUTION / 2.0)
    return np.array([x, y])

def calculate_position_score(world_pos, space_dist, is_offensive, ball_pos):
    """
    Calculates the "value" of a grid cell.
    (Using your "minimize space" logic)
    """
    if space_dist < 0.1: # Avoid division by zero / standing on another player
        score = -1000.0 
    else:
        # We reward the INVERSE of the distance.
        score = (1.0 / space_dist) * 5.0 # Multiplier to adjust importance
    
    if is_offensive:
        # --- ATTACK ---
        opp_goal_pos = np.array([15.0, 0.0])
        dist_to_goal = np.linalg.norm(world_pos - opp_goal_pos)
        score -= dist_to_goal * 1.0
        
    else:
        # --- DEFENSE ---
        own_goal_pos = np.array([-15.0, 0.0])
        dist_to_own_goal = np.linalg.norm(world_pos - own_goal_pos)
        dist_to_ball = np.linalg.norm(world_pos - ball_pos)
        score -= dist_to_own_goal * 1.5
        score -= dist_to_ball * 0.5
        if world_pos[0] > -2.0:
            score -= 1000.0
            
    return score


# --- Main Voronoi Logic (Adapted from your Java BFS) ---

def GenerateVoronoiPositions(strategyData, is_offensive=True):
    """
    Generates dynamic formation positions based on a Voronoi diagram (calculated via BFS).
    """
    
    # 1. Initialize Grids
    voronoi_grid = np.full((GRID_ROWS, GRID_COLS), OWNER_NONE, dtype=int)
    distance_grid = np.full((GRID_ROWS, GRID_COLS), np.inf, dtype=float)

    # 2. Initialize Queues (one for teammates, one for opponents)
    q_team = deque()
    q_opp = deque()

    # Add all teammates to the team queue
    for i, pos in enumerate(strategyData.teammate_positions):
        # --- MODIFIED: Do NOT add goalkeeper (player 0) to Voronoi calculation ---
        if i == 0: # Assuming player 1 is index 0
             continue 
        # --- END MODIFIED ---
             
        if pos is not None and not np.array_equal(pos, np.array([-100.0, -100.0])):
            r, c = world_to_grid(pos)
            if voronoi_grid[r, c] == OWNER_NONE:
                q_team.append((r, c, 0)) # (row, col, distance)
                voronoi_grid[r, c] = OWNER_TEAM
                distance_grid[r, c] = 0

    # Add all opponents to the opponent queue
    for pos in strategyData.opponent_positions:
        if pos is not None and not np.array_equal(pos, np.array([-100.0, -100.0])):
            r, c = world_to_grid(pos)
            if voronoi_grid[r, c] == OWNER_NONE:
                q_opp.append((r, c, 0))
                voronoi_grid[r, c] = OWNER_OPP
                distance_grid[r, c] = 0
            elif voronoi_grid[r, c] == OWNER_TEAM:
                voronoi_grid[r, c] = OWNER_OPP
                distance_grid[r, c] = 0


    # 3. Run Multi-Source BFS
    dRow = [-1, 1, 0, 0] # Up, Down
    dCol = [0, 0, -1, 1] # Left, Right
    
    current_dist = 0
    while q_team or q_opp:
        # (BFS logic is unchanged)
        while q_team and q_team[0][2] == current_dist:
            r, c, dist = q_team.popleft()
            for i in range(4):
                nr, nc = r + dRow[i], c + dCol[i]
                if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                    if distance_grid[nr, nc] == np.inf:
                        distance_grid[nr, nc] = dist + 1
                        voronoi_grid[nr, nc] = OWNER_TEAM
                        q_team.append((nr, nc, dist + 1))

        while q_opp and q_opp[0][2] == current_dist:
            r, c, dist = q_opp.popleft()
            for i in range(4):
                nr, nc = r + dRow[i], c + dCol[i]
                if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                    if distance_grid[nr, nc] == np.inf or distance_grid[nr, nc] == (dist + 1):
                        distance_grid[nr, nc] = dist + 1
                        voronoi_grid[nr, nc] = OWNER_OPP
                        q_opp.append((nr, nc, dist + 1))
        current_dist += 1


    # --- ENTIRE SECTION 4 & 5 MODIFIED ---
    
    # 4. Find Best 10 Target Positions for FIELD PLAYERS
    potential_targets = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            # We are only interested in cells our team "owns"
            if voronoi_grid[r, c] == OWNER_TEAM:
                
                world_pos = grid_to_world((r, c))
                
                # Exclude our own penalty box from field player positions
                if world_pos[0] < -12.5 and abs(world_pos[1]) < 5.0:
                    continue
                
                space_dist = distance_grid[r, c]
                score = calculate_position_score(world_pos, space_dist, is_offensive, strategyData.ball_2d)
                potential_targets.append((score, world_pos))

    # Sort targets by score (highest first)
    potential_targets.sort(key=lambda x: x[0], reverse=True)

    # 5. Return Top 11 Positions
    
    # Manually add the Goalkeeper position as the FIRST element
    # This is the fixed spot that Assignment.py will use for Player 1
    goalkeeper_pos = np.array([-14.0, 0.0])
    formation_positions = [goalkeeper_pos]
    
    # Add the top 10 best spots for the field players
    for i in range(10): # Loop 10 times for the 10 field players
        if i < len(potential_targets):
            formation_positions.append(potential_targets[i][1]) # Get the (x,y) pos
        else:
            # Failsafe: if we don't find 10 points (unlikely)
            # Add dummy positions from the base formation
            formation_positions.append(np.array([-12 + i, 0.0])) 

    return formation_positions
    # --- END OF MODIFIED LOGIC ---