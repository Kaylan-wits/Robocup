import numpy as np

# --- 11 PLAYER FORMATIONS (Originals) ---
# We leave these here in case they are needed elsewhere

BASE_FORMATION_PLAYON = [
    np.array([-14, 0]),     # Goalkeeper (Stays back)
    np.array([-7, -4]),    # Left Defender
    np.array([-7, 4]),     # Right Defender
    np.array([-2, 0]),     # Center Defender / Mid
    np.array([3, -5]),     # Left Midfielder
    np.array([3, 5]),      # Right Midfielder
    np.array([6, 0]),      # Center Attacking Mid
    np.array([9, -3]),     # Left Forward
    np.array([9, 3]),      # Right Forward
    np.array([12, -1]),    # Striker Left
    np.array([12, 1])      # Striker Right
]

def GeneratePlayOn(ball_x=0.0): # Takes ball's X-coordinate as input
    """Generates a dynamic attacking formation that shifts based on ball position."""

    shifted_formation = []

    # Calculate a shift factor based on ball position
    # Normalize ball_x from -15 (own goal) to +15 (opp goal) to a 0-1 range
    # Clamp ball_x to avoid extreme shifts near goal lines
    clamped_ball_x = np.clip(ball_x, -14.0, 14.0)
    norm_ball_x = (clamped_ball_x + 14.0) / 28.0 # Range 0 to 1

    # Define max shift (how far players push up at max attack)
    max_forward_shift = 7.0 # Increased from 6.0 for more aggression

    # Apply shift based on ball position and player's base X-coordinate
    for i, base_pos in enumerate(BASE_FORMATION_PLAYON):
        # Goalkeeper (index 0) doesn't shift much
        if i == 0:
            shift = norm_ball_x * 1.0 # GK moves up slightly
        # Defenders (indices 1, 2, 3) shift less
        elif base_pos[0] < -1:
            # Increased defender shift from 0.6 to 0.8
            shift = norm_ball_x * (max_forward_shift * 0.8)
        # Midfielders/Attackers shift more
        else:
            shift = norm_ball_x * max_forward_shift

        # Calculate new position, ensuring players don't go too far past goal lines
        new_x = np.clip(base_pos[0] + shift, -14.5, 14.5)
        new_y = base_pos[1] # Keep Y the same for simplicity

        shifted_formation.append(np.array([new_x, new_y]))

    # Ensure it always returns 11 positions
    if len(shifted_formation) < 11:
        dummy_pos = np.array([-100.0, -100.0]) # Use a far-off dummy
        shifted_formation.extend([dummy_pos] * (11 - len(shifted_formation)))

    return shifted_formation[:11]


def GenerateDefense(opponents):
    """Generates a defensive formation based on opponent positions, padded to 11."""
    formation = [ ]
    offset = 1.0 # Stand slightly offset from opponent

    # Ensure opponents is a list of valid positions
    valid_opponents = [opp for opp in opponents if opp is not None and len(opp) == 2 and not np.array_equal(opp, np.array([-100.0, -100.0]))]


    # 1. Add marking positions for each valid opponent
    for opponent in valid_opponents:
         # Simple marking: stand slightly behind and towards own goal
         mark_x = np.clip(opponent[0] - offset, -14.5, 14.5)
         mark_y = opponent[1]
         formation.append(np.array([mark_x, mark_y]))

    # 2. Get fallback spots using the BASE attacking formation
    #    (Using base ensures defenders stay back even if few opponents are seen)
    fallback_spots = BASE_FORMATION_PLAYON # Use the base, not dynamically shifted version

    # 3. Fill remaining spots to ensure 11 total positions
    num_players_to_add = 11 - len(formation)
    if num_players_to_add > 0:
        available_fallbacks = len(fallback_spots)
        if available_fallbacks > 0:
            # Add fallback spots, prioritizing defenders (lower indices in BASE_FORMATION_PLAYON)
            for i in range(num_players_to_add):
                # Ensure we don't index out of bounds if fallback_spots is somehow < 11
                fallback_index = i % available_fallbacks
                formation.append(fallback_spots[fallback_index])
        else: # Should not happen if BASE_FORMATION_PLAYON is defined
            dummy_pos = np.array([-100.0, -100.0])
            formation.extend([dummy_pos] * num_players_to_add)

    return formation[:11]


# --- 5 PLAYER FORMATIONS ---

# 1-3-1 Defensive Formation (When ball is in our third, x < -7)
BASE_DEFENSE_5 = [
    np.array([-14, 0]),   # 1. Goalkeeper
    np.array([-10, -5]),  # 2. Left Defender
    np.array([-10, 0]),   # 3. Center Defender
    np.array([-10, 5]),   # 4. Right Defender
    np.array([-5, 0])     # 5. Holding Midfielder
]

# 1-1-2-1 Midfield Formation (When ball is in middle third, -7 < x < 7)
BASE_MIDFIELD_5 = [
    np.array([-14, 0]),   # 1. Goalkeeper
    np.array([-8, 0]),    # 2. "Quarterback" Defender
    np.array([0, -4]),    # 3. Left Midfielder
    np.array([0, 4]),     # 4. Right Midfielder
    np.array([6, 0])      # 5. Attacking Midfielder
]

# 1-1-1-2 Attack Formation (When ball is in their third, x > 7)
BASE_ATTACK_5 = [
    np.array([-14, 0]),   # 1. Goalkeeper
    np.array([-6, 0]),    # 2. Defender
    np.array([2, 0]),     # 3. Midfielder
    np.array([9, -3]),    # 4. Left Striker
    np.array([9, 3])      # 5. Right Striker
]

def GenerateFormation_5(ball_x=0.0):
    """
    Selects the best 5-player formation based on the ball's X-position.
    """
    if ball_x < -7.0: # Ball is deep in our half
        return BASE_DEFENSE_5
    elif ball_x < 7.0: # Ball is in the midfield
        return BASE_MIDFIELD_5
    else: # Ball is deep in their half
        return BASE_ATTACK_5