# formation/Formation.py

import numpy as np
import itertools
import math
from .formation_data_5v5 import FORMATION_DATA # Import from the new file

# Define field boundaries (adjust if your field dimensions are different)
FIELD_X_LIMIT = 15.0 # Example: meters
FIELD_Y_LIMIT = 10.0 # Example: meters
# Add a small buffer inward from the absolute edge
CLIP_BUFFER = 0.2
CLIP_X_MIN = -FIELD_X_LIMIT + CLIP_BUFFER
CLIP_X_MAX = FIELD_X_LIMIT - CLIP_BUFFER
CLIP_Y_MIN = -FIELD_Y_LIMIT + CLIP_BUFFER
CLIP_Y_MAX = FIELD_Y_LIMIT + CLIP_BUFFER


# --- Helper Functions for Triangulation/Interpolation ---
# (get_barycentric_coords, find_containing_triangle, interpolate_positions remain the same as previous version)
def get_barycentric_coords(p, a, b, c):
    """Calculates barycentric coordinates of point p with respect to triangle abc."""
    try:
        v0 = b - a
        v1 = c - a
        v2 = p - a

        d00 = np.dot(v0, v0)
        d01 = np.dot(v0, v1)
        d11 = np.dot(v1, v1)
        d20 = np.dot(v2, v0)
        d21 = np.dot(v2, v1)

        denom = d00 * d11 - d01 * d01
        if abs(denom) < 1e-9: # Triangle is degenerate (collinear points)
            return None # Cannot compute valid coordinates

        v = (d11 * d20 - d01 * d21) / denom
        w = (d00 * d21 - d01 * d20) / denom
        u = 1.0 - v - w

        # Clamp coords slightly due to potential floating point inaccuracies
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))
        w = max(0.0, min(1.0, w))
        # Renormalize
        coord_sum = u + v + w
        if coord_sum > 1e-9:
             u /= coord_sum
             v /= coord_sum
             w /= coord_sum

        return u, v, w
    except Exception as e:
        print(f"Error in get_barycentric_coords: {e}")
        return None


def find_containing_triangle(point, reference_points):
    """
    Finds the indices of the vertices of a triangle in reference_points
    that contains the point. Returns (index_a, index_b, index_c), (u, v, w) or None.
    This version iterates through all triangles - can be slow.
    """
    num_points = len(reference_points)
    if num_points < 3:
        return None, None # Need at least 3 points

    # Find the 3 nearest neighbors first as potential candidates
    distances = np.linalg.norm(reference_points - point, axis=1)
    nearest_indices = np.argsort(distances)

    # Check triangles formed by nearby points first
    candidate_indices = nearest_indices[:min(num_points, 15)] # Check nearest ~15 points

    for indices in itertools.combinations(candidate_indices, 3):
        idx_a, idx_b, idx_c = indices
        a = reference_points[idx_a]
        b = reference_points[idx_b]
        c = reference_points[idx_c]

        coords = get_barycentric_coords(point, a, b, c)

        if coords is not None:
            u, v, w = coords
            # Check if point is inside or very close to edge
            if u >= -1e-6 and v >= -1e-6 and w >= -1e-6:
                 return indices, (u, v, w) # Return normalized coords

    # Fallback: Check all triangles if not found among nearest (SLOW)
    # print("Warning: Point not in nearest triangles, checking all (slow)...")
    # for indices in itertools.combinations(range(num_points), 3):
    #      # (Same logic as above loop) ...
    #      pass

    return None, None # Point not found inside any triangle


