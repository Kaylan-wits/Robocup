import numpy as np
import math

# --- HELPER FUNCTION ---
def get_matrix_size(matrix):
    """Helper to get the N from an NxN matrix."""
    # Add check for non-square or empty matrix
    if matrix is None or matrix.ndim != 2 or matrix.shape[0] == 0:
        return 0
    return matrix.shape[0]

def calculateEuclideanDistance(initialPos, formationPos):
    # Add safety checks for None or invalid inputs
    if initialPos is None or formationPos is None:
        return float('inf') # Return large distance if input invalid
    # Ensure they are tuples/lists of size 2
    if len(initialPos) != 2 or len(formationPos) != 2:
         return float('inf')

    initialPosX, initialPosY = initialPos
    formationPosX, formationPosY = formationPos

    xDiff = formationPosX - initialPosX
    yDiff = formationPosY - initialPosY

    distance = math.sqrt((xDiff ** 2) + (yDiff ** 2))

    return distance

# --- SAFE PASS HELPER FUNCTIONS ---
def get_closest_opponent_distance(teammate_pos, opponent_positions):
    """ Finds the distance to the closest opponent (handles None). """
    closest_dist = float('inf')
    # Check if opponent_positions is iterable
    if not hasattr(opponent_positions, '__iter__'): return closest_dist

    for opp_pos in opponent_positions:
        # Check opp_pos validity before calculating distance
        if opp_pos is not None and len(opp_pos)==2 and opp_pos[0] != -100.0:
            dist = calculateEuclideanDistance(teammate_pos, opp_pos)
            if dist < closest_dist:
                closest_dist = dist
    return closest_dist

def is_opponent_in_pass_lane(my_pos, target_pos, opponent_positions, pass_width=0.8):
    """ Checks if an opponent is intersecting the passing lane (handles None). """
    # Check inputs
    if my_pos is None or target_pos is None or not hasattr(opponent_positions, '__iter__'):
        return False # Cannot check lane if positions invalid

    try:
        pass_vec = np.array(target_pos) - np.array(my_pos)
        pass_len = np.linalg.norm(pass_vec)

        if pass_len == 0: return False

        pass_unit_vec = pass_vec / pass_len

        for opp_pos in opponent_positions:
            # Check opp_pos validity
            if opp_pos is None or len(opp_pos)!=2 or opp_pos[0] == -100.0:
                continue

            opp_vec = np.array(opp_pos) - np.array(my_pos)
            proj = np.dot(opp_vec, pass_unit_vec)

            if 0 < proj < pass_len:
                perp_dist = np.linalg.norm(opp_vec - proj * pass_unit_vec)
                if perp_dist < pass_width:
                    return True

    except Exception as e:
        # Catch potential numpy errors with invalid inputs
        print(f"Error in is_opponent_in_pass_lane: {e}")
        return False # Assume blocked if error occurs

    return False

# --- HUNGARIAN ALGORITHM FUNCTIONS (Dynamic Size & Safe) ---
def findMinZeroRow(zeroMatrix, markedPositions):
    minRowInfo = [float('inf'), -1]
    num_players = get_matrix_size(zeroMatrix)
    if num_players == 0: return # Exit if matrix invalid

    for rowIndex in range(num_players):
        # Check if row exists and is valid
        if rowIndex < zeroMatrix.shape[0] and hasattr(zeroMatrix[rowIndex], '__iter__'):
             zeroCount = np.sum(zeroMatrix[rowIndex])
             if zeroCount > 0 and zeroCount < minRowInfo[0]:
                 minRowInfo = [zeroCount, rowIndex]

    # Check if a valid min row was found
    if minRowInfo[1] != -1:
         # Find index safely
         zero_indices = np.where(zeroMatrix[minRowInfo[1]])[0]
         if len(zero_indices) > 0:
              zeroColIndex = zero_indices[0]
              markedPositions.append((minRowInfo[1], zeroColIndex))
              # Safely modify matrix dimensions
              if minRowInfo[1] < zeroMatrix.shape[0]: zeroMatrix[minRowInfo[1], :] = False
              if zeroColIndex < zeroMatrix.shape[1]: zeroMatrix[:, zeroColIndex] = False


