import numpy as np

# --- Offensive Formation (Renamed from Basic) ---
def GeneratePlayOn():
    # Keep the same basic offensive formation points 
    # (Using 11 points from amaan-hans init_pos for consistency)
     return { 
        1: np.array([-14, 0]), 
        2: np.array([-9, -5]), 
        3: np.array([-9, 0]), 
        4: np.array([-9, 5]), 
        5: np.array([-5, -5]), 
        6: np.array([-5, 0]), 
        7: np.array([-5, 5]), 
        8: np.array([-2, -6]), 
        9: np.array([-2, -2.5]), 
        10: np.array([-2, 2.5]), 
        11: np.array([-2, 6]) # Note: Cherry Picker (11) will ignore this in Agent.py
    }

# --- Defensive Formation (from muzzaam/test34) ---
def GenerateDefense(opponent_positions):
    """
    Generates defensive positions based on opponent locations.
    Tries to mark the closest opponents. Simple version.
    """
    num_opponents = sum(1 for pos in opponent_positions if pos is not None)
    
    # Basic defensive shell, slightly deeper than offensive midfield
    defense_positions = {
        1: np.array([-14, 0]),     # Goalie stays put
        2: np.array([-10, -4]),    # Left Back
        3: np.array([-11, 0]),     # Center Back
        4: np.array([-10, 4]),     # Right Back
        5: np.array([-6, -5]),     # Left Mid Defensive
        6: np.array([-7, 0]),      # Center Mid Defensive
        7: np.array([-6, 5]),      # Right Mid Defensive
        8: np.array([-3, -3]),     # Forward trying to track back
        9: np.array([-4, 0]),      # Forward trying to track back
        10: np.array([-3, 3]),     # Forward trying to track back
        11: np.array([-1, 0])      # Cherry picker tracks back slightly
    }
    
    # --- Simple Marking Logic (Optional Enhancement) ---
    # Could add logic here to adjust defender positions (2,3,4) 
    # to be closer to the nearest opponents if desired.
    # For now, just return the static defensive shell.
    # Example: Find 3 closest opponents and assign defenders 2, 3, 4 to shadow them.
    # Requires more complex assignment logic.

    return defense_positions

# --- Keep GenerateBasicFormation if other parts of the code still use it ---
# Or remove if GeneratePlayOn fully replaces it.
def GenerateBasicFormation():
     """ Original basic formation - keep for reference or if needed elsewhere"""
     return { 
        1: np.array([-13, 0]), 
        2: np.array([-7, -2]), 
        3: np.array([0, 3]), 
        4: np.array([7, 1]), 
        5: np.array([12, 0]) 
    }