def interpolate_positions(indices, coords, target_positions_lookup, roles_to_calculate):
    """Interpolates positions for specified roles using barycentric coordinates."""
    if indices is None or coords is None:
        print("Error: Cannot interpolate, invalid indices or coords.")
        return None

    idx_a, idx_b, idx_c = indices
    u, v, w = coords

    interpolated_positions = {}

    try:
        # Get the target positions dictionaries for the triangle vertices
        pos_a_all_roles = target_positions_lookup[idx_a]
        pos_b_all_roles = target_positions_lookup[idx_b]
        pos_c_all_roles = target_positions_lookup[idx_c]

        for role_idx in roles_to_calculate:
            # Role index might be int, keys in dict might be str
            role_key = str(role_idx)

            # Check if role exists for all vertices
            if (role_key in pos_a_all_roles and
                role_key in pos_b_all_roles and
                role_key in pos_c_all_roles):

                pos_a = pos_a_all_roles[role_key]
                pos_b = pos_b_all_roles[role_key]
                pos_c = pos_c_all_roles[role_key]

                # Ensure positions are numpy arrays
                pos_a = np.array(pos_a) if not isinstance(pos_a, np.ndarray) else pos_a
                pos_b = np.array(pos_b) if not isinstance(pos_b, np.ndarray) else pos_b
                pos_c = np.array(pos_c) if not isinstance(pos_c, np.ndarray) else pos_c

                # Interpolate: P = u*A + v*B + w*C
                interp_pos = u * pos_a + v * pos_b + w * pos_c
                interpolated_positions[role_idx] = interp_pos # Store with int key
            else:
                 print(f"Warning: Role index {role_idx} (key: {role_key}) missing in target_positions_lookup for triangle {indices}")
                 interpolated_positions[role_idx] = np.array([-100.0, -100.0]) # Default/dummy
    except IndexError:
         print(f"Error: Index out of bounds accessing target_positions_lookup with indices {indices}")
         return None
    except KeyError as e:
         print(f"Error: Key {e} not found in target positions dictionary for triangle {indices}")
         return None
    except Exception as e:
         print(f"Unexpected error during interpolation: {e}")
         return None

    return interpolated_positions

# --- Pre-process Data (Run once when module is loaded) ---
# (This section remains the same as previous version)
_FORMATION_DATA_5V5 = FORMATION_DATA
_REFERENCE_BALL_POINTS = np.array([[item['ball']['x'], item['ball']['y']]
                                  for item in _FORMATION_DATA_5V5['data']])
_TARGET_POSITIONS_LOOKUP = []
_DEFINED_ROLE_KEYS = list(_FORMATION_DATA_5V5['data'][0]['positions'].keys())
_DEFINED_ROLES_INT = [int(k) for k in _DEFINED_ROLE_KEYS]

for i, item in enumerate(_FORMATION_DATA_5V5['data']):
    player_pos_dict = {}
    for role_key in _DEFINED_ROLE_KEYS:
         pos = item['positions'][role_key]
         player_pos_dict[role_key] = np.array([pos['x'], pos['y']])
    _TARGET_POSITIONS_LOOKUP.append(player_pos_dict)
# ---

# --- Formation Generation Functions ---

def GeneratePlayOn(ball_x=0.0, ball_y=0.0): # Takes ball's X and Y
    """Generates a dynamic attacking formation using manual triangulation/interpolation."""
    current_ball_pos = np.array([ball_x, ball_y])

    # 1. Find the containing triangle for the current ball position
    indices, coords = find_containing_triangle(current_ball_pos, _REFERENCE_BALL_POINTS)

    calculated_positions_dict = {} # Dict {player_unum: np.array([x, y]), ...}
    raw_interpolated_positions = {} # Store pre-clipping values for debugging

    if indices is not None:
        # 2. Interpolate positions for the defined roles
        interpolated_role_positions = interpolate_positions(indices, coords,
                                                            _TARGET_POSITIONS_LOOKUP,
                                                            _DEFINED_ROLES_INT)

        if interpolated_role_positions is None:
            print("Error: Interpolation failed. Using fallback.")
            indices = None # Force fallback
        else:
             raw_interpolated_positions = interpolated_role_positions # Store for potential debugging
            # 3. Map interpolated role positions back to your player numbers (1-5)
             for player_unum, role_index in _FORMATION_DATA_5V5['roles'].items():
                 if role_index in interpolated_role_positions:
                     pos = interpolated_role_positions[role_index]
                     # ***** ADD CLIPPING HERE *****
                     clipped_pos = np.array([
                         np.clip(pos[0], CLIP_X_MIN, CLIP_X_MAX),
                         np.clip(pos[1], CLIP_Y_MIN, CLIP_Y_MAX)
                     ])
                     calculated_positions_dict[player_unum] = clipped_pos
                 else:
                     print(f"Warning: Role {role_index} for player {player_unum} not found in interpolated results.")
                     calculated_positions_dict[player_unum] = np.array([-100.0, -100.0])

    # Fallback if triangle not found OR interpolation failed
    if indices is None:
        distances = np.linalg.norm(_REFERENCE_BALL_POINTS - current_ball_pos, axis=1)
        nearest_ref_index = np.argmin(distances)
        nearest_positions_all_roles = _TARGET_POSITIONS_LOOKUP[nearest_ref_index]

        # print(f"Warning: Ball pos {current_ball_pos} outside hull or interp failed. Using nearest ref point {nearest_ref_index}.")

        for player_unum, role_index in _FORMATION_DATA_5V5['roles'].items():
            role_key = str(role_index)
            if role_key in nearest_positions_all_roles:
                 pos = nearest_positions_all_roles[role_key]
                 raw_interpolated_positions[role_index] = pos # Store for debugging
                 # ***** ADD CLIPPING HERE (Fallback) *****
                 clipped_pos = np.array([
                     np.clip(pos[0], CLIP_X_MIN, CLIP_X_MAX),
                     np.clip(pos[1], CLIP_Y_MIN, CLIP_Y_MAX)
                 ])
                 calculated_positions_dict[player_unum] = clipped_pos
            else:
                 print(f"Warning: Role {role_index} (key: {role_key}) for player {player_unum} not found in fallback data.")
                 calculated_positions_dict[player_unum] = np.array([-100.0, -100.0])

    # Optional: Debugging print statement
    # print(f"Ball: ({ball_x:.2f},{ball_y:.2f}) -> Raw: {raw_interpolated_positions} -> Clipped: {calculated_positions_dict}")

    # Convert to the required output format (list for players 1-5)
    formation_list = [np.array([-100.0, -100.0])] * 5
    for unum in range(1, 6):
        if unum in calculated_positions_dict:
            formation_list[unum - 1] = calculated_positions_dict[unum]
        else:
            print(f"Warning: Player unum {unum} not found in final calculated positions.")

    return formation_list