def identifyMarkedPositions(matrix):
    num_players = get_matrix_size(matrix)
    if num_players == 0: return [], [], [] # Return empty if invalid

    boolZeroMatrix = (matrix == 0)
    boolZeroMatrixCopy = boolZeroMatrix.copy()

    markedPositions = []
    # Add safety break for potential infinite loops
    max_iters = num_players * num_players
    iters = 0
    while np.any(boolZeroMatrixCopy) and iters < max_iters:
        findMinZeroRow(boolZeroMatrixCopy, markedPositions)
        iters += 1
    if iters >= max_iters: print("Warning: Max iterations reached in identifyMarkedPositions loop")


    markedRows, markedCols = zip(*markedPositions) if markedPositions else ([], [])

    unmarkedRows = list(set(range(num_players)) - set(markedRows))
    finalMarkedCols = []
    hasUpdates = True
    iters = 0 # Safety break
    while hasUpdates and iters < max_iters:
        hasUpdates = False
        for row in unmarkedRows:
             # Check row validity
            if row < boolZeroMatrix.shape[0]:
                 for col in range(boolZeroMatrix.shape[1]):
                     if boolZeroMatrix[row, col] and col not in finalMarkedCols:
                         finalMarkedCols.append(col)
                         hasUpdates = True

        for row, col in markedPositions:
            if row not in unmarkedRows and col in finalMarkedCols:
                 # Check if row is already present before appending
                if row not in unmarkedRows:
                     unmarkedRows.append(row)
                     hasUpdates = True # Should already be True, but safe
        iters += 1
    if iters >= max_iters: print("Warning: Max iterations reached in identifyMarkedPositions update loop")


    finalMarkedRows = list(set(range(num_players)) - set(unmarkedRows))

    return markedPositions, finalMarkedRows, finalMarkedCols

def modifyMatrix(matrix, coveredRows, coveredCols):
    num_players = get_matrix_size(matrix)
    if num_players == 0: return matrix # Return original if invalid

    modifiedMatrix = matrix.copy()
    nonZeroElements = []
    for r in range(num_players):
        if r not in coveredRows:
            for c in range(num_players): # Assuming square matrix
                if c not in coveredCols:
                    # Check indices validity before appending
                    if r < modifiedMatrix.shape[0] and c < modifiedMatrix.shape[1]:
                         nonZeroElements.append(modifiedMatrix[r, c])

    if not nonZeroElements:
        return modifiedMatrix # Fix: return if list is empty

    smallestValue = min(nonZeroElements)
    for r in range(num_players):
        if r not in coveredRows:
             # Check index validity
            if r < modifiedMatrix.shape[0]:
                 modifiedMatrix[r] -= smallestValue # Subtract from entire row
    for c in coveredCols:
         # Check index validity
        if c < modifiedMatrix.shape[1]:
             modifiedMatrix[:, c] += smallestValue # Add to entire column

    return modifiedMatrix

