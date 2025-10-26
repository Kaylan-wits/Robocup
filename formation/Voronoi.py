import numpy as np
from collections import deque
import math

# --- Field and Grid Constants ---
# Field dimensions (approx. -15.5 to 15.5 x, -10.5 to 10.5 y)
FIELD_MIN_X = -15.5
FIELD_MAX_X = 15.5
FIELD_MIN_Y = -10.5
FIELD_MAX_Y = 10.5

# Grid resolution (e.g., 0.5m per cell)
RESOLUTION = 1.5 # Was 0.5, increasing this makes the grid coarser and faster

# Calculate grid dimensions
GRID_ROWS = int((FIELD_MAX_X - FIELD_MIN_X) / RESOLUTION)
GRID_COLS = int((FIELD_MAX_Y - FIELD_MIN_Y) / RESOLUTION)

# Player "owners"
OWNER_NONE = -1
OWNER_TEAM = 0  # Represents any of our teammates
OWNER_OPP = 1   # Represents any of our opponents


# --- Helper Functions ---

def world_to_grid(world_pos):
    """Converts a continuous (x, y) world coordinate to a discrete (r, c) grid coordinate."""
    x, y = world_pos
    r = int((x - FIELD_MIN_X) / RESOLUTION)
    c = int((y - FIELD_MIN_Y) / RESOLUTION)
    
    # Clamp to grid boundaries
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
    High "space_dist" (distance from nearest player) is always good.
    """
    score = space_dist * 2.0  # Base score is for controlling space
    
    if is_offensive:
        # --- ATTACK ---
        # We want space that is ALSO near the opponent goal
        # This fixes your "passive" problem by rewarding forward positions.
        opp_goal_pos = np.array([15.0, 0.0])
        dist_to_goal = np.linalg.norm(world_pos - opp_goal_pos)
        
        # Bonus for being closer to goal (subtract distance)
        score -= dist_to_goal * 1.0
        
    else:
        # --- DEFENSE ---
        # We want space that is ALSO near our goal and near the ball.
        # This fixes your "too far up" problem by rewarding defensive positions.
        own_goal_pos = np.array([-15.0, 0.0])
        dist_to_own_goal = np.linalg.norm(world_pos - own_goal_pos)
        dist_to_ball = np.linalg.norm(world_pos - ball_pos)
        
        # Penalize distance from own goal and ball
        score -= dist_to_own_goal * 1.5
        score -= dist_to_ball * 0.5
        
        # Heavy penalty for being in the opponent's half
        if world_pos[0] > -2.0:
            score -= 1000.0
            
    return score


# --- Main Voronoi Logic (Adapted from your Java BFS) ---

def GenerateVoronoiPositions(strategyData, is_offensive=True):
    """
    Generates dynamic formation positions based on a Voronoi diagram (calculated via BFS).
    """
    
    # 1. Initialize Grids
    # 'voronoi_grid' stores *who* owns the cell (OWNER_TEAM, OWNER_OPP, OWNER_NONE)
    voronoi_grid = np.full((GRID_ROWS, GRID_COLS), OWNER_NONE, dtype=int)
    
    # 'distance_grid' stores the distance (in steps) to the *nearest* player
    distance_grid = np.full((GRID_ROWS, GRID_COLS), np.inf, dtype=float)

    # 2. Initialize Queues (one for teammates, one for opponents)
    # This is a simplification of your N-queue system. We just need to know
    # if a cell is owned by US or THEM.
    q_team = deque()
    q_opp = deque()

    # Add all teammates to the team queue
    for pos in strategyData.teammate_positions:
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
                # A teammate and opponent are on the same cell, mark as opponent's
                voronoi_grid[r, c] = OWNER_OPP
                distance_grid[r, c] = 0


    # 3. Run Multi-Source BFS (like your Java 'while(hasNodes)')
    dRow = [-1, 1, 0, 0] # Up, Down
    dCol = [0, 0, -1, 1] # Left, Right
    
    current_dist = 0
    while q_team or q_opp:
        
        # --- Process Team Queue Layer ---
        while q_team and q_team[0][2] == current_dist:
            r, c, dist = q_team.popleft()
            
            # Check neighbors
            for i in range(4):
                nr, nc = r + dRow[i], c + dCol[i]
                
                # Check bounds and if already visited
                if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                    if distance_grid[nr, nc] == np.inf: # Not visited yet
                        distance_grid[nr, nc] = dist + 1
                        voronoi_grid[nr, nc] = OWNER_TEAM
                        q_team.append((nr, nc, dist + 1))

        # --- Process Opponent Queue Layer ---
        while q_opp and q_opp[0][2] == current_dist:
            r, c, dist = q_opp.popleft()
            
            # Check neighbors
            for i in range(4):
                nr, nc = r + dRow[i], c + dCol[i]
                
                # Check bounds
                if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                    # Only claim if it's unvisited OR if we reached it at the same time as the team
                    if distance_grid[nr, nc] == np.inf or distance_grid[nr, nc] == (dist + 1):
                        distance_grid[nr, nc] = dist + 1
                        voronoi_grid[nr, nc] = OWNER_OPP
                        q_opp.append((nr, nc, dist + 1))
        
        current_dist += 1


    # 4. Find Best 11 Target Positions
    potential_targets = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            # We are only interested in cells our team "owns"
            if voronoi_grid[r, c] == OWNER_TEAM:
                
                world_pos = grid_to_world((r, c))
                space_dist = distance_grid[r, c] # This is the "distance to nearest player"
                
                # Score the position
                score = calculate_position_score(world_pos, space_dist, is_offensive, strategyData.ball_2d)
                potential_targets.append((score, world_pos))

    # Sort targets by score (highest first)
    potential_targets.sort(key=lambda x: x[0], reverse=True)

    # 5. Return Top 11 Positions
    formation_positions = []
    for i in range(11):
        if i < len(potential_targets):
            formation_positions.append(potential_targets[i][1]) # Get the (x,y) pos
        else:
            # Failsafe: if we don't find 11 points (unlikely)
            # Add dummy positions from the base formation
            formation_positions.append(np.array([-14 + i, 0.0])) 

    return formation_positions