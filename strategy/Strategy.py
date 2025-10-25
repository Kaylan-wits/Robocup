import math
import numpy as np
from math_ops.Math_Ops import Math_Ops as M

class Strategy():
    def __init__(self, world):
        self.world = world # Store world object for easier access
        self.play_mode = world.play_mode
        self.robot_model = world.robot  
        self.my_head_pos_2d = self.robot_model.loc_head_position[:2]
        self.player_unum = self.robot_model.unum
        # Ensure mypos is a numpy array for vector math
        self.mypos = np.array(world.teammates[self.player_unum-1].state_abs_pos[:2]) if world.teammates[self.player_unum-1].state_abs_pos is not None else np.array([0.0, 0.0])
       
        self.side = 1
        if world.team_side_is_left:
            self.side = 0

        # Store positions as numpy arrays where possible
        self.teammate_positions = [np.array(teammate.state_abs_pos[:2]) if teammate.state_abs_pos is not None 
                                    else None
                                    for teammate in world.teammates
                                    ]
        
        self.opponent_positions = [np.array(opponent.state_abs_pos[:2]) if opponent.state_abs_pos is not None 
                                    else None
                                    for opponent in world.opponents
                                    ]

        self.my_ori = self.robot_model.imu_torso_orientation
        self.ball_2d = np.array(world.ball_abs_pos[:2]) # Ball pos as numpy array
        self.ball_vec = self.ball_2d - self.my_head_pos_2d
        self.ball_dir = M.vector_angle(self.ball_vec)
        self.ball_dist = np.linalg.norm(self.ball_vec)
        self.ball_sq_dist = self.ball_dist * self.ball_dist 
        self.ball_speed = np.linalg.norm(world.get_ball_abs_vel(6)[:2])
        
        self.goal_dir = M.target_abs_angle(self.ball_2d,(15.05,0))
        self.opponent_goal_pos = np.array([15.5, 0.0]) # Store as numpy array
        self.own_goal_pos = np.array([-15.5, 0.0])     # Store as numpy array

        self.PM_GROUP = world.play_mode_group

        self.slow_ball_pos = np.array(world.get_predicted_ball_pos(0.5)) # Predicted ball pos

        # --- Calculate distances using numpy for potentially faster operations ---
        
        # Calculate squared distances for teammates, handling None positions
        self.teammates_ball_sq_dist = []
        for i, p in enumerate(world.teammates):
            teammate_pos = self.teammate_positions[i]
            if teammate_pos is not None and p.state_last_update != 0 and (world.time_local_ms - p.state_last_update <= 360 or p.is_self) and not p.state_fallen:
                dist_sq = np.sum((teammate_pos - self.slow_ball_pos) ** 2)
                self.teammates_ball_sq_dist.append(dist_sq)
            else:
                 self.teammates_ball_sq_dist.append(1000.0) # Large distance

        # Calculate squared distances for opponents, handling None positions
        self.opponents_ball_sq_dist = []
        for i, p in enumerate(world.opponents):
             opponent_pos = self.opponent_positions[i]
             if opponent_pos is not None and p.state_last_update != 0 and world.time_local_ms - p.state_last_update <= 360 and not p.state_fallen:
                 dist_sq = np.sum((opponent_pos - self.slow_ball_pos) ** 2)
                 self.opponents_ball_sq_dist.append(dist_sq)
             else:
                 self.opponents_ball_sq_dist.append(1000.0) # Large distance

        # Find minimum distances safely
        self.min_teammate_ball_sq_dist = min(self.teammates_ball_sq_dist) if self.teammates_ball_sq_dist else 1000.0
        self.min_teammate_ball_dist = math.sqrt(self.min_teammate_ball_sq_dist)
        
        self.min_opponent_ball_sq_dist = min(self.opponents_ball_sq_dist) if self.opponents_ball_sq_dist else 1000.0
        self.min_opponent_ball_dist = math.sqrt(self.min_opponent_ball_sq_dist)

        # Determine active player (closest teammate to ball)
        self.active_player_unum = self.teammates_ball_sq_dist.index(self.min_teammate_ball_sq_dist) + 1 if self.min_teammate_ball_sq_dist < 1000.0 else 0 # 0 if no valid teammate distance

        # --- Hard-Coded Roles (Based on amaan-hans structure) ---
        self.my_role = 'MIDFIELDER' # Default Role
        if self.player_unum == 1:
            self.my_role = 'GOALIE'
        elif self.player_unum == 11: # Player 11 is the dedicated Cherry-Picker
             self.my_role = 'CHERRY_PICKER' 
        elif self.player_unum in [2, 3, 4]:
            self.my_role = 'DEFENDER'
        # Players 5, 6, 7, 8, 9, 10 remain MIDFIELDERS

        # Placeholder for desired position/orientation, updated in Agent.py
        self.my_desired_position = self.mypos 
        self.my_desired_orientation = self.ball_dir
        
        # --- Potential Fields parameters (from amaan-hans) ---
        self.goal_attraction_coefficient = 5.0
        self.obstacle_repulsion_coefficient = 100.0 # Might need tuning
        self.obstacle_effect_radius = 1.5 # Increased radius
        self.damping_coefficient = 0.3  
        self.previous_force = np.zeros(2) 
    
    # --- Helper Functions ---
        
    def IsFormationReady(self, point_preferences):
        # (Same logic as baseline/test34)
        is_formation_ready = True
        num_players = len(self.teammate_positions) # Use actual number of teammates
        for i in range(1, num_players + 1):
            if i != self.active_player_unum: 
                teammate_pos = self.teammate_positions[i-1]
                target_pos = point_preferences.get(i) # Get target pos safely

                if teammate_pos is not None and target_pos is not None:
                    # Use numpy distance calculation
                    distance_sq = np.sum((teammate_pos - target_pos) ** 2)
                    if distance_sq > 0.3**2: # Compare squared distances
                        is_formation_ready = False
                        break # Exit early if one player is out of position
        return is_formation_ready

    def GetDirectionRelativeToMyPositionAndTarget(self, target):
        # Ensure target is a numpy array
        target = np.array(target)
        # Handle case where my_head_pos_2d might be None initially (though unlikely)
        if self.my_head_pos_2d is None: return 0.0 
        
        target_vec = target - self.my_head_pos_2d
        # Avoid division by zero if target is current position
        if np.linalg.norm(target_vec) < 1e-6: return 0.0 
        
        target_dir = M.vector_angle(target_vec)
        return target_dir
    
    # --- Distance function (using numpy) ---
    def distance(self, point1, point2):
         # Ensure points are numpy arrays
         p1 = np.array(point1)
         p2 = np.array(point2)
         return np.linalg.norm(p1 - p2) 

    # --- Fast Dribble Helper Functions (from amaan-hans) ---
    def are_points_collinear(self, position, ball_pos, goal, tolerance=0.45):
        # Ensure points are numpy arrays
        p1 = np.array(position)
        p2 = np.array(ball_pos)
        p3 = np.array(goal)

        # Calculate area of the triangle formed by the points
        # Using the determinant formula: Area = 0.5 * |x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2)|
        area = 0.5 * abs(p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1]))

        # Points are collinear if the area is close to zero
        return area < tolerance 

    def point_in_direction(self, start_point, end_point, distance):
        # Ensure points are numpy arrays
        start = np.array(start_point)
        end = np.array(end_point)
        
        vec = end - start
        norm_vec = vec / np.linalg.norm(vec) if np.linalg.norm(vec) > 1e-6 else np.array([0.0, 0.0])
        
        new_point = start + norm_vec * distance
        return tuple(new_point) # Return as tuple for compatibility 

    def next_position_to_startat(self, target, ball, myposition, startat, buffer_distance=0.4, angle_threshold=85): # Increased threshold
        target = np.array(target)
        ball = np.array(ball)
        myposition = np.array(myposition)
        startat = np.array(startat)

        target_to_ball = ball - target
        ball_to_myposition = myposition - ball

        # Check for zero vectors
        norm_target_to_ball = np.linalg.norm(target_to_ball)
        norm_ball_to_myposition = np.linalg.norm(ball_to_myposition)

        if norm_target_to_ball < 1e-6 or norm_ball_to_myposition < 1e-6:
             return tuple(startat) # Cannot calculate angle, default to startat

        dot_product = np.dot(target_to_ball, ball_to_myposition)
        magnitude_product = norm_target_to_ball * norm_ball_to_myposition
        
        # Clamp value for arccos to avoid domain errors due to floating point inaccuracies
        cos_angle = np.clip(dot_product / magnitude_product, -1.0, 1.0)
        angle_degrees = np.degrees(np.arccos(cos_angle))

        if abs(angle_degrees) < angle_threshold:
            # Calculate perpendicular direction safely
            if norm_target_to_ball < 1e-6: return tuple(startat) # Avoid division by zero
            perpendicular_direction = np.array([-target_to_ball[1], target_to_ball[0]]) / norm_target_to_ball
            
            left_of_ball = ball + perpendicular_direction * buffer_distance
            right_of_ball = ball - perpendicular_direction * buffer_distance

            dist_left = np.linalg.norm(myposition - left_of_ball)
            dist_right = np.linalg.norm(myposition - right_of_ball)
            dist_startat = np.linalg.norm(myposition - startat)

            if dist_left < dist_right and dist_left < dist_startat:
                return tuple(left_of_ball)
            elif dist_right < dist_left and dist_right < dist_startat:
                return tuple(right_of_ball)
            else:
                return tuple(startat)
        else:
            return tuple(startat)

    def get_player_ahead(self, position):
        # (Similar logic to amaan-hans)
        position = np.array(position)
        best_teammate_pos = None
        min_distance = float('inf') 

        for i, teammate_pos in enumerate(self.teammate_positions):
             # Check if teammate exists, is ahead, and is not self
             if teammate_pos is not None and teammate_pos[0] > position[0] + 1.0 and i + 1 != self.player_unum:
                  current_distance = self.distance(teammate_pos, position)
                  # Prefer closer teammates ahead, but ensure they are reasonably far (e.g., > 2m)
                  if current_distance < min_distance and current_distance > 2.0: 
                       min_distance = current_distance
                       best_teammate_pos = teammate_pos
        
        # Return position of closest valid teammate ahead, or None if none found
        return best_teammate_pos if best_teammate_pos is not None else None


    # --- Potential Fields Pathfinding (from amaan-hans) ---
    def potential_fields_pathfinding(self, start_pos, goal_pos):
        start_pos = np.array(start_pos)
        goal_pos = np.array(goal_pos)

        attraction_force = self.calculate_attraction(start_pos, goal_pos)
        repulsion_force = self.calculate_repulsion(start_pos)
        # boundary_correction = self.apply_boundary_correction(start_pos) # Optional boundary check

        # Simple combination (can add damping later if needed)
        resulting_force = attraction_force + repulsion_force # + boundary_correction 
        
        # Limit the magnitude of the force to prevent excessive speed/instability
        max_force_magnitude = 1.0 # Tune this value
        current_magnitude = np.linalg.norm(resulting_force)
        if current_magnitude > max_force_magnitude:
             resulting_force = (resulting_force / current_magnitude) * max_force_magnitude
        
        next_position = start_pos + resulting_force

        # Clamp next position to stay within field bounds (approximate)
        next_position[0] = np.clip(next_position[0], -15.0, 15.0)
        next_position[1] = np.clip(next_position[1], -10.0, 10.0)

        return tuple(next_position)

    def calculate_attraction(self, current_pos, goal_pos):
        direction_to_goal = goal_pos - current_pos
        distance_to_goal = np.linalg.norm(direction_to_goal)
        
        # Avoid division by zero
        if distance_to_goal < 1e-6: return np.zeros(2) 
        
        # Simple linear attraction (can be made more complex)
        attraction_force = self.goal_attraction_coefficient * (direction_to_goal / distance_to_goal)
        return attraction_force

    def calculate_repulsion(self, current_pos):
        total_repulsion = np.zeros(2)
        current_pos = np.array(current_pos) # Ensure numpy array

        # Repulsion from opponents
        for opponent_pos in self.opponent_positions:
            if opponent_pos is not None:
                opponent_pos = np.array(opponent_pos) # Ensure numpy array
                direction_from_obstacle = current_pos - opponent_pos
                distance_to_obstacle = np.linalg.norm(direction_from_obstacle)

                if distance_to_obstacle < self.obstacle_effect_radius and distance_to_obstacle > 1e-6:
                    # Repulsion strength increases sharply as distance decreases
                    repulsion_magnitude = self.obstacle_repulsion_coefficient * (1.0 / distance_to_obstacle - 1.0 / self.obstacle_effect_radius) / (distance_to_obstacle**2)
                    repulsion_force = repulsion_magnitude * (direction_from_obstacle / distance_to_obstacle)
                    total_repulsion += repulsion_force
        
        # Optional: Add repulsion from teammates (usually less strong)
        # ...

        return total_repulsion

    # --- Tactical Foul Helpers ---
    def should_commit_tactical_foul(self):
        """Checks if conditions are met for a tactical foul."""
        # Condition 1: Opponent has ball very close to our goal
        opponent_near_goal_threshold = 5.0 # How close opponent must be to our goal
        own_goal_center = self.own_goal_pos
        
        opponent_has_ball = self.min_opponent_ball_dist < 0.5 # Opponent likely controls ball
        
        ball_near_our_goal = self.distance(self.ball_2d, own_goal_center) < opponent_near_goal_threshold

        # Condition 2: Ensure we are not already in a set piece mode
        is_playon = (self.play_mode == self.world.M_PLAY_ON)

        return opponent_has_ball and ball_near_our_goal and is_playon

    def get_tactical_foul_target(self):
        """Finds a suitable opponent far away to foul."""
        foul_target_pos = None
        max_dist_from_ball = 0.0
        min_dist_from_me = 1.0 # Don't foul someone right next to me

        for opponent_pos in self.opponent_positions:
            if opponent_pos is not None:
                dist_from_ball = self.distance(opponent_pos, self.ball_2d)
                dist_from_me = self.distance(opponent_pos, self.mypos)

                # Find opponent furthest from the current ball pos, but reasonably close to me
                if dist_from_ball > max_dist_from_ball and dist_from_me > min_dist_from_me and dist_from_me < 5.0:
                    max_dist_from_ball = dist_from_ball
                    foul_target_pos = opponent_pos
        
        return foul_target_pos # Returns position or None
        
    def point_on_line_segment(self, p1, p2, x_coord):
        """Finds the point (x_coord, y) on the line segment between p1 and p2."""
        p1 = np.array(p1)
        p2 = np.array(p2)
        # Ensure x_coord is between the x-coordinates of p1 and p2
        x_min, x_max = min(p1[0], p2[0]), max(p1[0], p2[0])
        x_coord = np.clip(x_coord, x_min, x_max)

        # Avoid division by zero if line is vertical
        if abs(p2[0] - p1[0]) < 1e-6:
            # Return point on segment with avg y if vertical
            y_avg = (p1[1] + p2[1]) / 2.0 
            return np.array([x_coord, y_avg]) 

        # Calculate slope (m) and y-intercept (b)
        m = (p2[1] - p1[1]) / (p2[0] - p1[0])
        b = p1[1] - m * p1[0]
        
        # Calculate y for the given x_coord
        y_coord = m * x_coord + b
        
        # Ensure y is within bounds of segment
        y_min, y_max = min(p1[1], p2[1]), max(p1[1], p2[1])
        y_coord = np.clip(y_coord, y_min, y_max)

        return np.array([x_coord, y_coord])