def hungarianMethod(matrix):
    num_players = get_matrix_size(matrix)
    if num_players == 0: return [] # Return empty list if invalid

    adjustedMatrix = matrix.copy()

    # Handle potential errors if matrix is not valid for min operations
    try:
        rowMin = np.min(adjustedMatrix, axis=1)
        adjustedMatrix = adjustedMatrix - rowMin[:, np.newaxis]
        colMin = np.min(adjustedMatrix, axis=0)
        adjustedMatrix = adjustedMatrix - colMin
    except Exception as e:
        print(f"Error during matrix normalization in hungarianMethod: {e}")
        return [] # Return empty if normalization fails

    totalZeros = 0
    iters = 0 # Safety break
    max_iters = num_players * num_players * 2 # Heuristic limit
    positions = [] # Initialize positions outside loop

    while totalZeros < num_players and iters < max_iters:
        positions, markedRows, markedCols = identifyMarkedPositions(adjustedMatrix)
        totalZeros = len(markedRows) + len(markedCols)

        if totalZeros < num_players:
            adjustedMatrix = modifyMatrix(adjustedMatrix, markedRows, markedCols)
        iters +=1
    if iters >= max_iters: print("Warning: Max iterations reached in hungarianMethod main loop")

    # Final check on positions found
    if len(positions) != num_players:
        # If algo failed to find full assignment, try one last identification
        # This can sometimes resolve near-degenerate cases
        positions, _, _ = identifyMarkedPositions(adjustedMatrix)
        if len(positions) != num_players:
             print(f"Warning: Hungarian method did not find a full assignment ({len(positions)}/{num_players})")
             # Could return partial assignment or empty list depending on desired behavior
             # Returning partial for now:
             # return positions
             return [] # Returning empty might be safer

    return positions

def role_assignment(initialPos, formation):
    # Ensure inputs are lists and not empty
    if not isinstance(initialPos, list) or not isinstance(formation, list) or not initialPos or not formation:
        print("Warning: Invalid input to role_assignment")
        return {}

    num_players = len(initialPos)
    # Ensure formation is at least as long as initialPos
    if len(formation) < num_players:
        print("Warning: Formation list shorter than player list in role_assignment")
        # Pad formation with dummy positions if needed (or return error)
        dummy_pos = np.array([-100.0, -100.0])
        formation = formation + [dummy_pos] * (num_players - len(formation))

    formation_sized = formation[:num_players]

    cost_matrix = np.zeros((num_players, num_players))

    for r in range(num_players):
        for c in range(num_players):
            # Calculate distance safely
            cost_matrix[r][c] = calculateEuclideanDistance(initialPos[r], formation_sized[c])

    # Handle potential errors during hungarian method
    try:
        cost_copy = cost_matrix.copy()
        positions = hungarianMethod(cost_copy)
    except Exception as e:
        print(f"Error calling hungarianMethod in role_assignment: {e}")
        return {} # Return empty dict on error

    point_preferences = {}
    for i, (row, col) in enumerate(positions):
         # Check index validity before assignment
        if row < num_players and col < len(formation_sized):
             # Player numbers are 1-based, row index is 0-based
             point_preferences[row + 1] = formation_sized[col]

    return point_preferences

# --- SAFE PASS TARGET FUNCTION ---
def find_safe_pass_target(my_unum, my_pos, teammate_positions, opponent_positions):
    """ Finds the best teammate to pass to based on safety (handles None). """
    best_target = None
    best_score = 0
    MIN_OPEN_DISTANCE = 1.5

    # Safety checks on inputs
    if my_pos is None or not hasattr(teammate_positions, '__iter__') or not hasattr(opponent_positions, '__iter__'):
        return None

    for i, teammate_pos in enumerate(teammate_positions):
        teammate_unum = i + 1

        # --- Filter out bad targets ---
        if teammate_unum == my_unum: continue
        # Check teammate_pos validity
        if teammate_pos is None or len(teammate_pos)!=2 or teammate_pos[0] == -100.0: continue
        if teammate_pos[0] < my_pos[0] - 2.0: continue

        # --- Check if teammate is MARKED ---
        open_dist = get_closest_opponent_distance(teammate_pos, opponent_positions)
        if open_dist < MIN_OPEN_DISTANCE:
            continue

        # --- Check if pass lane is BLOCKED ---
        if is_opponent_in_pass_lane(my_pos, teammate_pos, opponent_positions):
            continue

        # --- This is a SAFE pass! Score based on openness and position ---
        score = (open_dist * 10) + (teammate_pos[0] * 5)

        if score > best_score:
            best_score = score
            best_target = teammate_pos

    if best_target is not None:
        # Pass slightly in front of them
        return (best_target[0] + 0.5, best_target[1])
    else:
        return None # No safe pass found