def GenerateDefense(opponents):
    """
    Generates a defensive formation based on opponent positions.
    (Keeping the original logic, assuming it's still desired for defense).
    Adjusted to return only 5 positions and adds clipping.
    """
    formation_raw = [] # Store pre-clipped positions
    offset = 1.0

    # Base positions for fallback (Adjust Y as needed for your field)
    BASE_DEFENSE_FALLBACK = [
        np.array([-14, 0]),    # Goalkeeper (Role 1)
        np.array([-7, -4]),   # Left CB (Role 2)
        np.array([-7, 4]),    # Right CB (Role 3)
        np.array([-10, -8]),  # Left SB (Role 4 example)
        np.array([-10, 8]),  # Right SB (Role 5 example)
    ]

    valid_opponents = [opp for opp in opponents if opp is not None and len(opp) == 2 and not np.array_equal(opp, np.array([-100.0, -100.0]))]
    valid_opponents.sort(key=lambda p: p[0]) # Prioritize marking opponents further forward

    # 1. Add marking positions (up to 4 markers for 5v5, GK doesn't mark)
    num_markers = 0
    max_markers = 4
    for opponent in valid_opponents:
         if num_markers < max_markers:
             mark_x = opponent[0] - offset # Stand behind
             mark_y = opponent[1]
             formation_raw.append(np.array([mark_x, mark_y]))
             num_markers += 1

    # 2. Fill remaining spots (up to 5 total) with fallback positions
    num_players_to_add = 5 - len(formation_raw)
    fallback_spots_used = 0
    if num_players_to_add > 0:
        for i in range(len(BASE_DEFENSE_FALLBACK)):
             if fallback_spots_used < num_players_to_add:
                 formation_raw.append(BASE_DEFENSE_FALLBACK[i])
                 fallback_spots_used += 1

    # Ensure exactly 5 positions, padding if necessary
    while len(formation_raw) < 5:
        formation_raw.append(np.array([-100.0, -100.0]))
    formation_raw = formation_raw[:5]

    # 3. Clip all calculated positions
    formation_clipped = []
    for pos in formation_raw:
         if not np.array_equal(pos, np.array([-100.0, -100.0])):
             clipped_pos = np.array([
                 np.clip(pos[0], CLIP_X_MIN, CLIP_X_MAX),
                 np.clip(pos[1], CLIP_Y_MIN, CLIP_Y_MAX)
             ])
             formation_clipped.append(clipped_pos)
         else:
             formation_clipped.append(pos) # Keep dummy positions as is

    return formation_clipped # Return exactly 5 clipped positions