import math
import numpy as np
from math_ops.Math_Ops import Math_Ops as M

class Strategy():
    def __init__(self, world):
        self.play_mode = world.play_mode
        self.robot_model = world.robot
        self.player_unum = self.robot_model.unum

        # --- SUPER-SAFE FALLBACKS ---

        # Fix 1: Head position can be None
        if self.robot_model.loc_head_position is not None:
            self.my_head_pos_2d = self.robot_model.loc_head_position[:2]
        else:
            self.my_head_pos_2d = (0.0, 0.0) # Safe fallback

        # Fix 2: My position can be None
        my_state = world.teammates[self.player_unum-1].state_abs_pos
        if my_state is not None:
            self.mypos = (my_state[0], my_state[1])
        else:
            self.mypos = (0.0, 0.0) # Safe fallback

        # Fix 3: Ball position can be None
        if world.ball_abs_pos is not None:
             self.ball_2d = world.ball_abs_pos[:2]
        else:
             self.ball_2d = (0.0, 0.0) # Safe fallback

        # Fix 4: Ball velocity can be None
        ball_vel = world.get_ball_abs_vel(6)
        if ball_vel is not None:
            self.ball_speed = np.linalg.norm(ball_vel[:2])
        else:
            self.ball_speed = 0.0 # Safe fallback

        # --- END OF SUPER-SAFE FALLBACKS ---

        self.side = 1
        if world.team_side_is_left:
            self.side = 0

        # Create teammate/opponent position lists, handling None
        self.teammate_positions = [teammate.state_abs_pos[:2] if teammate.state_abs_pos is not None and not teammate.state_fallen
                                       else None
                                       for teammate in world.teammates
                                       ]
        self.opponent_positions = [opponent.state_abs_pos[:2] if opponent.state_abs_pos is not None and not opponent.state_fallen
                                       else None
                                       for opponent in world.opponents
                                       ]

        # Initialize other variables
        self.team_dist_to_ball = None
        self.team_dist_to_oppGoal = None
        self.opp_dist_to_ball = None
        self.prev_important_positions_and_values = None
        self.curr_important_positions_and_values = None
        self.point_preferences = None
        self.combined_threat_and_definedPositions = None

        # Orientation and ball vector calculations (now using safe variables)
        self.my_ori = self.robot_model.imu_torso_orientation # Usually safe
        self.ball_vec = np.array(self.ball_2d) - np.array(self.my_head_pos_2d) # Use np.array for safety
        self.ball_dir = M.vector_angle(self.ball_vec)
        self.ball_dist = np.linalg.norm(self.ball_vec)
        self.ball_sq_dist = self.ball_dist * self.ball_dist

        # Goal direction
        self.goal_dir = M.target_abs_angle(self.ball_2d,(15.05,0))

        # Play mode group
        self.PM_GROUP = world.play_mode_group

        # Predicted ball position
        self.slow_ball_pos = world.get_predicted_ball_pos(0.5)
        # Handle case where prediction might fail (return None)
        if self.slow_ball_pos is None:
            self.slow_ball_pos = self.ball_2d # Fallback to current ball pos

        # Calculate distances to ball (using safe positions)
        self.teammates_ball_sq_dist = [np.sum((np.array(p.state_abs_pos[:2]) - np.array(self.slow_ball_pos)) ** 2)
                                      if p.state_abs_pos is not None and \
                                      p.state_last_update != 0 and (world.time_local_ms - p.state_last_update <= 360 or p.is_self) and not p.state_fallen
                                      else 1000
                                      for p in world.teammates ]

        self.opponents_ball_sq_dist = [np.sum((np.array(p.state_abs_pos[:2]) - np.array(self.slow_ball_pos)) ** 2)
                                      if p.state_abs_pos is not None and \
                                      p.state_last_update != 0 and world.time_local_ms - p.state_last_update <= 360 and not p.state_fallen
                                      else 1000
                                      for p in world.opponents ]

        # Add fallbacks for empty distance lists (e.g., at very start)
        if not self.teammates_ball_sq_dist:
             self.teammates_ball_sq_dist = [1000] * len(world.teammates) # Ensure list has correct length
        if not self.opponents_ball_sq_dist:
             self.opponents_ball_sq_dist = [1000] * len(world.opponents)

        # Calculate minimum distances safely
        self.min_teammate_ball_sq_dist = min(self.teammates_ball_sq_dist) if self.teammates_ball_sq_dist else 1000
        self.min_teammate_ball_dist = math.sqrt(self.min_teammate_ball_sq_dist)

        sorted_teammate_ball_sq_dist = sorted(self.teammates_ball_sq_dist)
        self.second_min_teammate_ball_sq_dist = sorted_teammate_ball_sq_dist[1] if len(sorted_teammate_ball_sq_dist) > 1 else self.min_teammate_ball_sq_dist

        self.min_opponent_ball_dist = math.sqrt(min(self.opponents_ball_sq_dist)) if self.opponents_ball_sq_dist else float('inf')

        # Find active player safely
        try:
            # Ensure min_teammate_ball_sq_dist is actually in the list before finding index
            if self.min_teammate_ball_sq_dist in self.teammates_ball_sq_dist:
                 self.active_player_unum = self.teammates_ball_sq_dist.index(self.min_teammate_ball_sq_dist) + 1
            else:
                 self.active_player_unum = 1 # Failsafe if min wasn't found (shouldn't happen)
        except ValueError:
            self.active_player_unum = 1 # Failsafe

        # Desired position/orientation initialization
        self.my_desired_position = self.mypos
        self.my_desired_orientation = self.ball_dir

        # --- START OF ADDED CODE FROM AMAAN ---
        self.goal_position = (15.5, 0.0)
        self.goal_tolerance = 0.25

        # Potential Fields parameters
        self.goal_attraction_coefficient = 5.0
        self.obstacle_repulsion_coefficient = 100.0
        self.obstacle_effect_radius = 1.0
        self.damping_coefficient = 0.3
        self.previous_force = np.zeros(2)

        self.formation_tiers = {"back": -10, "mid": 0, "forward": 10}

        self.defensive_bound_x = -10
        self.goal_shoot_margin = 0.2
        # --- END OF ADDED CODE FROM AMAAN ---

    # --- OTHER FUNCTIONS (UNCHANGED FROM YOUR VERSION) ---
    def GenerateTeamToTargetDistanceArray(self, target, world):
        for teammate in world.teammates:
            pass

    def IsFormationReady(self, point_preferences):
        is_formation_ready = True
        num_players = len(self.teammate_positions)

        for i in range(1, num_players + 1):
            if i != self.active_player_unum:
                # Use index i-1 for 0-based list
                if i-1 < len(self.teammate_positions):
                    teammate_pos = self.teammate_positions[i-1]
                    # Check if teammate_pos is valid before calculation
                    if teammate_pos is not None and not np.array_equal(teammate_pos, np.array([-100.0,-100.0])):
                        if i in point_preferences:
                            # Ensure preference is also a valid point
                            pref_pos = point_preferences[i]
                            if pref_pos is not None and not np.array_equal(pref_pos, np.array([-100.0,-100.0])):
                                distance_sq = np.sum((np.array(teammate_pos) - np.array(pref_pos)) ** 2)
                                # Increased tolerance slightly
                                if(distance_sq > 0.5**2): # Compare squared distance
                                    is_formation_ready = False
                        # else: # Player not assigned, might be intended for 5v5
                            # is_formation_ready = False
                # else: # Index out of bounds, means not ready
                    # is_formation_ready = False
        return is_formation_ready


    def GetDirectionRelativeToMyPositionAndTarget(self,target):
        # Ensure target is valid
        if target is None: return 0.0 # Default orientation if target is invalid
        target_vec = np.array(target) - np.array(self.my_head_pos_2d)
        target_dir = M.vector_angle(target_vec)
        return target_dir

    # --- START OF HELPER FUNCTIONS FROM AMAAN (UNCHANGED) ---
    def potential_fields_pathfinding(self, start_pos, goal_pos=None):
        if goal_pos is None:
            goal_pos = self.goal_position
        attraction_force = self.calculate_attraction(start_pos, goal_pos)
        repulsion_force = self.calculate_repulsion(start_pos)
        boundary_correction = self.apply_boundary_correction(start_pos)
        resulting_force = attraction_force + repulsion_force + boundary_correction + self.central_field_correction(start_pos) - self.damping_coefficient * self.previous_force
        self.previous_force = resulting_force
        next_position = np.array(start_pos) + resulting_force # Ensure numpy array math
        return (next_position[0], next_position[1])

    def calculate_attraction(self, current_pos, goal_pos):
        direction_to_goal = np.array(goal_pos) - np.array(current_pos)
        distance_to_goal = np.linalg.norm(direction_to_goal)
        decay_factor = 1 - np.exp(-0.1 * distance_to_goal)
        if distance_to_goal > 0:
            direction_to_goal = direction_to_goal / distance_to_goal
        else:
            direction_to_goal = np.zeros_like(direction_to_goal)
        boundary_proximity_boost = 1.5 if np.linalg.norm(self.apply_boundary_correction(current_pos)) > 0.5 else 1.0
        attraction_multiplier = 1.0 if self.ball_dist > 0.5 else 1.5
        attraction_force = self.goal_attraction_coefficient * direction_to_goal * decay_factor * attraction_multiplier * boundary_proximity_boost
        return attraction_force

    def calculate_repulsion(self, current_pos):
        total_repulsion = np.zeros(2)
        for opponent_pos in self.opponent_positions:
            if opponent_pos is not None: # Check for None
                 # Ensure numpy array math
                direction_from_obstacle = np.array(current_pos) - np.array(opponent_pos)
                distance_to_obstacle = np.linalg.norm(direction_from_obstacle)
                if distance_to_obstacle < self.obstacle_effect_radius:
                    if distance_to_obstacle > 0:
                        direction_from_obstacle /= distance_to_obstacle
                    variable_repulsion = (self.obstacle_repulsion_coefficient / (distance_to_obstacle ** 2 + 0.1)) \
                                         * (0.8 if self.ball_dist < 0.5 else 1.0)
                    repulsion_force = variable_repulsion * direction_from_obstacle
                    total_repulsion += repulsion_force
        return total_repulsion

    def apply_boundary_correction(self, current_pos):
        correction_force = np.zeros(2)
        if abs(current_pos[0]) > 13:
            distance_to_boundary_x = 15 - abs(current_pos[0])
            correction_force[0] = -1.0 / (distance_to_boundary_x + 0.1) * np.sign(current_pos[0])
        if abs(current_pos[1]) > 8:
            distance_to_boundary_y = 10 - abs(current_pos[1])
            correction_force[1] = -1.0 / (distance_to_boundary_y + 0.1) * np.sign(current_pos[1])
        return correction_force

    def central_field_correction(self, current_pos):
        center_of_field = np.array([0, 0])
        direction_to_center = center_of_field - np.array(current_pos)
        norm = np.linalg.norm(direction_to_center)
        if norm == 0:
            return np.zeros(2)
        central_attraction_force = 0.05 * direction_to_center / norm
        return central_attraction_force

    def distance(self, point1, point2):
        # Add checks for None
        if point1 is None or point2 is None: return float('inf')
        return np.linalg.norm(np.array(point1) - np.array(point2))

    def calculate_orientation(self, target_pos, my_pos):
        # Add checks for None
        if target_pos is None or my_pos is None: return 0.0
        current_orientation = self.my_ori
        target_vec = np.array(target_pos) - np.array(my_pos)
        orientation_radians = np.arctan2(target_vec[1], target_vec[0])
        orientation_degrees = np.degrees(orientation_radians)
        relative_orientation = orientation_degrees
        return relative_orientation

    def are_points_collinear(self, position, ball_pos, goal, tolerance=0.45):
        # Add checks for None
        if position is None or ball_pos is None or goal is None: return False
        x1, y1 = position
        x2, y2 = ball_pos
        x3, y3 = goal
        if abs(x2 - x1) < 1e-6 and abs(x3 - x2) < 1e-6:
             return True
        if abs(x2 - x1) < 1e-6 or abs(x3 - x2) < 1e-6:
             return False
        # Add check for division by zero
        if (x2 - x1) == 0 or (x3 - x2) == 0: return False
        slope1 = (y2 - y1) / (x2 - x1)
        slope2 = (y3 - y2) / (x3 - x2)
        return abs(slope1 - slope2) < tolerance

    def point_in_direction(self, position, goal, distance=0.2):
         # Add checks for None
        if position is None or goal is None: return position # Return original if invalid input
        x1, y1 = position
        x2, y2 = goal
        direction_x = x2 - x1
        direction_y = y2 - y1
        magnitude = math.sqrt(direction_x**2 + direction_y**2)
        if magnitude == 0:
            return position
        unit_direction_x = direction_x / magnitude
        unit_direction_y = direction_y / magnitude
        scaled_x = unit_direction_x * distance
        scaled_y = unit_direction_y * distance
        new_position = (x1 + scaled_x, y1 + scaled_y)
        return new_position

    def next_position_to_startat(self, target, ball, myposition, startat, buffer_distance=0.4, angle_threshold=78):
         # Add checks for None
        if target is None or ball is None or myposition is None or startat is None: return startat
        target = np.array(target)
        ball = np.array(ball)
        myposition = np.array(myposition)
        startat = np.array(startat)
        target_to_ball = ball - target
        ball_to_myposition = myposition - ball
        norm_target_to_ball = np.linalg.norm(target_to_ball)
        norm_ball_to_mypos = np.linalg.norm(ball_to_myposition)
        if norm_target_to_ball == 0 or norm_ball_to_mypos == 0:
            return tuple(startat)
        dot_product = np.dot(target_to_ball, ball_to_myposition)
        magnitude_product = norm_target_to_ball * norm_ball_to_mypos
        # Add check for division by zero
        if magnitude_product == 0: return tuple(startat)
        cos_angle = np.clip(dot_product / magnitude_product, -1.0, 1.0)
        angle_degrees = np.degrees(np.arccos(cos_angle))
        if abs(angle_degrees) < angle_threshold:
             # Add check for division by zero
            if norm_target_to_ball == 0: return tuple(startat)
            perpendicular_direction = np.array([-target_to_ball[1], target_to_ball[0]]) / norm_target_to_ball
            left_of_ball = ball + perpendicular_direction * buffer_distance
            right_of_ball = ball - perpendicular_direction * buffer_distance
            distances = {
                "left": np.linalg.norm(myposition - left_of_ball),
                "right": np.linalg.norm(myposition - right_of_ball),
                "startat": np.linalg.norm(myposition - startat)
            }
            closest_point = min(distances, key=distances.get)
            if closest_point == "left":
                return tuple(left_of_ball)
            elif closest_point == "right":
                return tuple(right_of_ball)
            else:
                return tuple(startat)
        else:
            return tuple(startat)

    def get_player_ahead(self, position):
         # Add check for None
        if position is None: return None
        ind = None
        distance = float('inf')
        num_players = len(self.teammate_positions)
        for i in range(num_players):
            # Check for None before accessing index
            if self.teammate_positions[i] is not None and self.teammate_positions[i][0] > position[0] + 1.5:
                current_distance = self.distance(self.teammate_positions[i], position)
                if current_distance < distance and distance > 2:
                    ind = i
                    distance = current_distance
        # Check index validity before returning
        return self.teammate_positions[ind] if ind is not None and ind < len(self.teammate_positions) else position

    # --- END OF HELPER FUNCTIONS FROM AMAAN ---