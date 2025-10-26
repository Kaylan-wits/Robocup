import numpy as np

# --- 5-PLAYER ATTACK FORMATION ---
# 1-1-2 (Goalie, Defender, Mid, 2 Forwards)
BASE_FORMATION_PLAYON_5V5 = [
    np.array([-14, 0]),   # Goalkeeper
    np.array([-7, 0]),    # Central Defender
    np.array([1, 0]),     # Central Midfielder
    np.array([8, -4]),    # Left Forward
    np.array([8, 4])      # Right Forward
]

# --- 5-PLAYER DEFENSE FORMATION ---
# 1-2-1 (Goalie, 2 Defenders, 1 Mid/Stopper, 1 Mid)
BASE_FORMATION_DEFENSE_5V5 = [
    np.array([-14, 0]),   # Goalkeeper
    np.array([-10, -4]),  # Left Defender
    np.array([-10, 4]),   # Right Defender
    np.array([-5, 0]),    # Defensive Mid
    np.array([-1, 0])     # Center Mid (provides some pressure)
]

def GeneratePlayOn(ball_x=0.0):
    """Generates a dynamic 5-PLAYER attacking formation based on ball_x."""
    shifted_formation = []
    NUM_PLAYERS = 5 # Define size explicitly

    # Safety check for ball_x type
    if not isinstance(ball_x, (int, float)): ball_x = 0.0

    clamped_ball_x = np.clip(ball_x, -14.0, 14.0)
    # Avoid division by zero if range is zero (shouldn't happen here)
    norm_ball_x = (clamped_ball_x + 14.0) / 28.0 if 28.0 != 0 else 0.5
    max_forward_shift = 7.0

    for i, base_pos in enumerate(BASE_FORMATION_PLAYON_5V5):
         # Ensure base_pos is valid
        if base_pos is None or len(base_pos) != 2: continue # Skip invalid base positions

        shift = 0.0 # Default shift
        if i == 0: # Goalkeeper
            shift = norm_ball_x * 1.0
        elif base_pos[0] < -5: # Defender
            shift = norm_ball_x * (max_forward_shift * 0.8)
        else: # Mid/Attackers
            shift = norm_ball_x * max_forward_shift

        new_x = np.clip(base_pos[0] + shift, -14.5, 14.5)
        new_y = base_pos[1]
        shifted_formation.append(np.array([new_x, new_y]))

    # Ensure exactly NUM_PLAYERS positions are returned
    current_len = len(shifted_formation)
    if current_len < NUM_PLAYERS:
        dummy_pos = np.array([-100.0, -100.0])
        shifted_formation.extend([dummy_pos] * (NUM_PLAYERS - current_len))

    return shifted_formation[:NUM_PLAYERS] # Return exactly 5

def GenerateDefense(opponents):
    """Generates a 5-PLAYER defensive formation (currently static zonal)."""
    # opponents parameter is currently unused but kept for potential future use
    NUM_PLAYERS = 5

    # Start with the base defensive formation positions
    # Use .copy() to avoid modifying the original list if elements are changed later
    formation = [pos.copy() for pos in BASE_FORMATION_DEFENSE_5V5]

    # Future enhancement: Could adjust positions slightly based on opponent locations
    # e.g., shift defenders towards the side with more opponents

    # Ensure exactly NUM_PLAYERS positions are returned
    current_len = len(formation)
    if current_len < NUM_PLAYERS:
        dummy_pos = np.array([-100.0, -100.0])
        formation.extend([dummy_pos] * (NUM_PLAYERS - current_len))

    return formation[:NUM_PLAYERS] # Return exactly 5