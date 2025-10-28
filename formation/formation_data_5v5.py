# formation/formation_data_5v5.py

"""
Adapted formation data for 5v5 based on helios-base normal-formation.conf.
Player 4 is now mapped to Helios Role 11 (Center Striker) instead of Role 6 (Center Midfield).
This data provides reference points for triangulation-based positioning.
"""

FORMATION_DATA = {
    "method": "ManualTriangulation",
    "roles": {
        # Maps your player unum (1-5) to the role index from helios-base (1-11)
        1: 1,  # Goalie
        2: 2,  # Left Defender (originally CenterBack Left)
        3: 3,  # Right Defender (originally CenterBack Right)
        # ***** ROLE MAPPING UPDATED *****
        4: 11, # Center Striker (originally CenterForward)
        # ***** END UPDATE *****
        5: 11, # Center Attacker (originally CenterForward) - NOTE: Player 5 is ALSO striker
    },
    "data": [
        # --- Extracted and adapted data points ---
        # --- COORDINATES FOR ROLE 11 (Player 4's new role) ARE NOW USED ---
        {
            "ball" : { "x" :  54.50, "y" : -36.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -0.72, "y" : -12.00 }, # Role 2
                "3" : { "x" :  -0.84, "y" :   1.08 }, # Role 3
                # Player 4 now uses Role 11 coords
                "11" : { "x" :  46.28, "y" : -14.00 }, # Role 11 Coordinates
                # Player 5 also uses Role 11 coords
                # "11" : { "x" :  46.28, "y" : -14.00 } # Role 11 (Same coordinates for Player 5)
            }
        },
        {
            "ball" : { "x" :  54.50, "y" :  36.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -0.84, "y" :  -1.08 }, # Role 2
                "3" : { "x" :  -0.72, "y" :  12.00 }, # Role 3
                "11" : { "x" :  46.28, "y" :  14.00 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :   0.00, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -15.53, "y" :  -5.42 }, # Role 2
                "3" : { "x" : -15.53, "y" :   5.42 }, # Role 3
                "11" : { "x" :   9.41, "y" :  -3.12 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  54.50, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   2.74, "y" :  -6.07 }, # Role 2
                "3" : { "x" :   2.74, "y" :   6.07 }, # Role 3
                "11" : { "x" :  45.60, "y" :  -1.65 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  36.57, "y" : -12.09 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -1.25, "y" :  -9.96 }, # Role 2
                "3" : { "x" :   0.52, "y" :   3.20 }, # Role 3
                "11" : { "x" :  38.10, "y" :  -8.45 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  36.57, "y" :  12.09 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   0.52, "y" :  -3.20 }, # Role 2
                "3" : { "x" :  -1.25, "y" :   9.96 }, # Role 3
                "11" : { "x" :  38.10, "y" :   8.45 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  48.51, "y" : -15.92 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   0.51, "y" : -10.77 }, # Role 2
                "3" : { "x" :   3.07, "y" :   3.38 }, # Role 3
                "11" : { "x" :  43.86, "y" :  -8.86 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  48.51, "y" :  15.92 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   3.07, "y" :  -3.38 }, # Role 2
                "3" : { "x" :   0.51, "y" :  10.77 }, # Role 3
                "11" : { "x" :  43.86, "y" :   8.86 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  42.76, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   0.98, "y" :  -5.97 }, # Role 2
                "3" : { "x" :   0.98, "y" :   5.97 }, # Role 3
                "11" : { "x" :  40.72, "y" :  -2.36 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  48.66, "y" :  -5.01 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   1.54, "y" :  -7.25 }, # Role 2
                "3" : { "x" :   2.33, "y" :   5.02 }, # Role 3
                "11" : { "x" :  43.57, "y" :  -4.31 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  48.66, "y" :   5.01 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   2.33, "y" :  -5.02 }, # Role 2
                "3" : { "x" :   1.54, "y" :   7.25 }, # Role 3
                "11" : { "x" :  43.57, "y" :   4.31 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  50.57, "y" :  -6.78 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   1.66, "y" :  -7.71 }, # Role 2
                "3" : { "x" :   2.75, "y" :   4.77 }, # Role 3
                "11" : { "x" :  44.40, "y" :  -4.93 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  50.57, "y" :   6.78 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   2.75, "y" :  -4.77 }, # Role 2
                "3" : { "x" :   1.66, "y" :   7.71 }, # Role 3
                "11" : { "x" :  44.40, "y" :   4.93 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  52.49, "y" : -17.10 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   0.95, "y" : -10.96 }, # Role 2
                "3" : { "x" :   3.74, "y" :   3.50 }, # Role 3
                "11" : { "x" :  45.39, "y" :  -8.87 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  52.49, "y" :  17.10 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   3.74, "y" :  -3.50 }, # Role 2
                "3" : { "x" :   0.95, "y" :  10.96 }, # Role 3
                "11" : { "x" :  45.39, "y" :   8.87 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  52.49, "y" :  -7.96 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   1.82, "y" :  -7.99 }, # Role 2
                "3" : { "x" :   3.10, "y" :   4.66 }, # Role 3
                "11" : { "x" :  45.16, "y" :  -5.26 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  52.49, "y" :   7.96 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   3.10, "y" :  -4.66 }, # Role 2
                "3" : { "x" :   1.82, "y" :   7.99 }, # Role 3
                "11" : { "x" :  45.16, "y" :   5.26 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  49.25, "y" :  -9.29 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   1.25, "y" :  -8.48 }, # Role 2
                "3" : { "x" :   2.73, "y" :   4.33 }, # Role 3
                "11" : { "x" :  43.96, "y" :  -6.11 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  49.25, "y" :   9.29 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   2.73, "y" :  -4.33 }, # Role 2
                "3" : { "x" :   1.25, "y" :   8.48 }, # Role 3
                "11" : { "x" :  43.96, "y" :   6.11 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  46.74, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   1.62, "y" :  -6.08 }, # Role 2
                "3" : { "x" :   1.62, "y" :   6.08 }, # Role 3
                "11" : { "x" :  42.56, "y" :  -2.13 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  42.61, "y" :  -5.60 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   0.50, "y" :  -7.52 }, # Role 2
                "3" : { "x" :   1.36, "y" :   4.72 }, # Role 3
                "11" : { "x" :  40.91, "y" :  -5.04 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  42.61, "y" :   5.60 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   1.36, "y" :  -4.72 }, # Role 2
                "3" : { "x" :   0.50, "y" :   7.52 }, # Role 3
                "11" : { "x" :  40.91, "y" :   5.04 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  45.86, "y" :  -3.54 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   1.23, "y" :  -6.89 }, # Role 2
                "3" : { "x" :   1.78, "y" :   5.23 }, # Role 3
                "11" : { "x" :  42.32, "y" :  -3.85 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  45.86, "y" :   3.54 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   1.78, "y" :  -5.23 }, # Role 2
                "3" : { "x" :   1.23, "y" :   6.89 }, # Role 3
                "11" : { "x" :  42.32, "y" :   3.85 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  46.89, "y" :  -6.49 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   1.14, "y" :  -7.70 }, # Role 2
                "3" : { "x" :   2.17, "y" :   4.70 }, # Role 3
                "11" : { "x" :  42.89, "y" :  -5.11 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  46.89, "y" :   6.49 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   2.17, "y" :  -4.70 }, # Role 2
                "3" : { "x" :   1.14, "y" :   7.70 }, # Role 3
                "11" : { "x" :  42.89, "y" :   5.11 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  38.63, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :   0.18, "y" :  -5.93 }, # Role 2
                "3" : { "x" :   0.18, "y" :   5.93 }, # Role 3
                "11" : { "x" :  38.61, "y" :  -2.57 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  39.22, "y" :  -5.75 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -0.15, "y" :  -7.62 }, # Role 2
                "3" : { "x" :   0.71, "y" :   4.57 }, # Role 3
                "11" : { "x" :  39.22, "y" :  -5.35 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  39.22, "y" :   5.75 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   0.71, "y" :  -4.57 }, # Role 2
                "3" : { "x" :  -0.15, "y" :   7.62 }, # Role 3
                "11" : { "x" :  39.22, "y" :   5.35 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  30.37, "y" : -15.92 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -3.06, "y" : -11.84 }, # Role 2
                "3" : { "x" :  -0.92, "y" :   2.05 }, # Role 3
                "11" : { "x" :  34.70, "y" : -10.66 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  30.37, "y" :  15.92 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -0.92, "y" :  -2.05 }, # Role 2
                "3" : { "x" :  -3.06, "y" :  11.84 }, # Role 3
                "11" : { "x" :  34.70, "y" :  10.66 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :   0.00, "y" : -36.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -17.18, "y" : -19.96 }, # Role 2
                "3" : { "x" : -16.68, "y" :  -6.05 }, # Role 3
                "11" : { "x" :  14.62, "y" : -20.60 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :   0.00, "y" :  36.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -16.68, "y" :   6.05 }, # Role 2
                "3" : { "x" : -17.18, "y" :  19.96 }, # Role 3
                "11" : { "x" :  14.62, "y" :  20.60 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  44.53, "y" : -22.41 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -0.79, "y" : -13.56 }, # Role 2
                "3" : { "x" :   2.77, "y" :   2.31 }, # Role 3
                "11" : { "x" :  42.36, "y" : -11.75 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  44.53, "y" :  22.41 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   2.77, "y" :  -2.31 }, # Role 2
                "3" : { "x" :  -0.79, "y" :  13.56 }, # Role 3
                "11" : { "x" :  42.36, "y" :  11.75 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  44.09, "y" : -29.78 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -1.70, "y" : -16.43 }, # Role 2
                "3" : { "x" :   3.08, "y" :   1.45 }, # Role 3
                "11" : { "x" :  42.31, "y" : -14.34 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  44.09, "y" :  29.78 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   3.08, "y" :  -1.45 }, # Role 2
                "3" : { "x" :  -1.70, "y" :  16.43 }, # Role 3
                "11" : { "x" :  42.31, "y" :  14.34 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  29.19, "y" : -34.36 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -5.36, "y" : -18.80 }, # Role 2
                "3" : { "x" :  -0.74, "y" :  -0.94 }, # Role 3
                "11" : { "x" :  34.81, "y" : -17.65 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  29.19, "y" :  34.36 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -0.74, "y" :   0.94 }, # Role 2
                "3" : { "x" :  -5.36, "y" :  18.80 }, # Role 3
                "11" : { "x" :  34.81, "y" :  17.65 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  33.03, "y" : -31.26 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -4.18, "y" : -17.73 }, # Role 2
                "3" : { "x" :   0.28, "y" :  -0.08 }, # Role 3
                "11" : { "x" :  36.65, "y" : -16.30 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  33.03, "y" :  31.26 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :   0.28, "y" :   0.08 }, # Role 2
                "3" : { "x" :  -4.18, "y" :  17.73 }, # Role 3
                "11" : { "x" :  36.65, "y" :  16.30 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  23.00, "y" :  -5.16 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -4.35, "y" :  -7.68 }, # Role 2
                "3" : { "x" :  -3.76, "y" :   4.10 }, # Role 3
                "11" : { "x" :  29.04, "y" :  -6.00 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  23.00, "y" :   5.16 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -3.76, "y" :  -4.10 }, # Role 2
                "3" : { "x" :  -4.35, "y" :   7.68 }, # Role 3
                "11" : { "x" :  29.04, "y" :   6.00 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  28.16, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -2.39, "y" :  -5.82 }, # Role 2
                "3" : { "x" :  -2.39, "y" :   5.82 }, # Role 3
                "11" : { "x" :  32.25, "y" :  -1.00 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  34.65, "y" :  -5.75 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -1.13, "y" :  -7.70 }, # Role 2
                "3" : { "x" :  -0.31, "y" :   4.40 }, # Role 3
                "11" : { "x" :  36.70, "y" :  -5.66 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  34.65, "y" :   5.75 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -0.31, "y" :  -4.40 }, # Role 2
                "3" : { "x" :  -1.13, "y" :   7.70 }, # Role 3
                "11" : { "x" :  36.70, "y" :   5.66 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  19.91, "y" : -28.60 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -7.44, "y" : -17.45 }, # Role 2
                "3" : { "x" :  -4.43, "y" :  -1.60 }, # Role 3
                "11" : { "x" :  28.57, "y" : -16.62 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  19.91, "y" :  28.60 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -4.43, "y" :   1.60 }, # Role 2
                "3" : { "x" :  -7.44, "y" :  17.45 }, # Role 3
                "11" : { "x" :  28.57, "y" :  16.62 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  14.30, "y" : -11.06 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -8.06, "y" : -10.45 }, # Role 2
                "3" : { "x" :  -7.15, "y" :   1.87 }, # Role 3
                "11" : { "x" :  22.95, "y" :  -9.41 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  14.30, "y" :  11.06 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -7.15, "y" :  -1.87 }, # Role 2
                "3" : { "x" :  -8.06, "y" :  10.45 }, # Role 3
                "11" : { "x" :  22.95, "y" :   9.41 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  11.35, "y" : -25.07 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -10.43, "y" : -16.57 }, # Role 2
                "3" : { "x" :  -8.68, "y" :  -1.89 }, # Role 3
                "11" : { "x" :  22.04, "y" : -15.92 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  11.35, "y" :  25.07 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -8.68, "y" :   1.89 }, # Role 2
                "3" : { "x" : -10.43, "y" :  16.57 }, # Role 3
                "11" : { "x" :  22.04, "y" :  15.92 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :   9.58, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -9.77, "y" :  -5.58 }, # Role 2
                "3" : { "x" :  -9.77, "y" :   5.58 }, # Role 3
                "11" : { "x" :  17.81, "y" :  -1.03 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  18.58, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -5.66, "y" :  -5.71 }, # Role 2
                "3" : { "x" :  -5.66, "y" :   5.71 }, # Role 3
                "11" : { "x" :  25.23, "y" :  -0.34 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :   3.83, "y" : -20.20 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -13.84, "y" : -14.96 }, # Role 2
                "3" : { "x" : -13.20, "y" :  -1.74 }, # Role 3
                "11" : { "x" :  15.55, "y" : -14.21 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :   3.83, "y" :  20.20 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -13.20, "y" :   1.74 }, # Role 2
                "3" : { "x" : -13.84, "y" :  14.96 }, # Role 3
                "11" : { "x" :  15.55, "y" :  14.21 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :   6.19, "y" : -10.32 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -11.99, "y" : -10.37 }, # Role 2
                "3" : { "x" : -11.54, "y" :   1.49 }, # Role 3
                "11" : { "x" :  16.23, "y" :  -9.25 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :   6.19, "y" :  10.32 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -11.54, "y" :  -1.49 }, # Role 2
                "3" : { "x" : -11.99, "y" :  10.37 }, # Role 3
                "11" : { "x" :  16.23, "y" :   9.25 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  10.47, "y" : -29.78 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -11.25, "y" : -18.18 }, # Role 2
                "3" : { "x" :  -9.28, "y" :  -3.00 }, # Role 3
                "11" : { "x" :  21.84, "y" : -17.79 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  10.47, "y" :  29.78 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -9.28, "y" :   3.00 }, # Role 2
                "3" : { "x" : -11.25, "y" :  18.18 }, # Role 3
                "11" : { "x" :  21.84, "y" :  17.79 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  13.27, "y" : -33.18 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -10.40, "y" : -19.06 }, # Role 2
                "3" : { "x" :  -7.76, "y" :  -3.20 }, # Role 3
                "11" : { "x" :  24.21, "y" : -18.79 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  13.27, "y" :  33.18 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -7.76, "y" :   3.20 }, # Role 2
                "3" : { "x" : -10.40, "y" :  19.06 }, # Role 3
                "11" : { "x" :  24.21, "y" :  18.79 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -16.96, "y" : -30.52 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -23.33, "y" : -18.45 }, # Role 2
                "3" : { "x" : -23.18, "y" :  -4.34 }, # Role 3
                "11" : { "x" :   0.06, "y" :  -9.81 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -16.96, "y" :  30.52 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -23.18, "y" :   4.34 }, # Role 2
                "3" : { "x" : -23.33, "y" :  18.45 }, # Role 3
                "11" : { "x" :   0.06, "y" :   9.81 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -4.28, "y" : -16.81 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -12.71, "y" : -15.79 }, # Role 2
                "3" : { "x" : -14.88, "y" :  -3.68 }, # Role 3
                "11" : { "x" :   5.59, "y" :  -8.48 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -4.28, "y" :  16.81 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -14.88, "y" :   3.68 }, # Role 2
                "3" : { "x" : -12.71, "y" :  15.79 }, # Role 3
                "11" : { "x" :   5.59, "y" :   8.48 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -7.08, "y" : -27.57 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -15.15, "y" : -19.34 }, # Role 2
                "3" : { "x" : -16.57, "y" :  -4.96 }, # Role 3
                "11" : { "x" :   6.91, "y" : -10.52 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -7.08, "y" :  27.57 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -16.57, "y" :   4.96 }, # Role 2
                "3" : { "x" : -15.15, "y" :  19.34 }, # Role 3
                "11" : { "x" :   6.91, "y" :  10.52 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -7.96, "y" : -31.41 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -15.89, "y" : -20.09 }, # Role 2
                "3" : { "x" : -17.14, "y" :  -5.03 }, # Role 3
                "11" : { "x" :   8.36, "y" : -10.67 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -7.96, "y" :  31.41 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -17.14, "y" :   5.03 }, # Role 2
                "3" : { "x" : -15.89, "y" :  20.09 }, # Role 3
                "11" : { "x" :   8.36, "y" :  10.67 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -23.89, "y" : -34.21 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -31.05, "y" : -17.31 }, # Role 2
                "3" : { "x" : -29.37, "y" :  -4.33 }, # Role 3
                "11" : { "x" :  -3.41, "y" :  -8.93 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -23.89, "y" :  34.21 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -29.37, "y" :   4.33 }, # Role 2
                "3" : { "x" : -31.05, "y" :  17.31 }, # Role 3
                "11" : { "x" :  -3.41, "y" :   8.93 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -54.50, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -47.53, "y" :  -3.17 }, # Role 2
                "3" : { "x" : -47.53, "y" :   3.17 }, # Role 3
                "11" : { "x" : -30.03, "y" :   4.57 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -19.61, "y" :  -5.46 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -26.74, "y" :  -7.22 }, # Role 2
                "3" : { "x" : -27.37, "y" :   1.07 }, # Role 3
                "11" : { "x" :  -8.99, "y" :  -3.01 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -19.61, "y" :   5.46 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -27.37, "y" :  -1.07 }, # Role 2
                "3" : { "x" : -26.74, "y" :   7.22 }, # Role 3
                "11" : { "x" :  -8.99, "y" :   3.01 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -7.96, "y" :  -7.37 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -15.64, "y" :  -9.85 }, # Role 2
                "3" : { "x" : -17.18, "y" :   0.07 }, # Role 3
                "11" : { "x" :   0.76, "y" :  -4.50 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -7.96, "y" :   7.37 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -17.18, "y" :  -0.07 }, # Role 2
                "3" : { "x" : -15.64, "y" :   9.85 }, # Role 3
                "11" : { "x" :   0.76, "y" :   4.50 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -5.31, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -14.82, "y" :  -4.50 }, # Role 2
                "3" : { "x" : -14.82, "y" :   4.50 }, # Role 3
                "11" : { "x" :   2.20, "y" :  -0.09 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -2.06, "y" : -11.35 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -11.37, "y" : -12.91 }, # Role 2
                "3" : { "x" : -13.56, "y" :  -2.16 }, # Role 3
                "11" : { "x" :   6.06, "y" :  -6.47 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -2.06, "y" :  11.35 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -13.56, "y" :   2.16 }, # Role 2
                "3" : { "x" : -11.37, "y" :  12.91 }, # Role 3
                "11" : { "x" :   6.06, "y" :   6.47 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -3.39, "y" :  -5.90 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -12.70, "y" :  -8.99 }, # Role 2
                "3" : { "x" : -14.14, "y" :   0.58 }, # Role 3
                "11" : { "x" :   4.70, "y" :  -3.75 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -3.39, "y" :   5.90 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -14.14, "y" :  -0.58 }, # Role 2
                "3" : { "x" : -12.70, "y" :   8.99 }, # Role 3
                "11" : { "x" :   4.70, "y" :   3.75 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -9.44, "y" : -24.77 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -16.56, "y" : -18.28 }, # Role 2
                "3" : { "x" : -17.92, "y" :  -4.50 }, # Role 3
                "11" : { "x" :   3.59, "y" : -10.02 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  -9.44, "y" :  24.77 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -17.92, "y" :   4.50 }, # Role 2
                "3" : { "x" : -16.56, "y" :  18.28 }, # Role 3
                "11" : { "x" :   3.59, "y" :  10.02 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -12.39, "y" : -12.39 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -18.61, "y" : -12.64 }, # Role 2
                "3" : { "x" : -20.37, "y" :  -1.72 }, # Role 3
                "11" : { "x" :  -2.10, "y" :  -6.61 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -12.39, "y" :  12.39 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -20.37, "y" :   1.72 }, # Role 2
                "3" : { "x" : -18.61, "y" :  12.64 }, # Role 3
                "11" : { "x" :  -2.10, "y" :   6.61 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -16.37, "y" : -15.78 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -22.13, "y" : -13.78 }, # Role 2
                "3" : { "x" : -23.54, "y" :  -2.52 }, # Role 3
                "11" : { "x" :  -4.48, "y" :  -7.55 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -16.37, "y" :  15.78 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -23.54, "y" :   2.52 }, # Role 2
                "3" : { "x" : -22.13, "y" :  13.78 }, # Role 3
                "11" : { "x" :  -4.48, "y" :   7.55 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -19.91, "y" : -18.28 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -25.82, "y" : -14.13 }, # Role 2
                "3" : { "x" : -26.70, "y" :  -3.02 }, # Role 3
                "11" : { "x" :  -6.47, "y" :  -7.96 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -19.91, "y" :  18.28 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -26.70, "y" :   3.02 }, # Role 2
                "3" : { "x" : -25.82, "y" :  14.13 }, # Role 3
                "11" : { "x" :  -6.47, "y" :   7.96 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -32.73, "y" : -29.19 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -39.69, "y" : -13.44 }, # Role 2
                "3" : { "x" : -38.23, "y" :  -4.58 }, # Role 3
                "11" : { "x" : -12.00, "y" :  -7.92 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -32.73, "y" :  29.19 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -38.23, "y" :   4.58 }, # Role 2
                "3" : { "x" : -39.69, "y" :  13.44 }, # Role 3
                "11" : { "x" : -12.00, "y" :   7.92 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -24.03, "y" : -17.55 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -30.55, "y" : -12.75 }, # Role 2
                "3" : { "x" : -31.07, "y" :  -2.95 }, # Role 3
                "11" : { "x" :  -9.46, "y" :  -7.39 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -24.03, "y" :  17.55 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -31.07, "y" :   2.95 }, # Role 2
                "3" : { "x" : -30.55, "y" :  12.75 }, # Role 3
                "11" : { "x" :  -9.46, "y" :   7.39 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -31.26, "y" :   0.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -39.65, "y" :  -2.16 }, # Role 2
                "3" : { "x" : -39.65, "y" :   2.16 }, # Role 3
                "11" : { "x" : -18.33, "y" :   1.17 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -29.34, "y" : -15.33 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -36.56, "y" : -10.26 }, # Role 2
                "3" : { "x" : -36.79, "y" :  -2.72 }, # Role 3
                "11" : { "x" : -13.30, "y" :  -6.21 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -29.34, "y" :  15.33 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -36.79, "y" :   2.72 }, # Role 2
                "3" : { "x" : -36.56, "y" :  10.26 }, # Role 3
                "11" : { "x" : -13.30, "y" :   6.21 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -37.01, "y" : -33.03 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -42.77, "y" : -12.81 }, # Role 2
                "3" : { "x" : -40.82, "y" :  -4.62 }, # Role 3
                "11" : { "x" : -13.43, "y" :  -7.26 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -37.01, "y" :  33.03 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -40.82, "y" :   4.62 }, # Role 2
                "3" : { "x" : -42.77, "y" :  12.81 }, # Role 3
                "11" : { "x" : -13.43, "y" :   7.26 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -54.50, "y" : -36.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -46.24, "y" : -10.29 }, # Role 2
                "3" : { "x" : -44.48, "y" :  -1.69 }, # Role 3
                "11" : { "x" : -22.80, "y" :  -4.37 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -54.50, "y" :  36.00 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -44.48, "y" :   1.69 }, # Role 2
                "3" : { "x" : -46.24, "y" :  10.29 }, # Role 3
                "11" : { "x" : -22.80, "y" :   4.37 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -48.66, "y" : -22.71 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -46.06, "y" :  -8.98 }, # Role 2
                "3" : { "x" : -45.54, "y" :  -2.25 }, # Role 3
                "11" : { "x" : -22.29, "y" :  -5.05 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -48.66, "y" :  22.71 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -45.54, "y" :   2.25 }, # Role 2
                "3" : { "x" : -46.06, "y" :   8.98 }, # Role 3
                "11" : { "x" : -22.29, "y" :   5.05 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -39.52, "y" : -28.16 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -43.82, "y" : -11.32 }, # Role 2
                "3" : { "x" : -42.60, "y" :  -4.34 }, # Role 3
                "11" : { "x" : -16.44, "y" :  -6.95 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -39.52, "y" :  28.16 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -42.60, "y" :   4.34 }, # Role 2
                "3" : { "x" : -43.82, "y" :  11.32 }, # Role 3
                "11" : { "x" : -16.44, "y" :   6.95 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -39.22, "y" : -22.12 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -43.64, "y" : -10.02 }, # Role 2
                "3" : { "x" : -43.11, "y" :  -3.81 }, # Role 3
                "11" : { "x" : -17.55, "y" :  -6.43 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -39.22, "y" :  22.12 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -43.11, "y" :   3.81 }, # Role 2
                "3" : { "x" : -43.64, "y" :  10.02 }, # Role 3
                "11" : { "x" : -17.55, "y" :   6.43 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -41.58, "y" :  -7.22 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -45.59, "y" :  -4.05 }, # Role 2
                "3" : { "x" : -45.51, "y" :  -0.60 }, # Role 3
                "11" : { "x" : -21.98, "y" :  -1.47 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -41.58, "y" :   7.22 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -45.51, "y" :   0.60 }, # Role 2
                "3" : { "x" : -45.59, "y" :   4.05 }, # Role 3
                "11" : { "x" : -21.98, "y" :   1.47 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -34.06, "y" :  -7.37 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -41.55, "y" :  -5.15 }, # Role 2
                "3" : { "x" : -41.60, "y" :  -0.80 }, # Role 3
                "11" : { "x" : -17.91, "y" :  -2.58 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -34.06, "y" :   7.37 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -41.60, "y" :   0.80 }, # Role 2
                "3" : { "x" : -41.55, "y" :   5.15 }, # Role 3
                "11" : { "x" : -17.91, "y" :   2.58 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -48.22, "y" :  -9.88 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" : -46.90, "y" :  -4.98 }, # Role 2
                "3" : { "x" : -46.74, "y" :  -0.12 }, # Role 3
                "11" : { "x" : -24.49, "y" :  -1.57 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" : -48.22, "y" :   9.88 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" : -46.74, "y" :   0.12 }, # Role 2
                "3" : { "x" : -46.90, "y" :   4.98 }, # Role 3
                "11" : { "x" : -24.49, "y" :   1.57 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  15.33, "y" : -21.38 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :   0.00 }, # Role 1
                "2" : { "x" :  -8.43, "y" : -14.97 }, # Role 2
                "3" : { "x" :  -6.57, "y" :  -0.58 }, # Role 3
                "11" : { "x" :  24.72, "y" : -14.15 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        },
        {
            "ball" : { "x" :  15.33, "y" :  21.38 },
            "positions" : {
                "1" : { "x" : -50.00, "y" :  -0.00 }, # Role 1
                "2" : { "x" :  -6.57, "y" :   0.58 }, # Role 2
                "3" : { "x" :  -8.43, "y" :  14.97 }, # Role 3
                "11" : { "x" :  24.72, "y" :  14.15 }, # Role 11 Coordinates (for Player 4 & 5)
            }
        }
    ]
}