import numpy as np

# Define the BASE attacking formation (positions relative to a neutral state)
BASE_FORMATION_PLAYON = [
    np.array([-14, 0]),    # Goalkeeper (Stays back)
    np.array([-7, -4]),   # Left Defender
    np.array([-7, 4]),    # Right Defender
    np.array([-2, 0]),    # Center Defender / Mid
    np.array([3, -5]),    # Left Midfielder
    np.array([3, 5]),     # Right Midfielder
    np.array([6, 0]),     # Center Attacking Mid
    np.array([9, -3]),    # Left Forward
    np.array([9, 3]),     # Right Forward
    np.array([12, -1]),   # Striker Left
    np.array([12, 1])     # Striker Right
]

# --- NEW ---
# Proactive defensive formation (compact, covers defensive third)
BASE_FORMATION_DEFENSE = [
    np.array([-14, 0]),     # Goalkeeper
    np.array([-10, -5]),    # Left Fullback
    np.array([-10, 5]),     # Right Fullback
    np.array([-11, -2]),    # Left Center Back
    np.array([-11, 2]),     # Right Center Back
    np.array([-6, 0]),      # Defensive Mid
    np.array([-6, -4]),     # Left Mid
    np.array([-6, 4]),      # Right Mid
    np.array([-3, -3]),     # Left Wing (for pressure)
    np.array([-3, 3]),      # Right Wing (for pressure)
    np.array([-2, 0])       # Center Forward (for pressure)
]
# --- END NEW ---

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
        base_x = base_pos[0]
        
        # --- MODIFIED LOGIC ---
        
        # Goalkeeper (index 0)
        if i == 0:
             shift = norm_ball_x * 1.0 # GK moves up slightly
        
        # Side Defenders (indices 1, 2) - Stay very defensive
        elif i == 1 or i == 2:
             # Shift much less to stay back
             # Max shift is 7.0 * 0.3 = 2.1. Max X pos = -7 + 2.1 = -4.9
             shift = norm_ball_x * (max_forward_shift * 0.3)
        
        # Center Defender (index 3) - Can push up as defensive mid
        elif i == 3:
             # Max shift is 7.0 * 0.8 = 5.6. Max X pos = -2 + 5.6 = 3.6
             shift = norm_ball_x * (max_forward_shift * 0.8)
        
        # Midfielders/Attackers
        else:
             shift = norm_ball_x * max_forward_shift

        # Calculate new position
        # --- MODIFIED CLIP ---
        # Ensure our side defenders (1, 2) never cross the -4.0 line
        if i == 1 or i == 2:
            max_x_limit = -4.0 # Don't let side defenders push past this line
            new_x = np.clip(base_x + shift, -14.5, max_x_limit)
        else:
            # Other players can push up
            new_x = np.clip(base_x + shift, -14.5, 14.5)
        # --- END MODIFIED ---
            
        new_y = base_pos[1] # Keep Y the same

        shifted_formation.append(np.array([new_x, new_y]))
        # --- END MODIFIED LOGIC ---

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


    # 1. Add marking positions for each valid opponent (REACTIVE part)
    for opponent in valid_opponents:
         # Simple marking: stand slightly behind and towards own goal
         mark_x = np.clip(opponent[0] - offset, -14.5, 14.5)
         mark_y = opponent[1]
         formation.append(np.array([mark_x, mark_y]))

    # --- MODIFIED ---
    # 2. Get fallback spots using the new proactive BASE_FORMATION_DEFENSE
    fallback_spots = BASE_FORMATION_DEFENSE
    # --- END MODIFIED ---

    # 3. Fill remaining spots to ensure 11 total positions (PROACTIVE part)
    num_players_to_add = 11 - len(formation)
    if num_players_to_add > 0:
        available_fallbacks = len(fallback_spots)
        if available_fallbacks > 0:
            # Add fallback spots, prioritizing defenders (lower indices in BASE_FORMATION_DEFENSE)
            for i in range(num_players_to_add):
                # Ensure we don't index out of bounds
                fallback_index = i % available_fallbacks
                formation.append(fallback_spots[fallback_index])
        else: # Should not happen if BASE_FORMATION_DEFENSE is defined
            dummy_pos = np.array([-100.0, -100.0])
            formation.extend([dummy_pos] * num_players_to_add)

    return formation[:11]