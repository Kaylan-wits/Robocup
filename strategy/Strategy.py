# strategy/Strategy.py

import math
import numpy as np
from math_ops.Math_Ops import Math_Ops as M
from formation.Formation import GeneratePlayOn, GenerateDefense

# Define field boundaries (should match Formation.py)
FIELD_X_LIMIT = 15.0
FIELD_Y_LIMIT = 10.0
CLIP_BUFFER = 0.2
CLIP_X_MIN = -FIELD_X_LIMIT + CLIP_BUFFER
CLIP_X_MAX = FIELD_X_LIMIT - CLIP_BUFFER
CLIP_Y_MIN = -FIELD_Y_LIMIT + CLIP_BUFFER
CLIP_Y_MAX = FIELD_Y_LIMIT + CLIP_BUFFER

class Strategy():
    def __init__(self, world):
        # ... (Initialization code from previous version remains the same up to formation calculation) ...
        self.play_mode = world.play_mode
        self.robot_model = world.robot
        self.my_head_pos_2d = self.robot_model.loc_head_position[:2] if self.robot_model.loc_head_position is not None else np.array([0.0, 0.0])
        self.player_unum = self.robot_model.unum
        if 1 <= self.player_unum <= len(world.teammates) and world.teammates[self.player_unum-1].state_abs_pos is not None:
             self.mypos = (world.teammates[self.player_unum-1].state_abs_pos[0], world.teammates[self.player_unum-1].state_abs_pos[1])
        else:
             self.mypos = (self.my_head_pos_2d[0], self.my_head_pos_2d[1]) if self.my_head_pos_2d is not None else (0.0, 0.0)

        self.side = 1
        if world.team_side_is_left: self.side = 0

        self.teammate_positions = [
            np.array(teammate.state_abs_pos[:2]) if teammate and teammate.state_abs_pos is not None else np.array([-100.0, -100.0])
            for teammate in world.teammates
        ]
        while len(self.teammate_positions) < 5: self.teammate_positions.append(np.array([-100.0, -100.0]))
        self.teammate_positions = self.teammate_positions[:5]

        self.opponent_positions = [
             np.array(opponent.state_abs_pos[:2]) if opponent and opponent.state_abs_pos is not None else np.array([-100.0, -100.0])
             for opponent in world.opponents
        ]
        while len(self.opponent_positions) < 5: self.opponent_positions.append(np.array([-100.0, -100.0]))
        self.opponent_positions = self.opponent_positions[:5]

        self.ball_2d = np.array(world.ball_abs_pos[:2]) if world.ball_abs_pos is not None else np.array([0.0, 0.0])
        self.ball_vec = self.ball_2d - self.my_head_pos_2d
        ball_vec_norm = np.linalg.norm(self.ball_vec)
        self.ball_dir = M.vector_angle(self.ball_vec) if ball_vec_norm > 1e-6 else 0.0
        self.ball_dist = ball_vec_norm
        self.ball_sq_dist = self.ball_dist * self.ball_dist
        ball_vel = world.get_ball_abs_vel(6)
        self.ball_speed = np.linalg.norm(ball_vel[:2]) if ball_vel is not None else 0.0

        self.goal_dir = M.target_abs_angle(self.ball_2d,(15.05,0))
        self.PM_GROUP = world.play_mode_group
        predicted_ball = world.get_predicted_ball_pos(0.5)
        self.slow_ball_pos = np.array(predicted_ball) if predicted_ball is not None else self.ball_2d

        # --- Distance calculations ---
        valid_teammates = world.teammates[:5]
        self.teammates_ball_sq_dist = []
        for i, p in enumerate(valid_teammates):
             if p and p.state_abs_pos is not None and p.state_last_update is not None and p.state_last_update != 0:
                  is_recent = (world.time_local_ms - p.state_last_update <= 360) or p.is_self
                  is_standing = not p.state_fallen
                  if is_recent and is_standing:
                       sq_dist = np.sum((np.array(p.state_abs_pos[:2]) - self.slow_ball_pos) ** 2)
                       self.teammates_ball_sq_dist.append(sq_dist)
                  else: self.teammates_ball_sq_dist.append(1000.0)
             else: self.teammates_ball_sq_dist.append(1000.0)
        while len(self.teammates_ball_sq_dist) < 5: self.teammates_ball_sq_dist.append(1000.0)
        self.teammates_ball_sq_dist = self.teammates_ball_sq_dist[:5]

        valid_opponents = world.opponents[:5]
        self.opponents_ball_sq_dist = []
        for i, p in enumerate(valid_opponents):
             if p and p.state_abs_pos is not None and p.state_last_update is not None and p.state_last_update != 0:
                  is_recent = world.time_local_ms - p.state_last_update <= 360
                  is_standing = not p.state_fallen
                  if is_recent and is_standing:
                      sq_dist = np.sum((np.array(p.state_abs_pos[:2]) - self.slow_ball_pos) ** 2)
                      self.opponents_ball_sq_dist.append(sq_dist)
                  else: self.opponents_ball_sq_dist.append(1000.0)
             else: self.opponents_ball_sq_dist.append(1000.0)
        while len(self.opponents_ball_sq_dist) < 5: self.opponents_ball_sq_dist.append(1000.0)
        self.opponents_ball_sq_dist = self.opponents_ball_sq_dist[:5]

        # --- Active player calculation ---
        self.active_player_unum = 1
        self.min_teammate_ball_sq_dist = 1000.0
        self.min_teammate_ball_dist = math.sqrt(1000.0)
        self.second_min_teammate_ball_sq_dist = 1000.0
        if self.teammates_ball_sq_dist:
             valid_dists = [d for d in self.teammates_ball_sq_dist if d < 999.0]
             if valid_dists:
                  self.min_teammate_ball_sq_dist = min(valid_dists)
                  try:
                      self.active_player_unum = self.teammates_ball_sq_dist.index(self.min_teammate_ball_sq_dist) + 1
                  except ValueError:
                      self.min_teammate_ball_sq_dist = min(self.teammates_ball_sq_dist)
                      self.active_player_unum = self.teammates_ball_sq_dist.index(self.min_teammate_ball_sq_dist) + 1
                  self.min_teammate_ball_dist = math.sqrt(self.min_teammate_ball_sq_dist)
                  sorted_valid_dists = sorted(valid_dists)
                  self.second_min_teammate_ball_sq_dist = sorted_valid_dists[1] if len(sorted_valid_dists) > 1 else 1000.0

        self.min_opponent_ball_dist = math.sqrt(min(self.opponents_ball_sq_dist)) if self.opponents_ball_sq_dist and min(self.opponents_ball_sq_dist)<999 else math.sqrt(1000.0)

        self.my_ori = self.robot_model.imu_torso_orientation
        self.my_desired_orientation = self.ball_dir if self.ball_dist > 1e-6 else self.my_ori

        # --- Formation Generation ---
        self.formation_points = [np.array([-100.0, -100.0])] * 5
        opponent_is_closer = self.min_opponent_ball_dist < self.min_teammate_ball_dist
        opponent_is_near = self.min_opponent_ball_dist < 1.5
        ball_in_own_half = self.ball_2d[0] < 0.0
        use_defense_formation = False
        if self.play_mode != "PlayOn": use_defense_formation = True
        elif ball_in_own_half and (opponent_is_closer or opponent_is_near): use_defense_formation = True

        if not use_defense_formation:
             # --- ATTACK FORMATION ---
             try:
                  self.formation_points = GeneratePlayOn(self.ball_2d[0], self.ball_2d[1])
                  if not isinstance(self.formation_points, list) or len(self.formation_points) != 5:
                       print(f"Error: GeneratePlayOn returned invalid data type/length")
                       self.formation_points = [np.array([-100.0, -100.0])] * 5
                       use_defense_formation = True
             except Exception as e:
                  print(f"Error calling GeneratePlayOn: {e}")
                  self.formation_points = [np.array([-100.0, -100.0])] * 5
                  use_defense_formation = True
        # else: # Covered by the check below

        if use_defense_formation:
             # --- DEFENSE FORMATION ---
             try:
                  valid_opp_pos_list = [pos for pos in self.opponent_positions if not np.array_equal(pos, np.array([-100.0,-100.0]))]
                  self.formation_points = GenerateDefense(valid_opp_pos_list)
                  if not isinstance(self.formation_points, list) or len(self.formation_points) != 5:
                       print(f"Error: GenerateDefense returned invalid data type/length")
                       self.formation_points = [np.array([-100.0, -100.0])] * 5
             except Exception as e:
                  print(f"Error calling GenerateDefense: {e}")
                  self.formation_points = [np.array([-100.0, -100.0])] * 5


        # --- Assign my desired position ---
        self.my_desired_position = self.mypos # Default

        if 1 <= self.player_unum <= 5:
             # Get the base formation position for this player
             target_formation_pos_raw = self.formation_points[self.player_unum - 1]
             is_valid_formation_pos = not np.array_equal(target_formation_pos_raw, np.array([-100.0, -100.0]))

             # --- ROLE-BASED TARGET ADJUSTMENT ---
             if self.player_unum == self.active_player_unum and self.play_mode == "PlayOn":
                  # --- Active Player Target (Focus on Ball) ---
                  # (Logic from previous version: potential fields if close, else formation/approach ball)
                   if self.min_teammate_ball_dist < 5.0 :
                       next_pf_pos = self.potential_fields_pathfinding(self.mypos, goal_pos=tuple(self.ball_2d))
                       self.my_desired_position = next_pf_pos
                       target_vec = self.ball_2d - np.array(self.my_desired_position)
                       self.my_desired_orientation = M.vector_angle(target_vec) if np.linalg.norm(target_vec) > 1e-6 else self.ball_dir
                   elif is_valid_formation_pos:
                        self.my_desired_position = tuple(target_formation_pos_raw)
                        target_vec = self.ball_2d - np.array(self.my_desired_position)
                        self.my_desired_orientation = M.vector_angle(target_vec) if np.linalg.norm(target_vec) > 1e-6 else self.ball_dir
                   else: # Active, far, invalid formation spot -> go towards ball
                        next_pf_pos = self.potential_fields_pathfinding(self.mypos, goal_pos=tuple(self.ball_2d))
                        self.my_desired_position = next_pf_pos
                        target_vec = self.ball_2d - np.array(self.my_desired_position)
                        self.my_desired_orientation = M.vector_angle(target_vec) if np.linalg.norm(target_vec) > 1e-6 else self.ball_dir

             elif is_valid_formation_pos: # --- Non-Active Player Target (Formation + Support) ---
                  # Start with the calculated formation position
                  current_target = target_formation_pos_raw

                  # ***** SUPPORT LOGIC ADJUSTMENT *****
                  # If attacking (not defense formation) and active player is ahead, adjust position
                  if not use_defense_formation and self.active_player_unum != 0: # Ensure active player is valid
                      active_player_pos = self.teammate_positions[self.active_player_unum - 1]
                      is_active_player_valid = not np.array_equal(active_player_pos, np.array([-100.0, -100.0]))

                      if is_active_player_valid:
                          active_player_x = active_player_pos[0]
                          my_formation_x = current_target[0]
                          # Define 'ahead': active player is in opponent half and significantly further than my formation spot
                          is_active_ahead = active_player_x > 0 and active_player_x > my_formation_x + 4.0 # Active player is >4m ahead

                          if is_active_ahead:
                              # Calculate a support position relative to the active player
                              # Example: Stay ~4m behind and slightly wider than the active player
                              support_offset_x = -4.0
                              # Use player unum or formation Y to decide side offset (crude example)
                              side_offset_y = 5.0 if self.player_unum % 2 == 0 else -5.0 # Alternate sides
                              # Or use formation Y to decide side
                              # side_offset_y = np.sign(current_target[1]) * 5.0 if abs(current_target[1]) > 1.0 else 5.0

                              support_target = active_player_pos + np.array([support_offset_x, side_offset_y])

                              # Blend the formation target with the support target
                              # Weight towards support position if active player is far ahead
                              blend_factor = np.clip((active_player_x - (my_formation_x + 4.0)) / 10.0, 0.0, 0.8) # Blend more towards support the further ahead active player is (max 80% support)

                              # Calculate blended target
                              blended_target = (1.0 - blend_factor) * current_target + blend_factor * support_target

                              # Update current_target, ensure it's clipped later
                              current_target = blended_target
                              # print(f"Player {self.player_unum} supporting active {self.active_player_unum}. Blend: {blend_factor:.2f}") # Debug

                  # Assign the (potentially adjusted) target
                  self.my_desired_position = tuple(current_target)
                  # Orient towards the ball from the target spot
                  target_vec = self.ball_2d - np.array(self.my_desired_position)
                  self.my_desired_orientation = M.vector_angle(target_vec) if np.linalg.norm(target_vec) > 1e-6 else self.ball_dir

             else: # Non-active, invalid formation spot -> stay at current position
                  self.my_desired_position = self.mypos
                  self.my_desired_orientation = self.ball_dir if self.ball_dist > 1e-6 else self.my_ori


             # ***** FINAL CLIP for my_desired_position *****
             self.my_desired_position = (
                 np.clip(self.my_desired_position[0], CLIP_X_MIN, CLIP_X_MAX),
                 np.clip(self.my_desired_position[1], CLIP_Y_MIN, CLIP_Y_MAX)
             )

        else: # Invalid player unum
             print(f"Warning: Player unum {self.player_unum} out of range (1-5). Using current position.")
             self.my_desired_position = self.mypos
             self.my_desired_orientation = self.ball_dir if self.ball_dist > 1e-6 else self.my_ori

        # --- Amaan's Added Code / Params ---
        # (Keep this section as it was)
        self.goal_position = (FIELD_X_LIMIT + 0.5, 0.0) # Adjust based on actual goal line
        self.goal_tolerance = 0.25
        self.goal_attraction_coefficient = 5.0
        self.obstacle_repulsion_coefficient = 150.0
        self.obstacle_effect_radius = 1.2
        self.damping_coefficient = 0.3
        self.previous_force = np.zeros(2)
        self.formation_tiers = {"back": -10, "mid": 0, "forward": 10}
        self.defensive_bound_x = -10
        self.goal_shoot_margin = 0.2
        # --- END OF AMAAN'S CODE ---

    # --- Rest of the Strategy class methods ---
    # (IsFormationReady, GetDirection..., potential_fields..., etc. remain the same as previous correct version)
    def IsFormationReady(self, point_preferences=None):
        is_formation_ready = True
        num_players = 5
        if not hasattr(self, 'formation_points') or len(self.formation_points) != num_players:
             # print("Warning in IsFormationReady: self.formation_points not ready or wrong size.") # Reduce noise
             return False
        for i in range(1, num_players + 1):
            if i == self.active_player_unum: continue
            if i <= len(self.teammate_positions):
                teammate_pos = self.teammate_positions[i-1]
                # Use my_desired_position if it's me, otherwise use formation_points for others
                target_pos = self.my_desired_position if i == self.player_unum else self.formation_points[i-1]
                target_pos = np.array(target_pos) # Ensure numpy array

                if not np.array_equal(teammate_pos, np.array([-100.0, -100.0])) and \
                   not np.array_equal(target_pos, np.array([-100.0, -100.0])):
                    distance_sq = np.sum((teammate_pos - target_pos) ** 2)
                    if distance_sq > 0.7**2: # Use threshold
                        is_formation_ready = False
                        break
            else:
                 # print(f"Warning in IsFormationReady: Index {i} out of bounds.") # Reduce noise
                 is_formation_ready = False
                 break
        return is_formation_ready

    # GetDirectionRelativeToMyPositionAndTarget - unchanged
    def GetDirectionRelativeToMyPositionAndTarget(self,target):
        target_np = np.array(target)
        my_pos_np = self.my_head_pos_2d
        target_vec = target_np - my_pos_np
        vec_norm = np.linalg.norm(target_vec)
        if vec_norm < 1e-6: return 0.0
        target_dir = M.vector_angle(target_vec)
        return target_dir

    # potential_fields_pathfinding - unchanged
    def potential_fields_pathfinding(self, start_pos, goal_pos=None):
        if goal_pos is None: goal_pos = self.goal_position
        current_pos_np = np.array(start_pos); goal_pos_np = np.array(goal_pos)
        attraction_force = self.calculate_attraction(current_pos_np, goal_pos_np)
        repulsion_force = self.calculate_repulsion(current_pos_np)
        boundary_repulsion = self.apply_boundary_repulsion(current_pos_np)
        center_correction = self.central_field_correction(current_pos_np)
        resulting_force = (attraction_force + repulsion_force + boundary_repulsion + center_correction - self.damping_coefficient * self.previous_force)
        max_step = 0.5
        force_magnitude = np.linalg.norm(resulting_force)
        if force_magnitude > max_step: resulting_force = (resulting_force / force_magnitude) * max_step
        elif force_magnitude < 0.01: resulting_force = np.zeros(2)
        self.previous_force = resulting_force
        next_position = current_pos_np + resulting_force
        next_position[0] = np.clip(next_position[0], CLIP_X_MIN, CLIP_X_MAX)
        next_position[1] = np.clip(next_position[1], CLIP_Y_MIN, CLIP_Y_MAX)
        return (next_position[0], next_position[1])

    # calculate_attraction - unchanged
    def calculate_attraction(self, current_pos_np, goal_pos_np):
        direction_to_goal = goal_pos_np - current_pos_np
        distance_to_goal = np.linalg.norm(direction_to_goal)
        if distance_to_goal < 0.1: return np.zeros(2)
        direction_to_goal /= distance_to_goal
        scale_factor = 1.0
        attraction_force = self.goal_attraction_coefficient * direction_to_goal * scale_factor
        return attraction_force

    # calculate_repulsion - unchanged
    def calculate_repulsion(self, current_pos_np):
        total_repulsion = np.zeros(2)
        for opponent_pos_np in self.opponent_positions:
            if not np.array_equal(opponent_pos_np, np.array([-100.0, -100.0])):
                direction_from_obstacle = current_pos_np - opponent_pos_np
                distance_to_obstacle = np.linalg.norm(direction_from_obstacle)
                if 0 < distance_to_obstacle < self.obstacle_effect_radius:
                    repulsion_magnitude = self.obstacle_repulsion_coefficient * (1.0 / distance_to_obstacle - 1.0 / self.obstacle_effect_radius)
                    direction_from_obstacle /= distance_to_obstacle
                    repulsion_force = repulsion_magnitude * direction_from_obstacle
                    total_repulsion += repulsion_force
        return total_repulsion

    # apply_boundary_repulsion - unchanged
    def apply_boundary_repulsion(self, current_pos_np):
        repulsion_force = np.zeros(2)
        boundary_threshold = 1.0; strength = 200.0
        dist_from_pos_x = CLIP_X_MAX - current_pos_np[0]; dist_from_neg_x = current_pos_np[0] - CLIP_X_MIN
        if dist_from_pos_x < boundary_threshold and dist_from_pos_x > 0: repulsion_force[0] -= strength * (1.0 / dist_from_pos_x - 1.0 / boundary_threshold)
        elif dist_from_neg_x < boundary_threshold and dist_from_neg_x > 0: repulsion_force[0] += strength * (1.0 / dist_from_neg_x - 1.0 / boundary_threshold)
        dist_from_pos_y = CLIP_Y_MAX - current_pos_np[1]; dist_from_neg_y = current_pos_np[1] - CLIP_Y_MIN
        if dist_from_pos_y < boundary_threshold and dist_from_pos_y > 0: repulsion_force[1] -= strength * (1.0 / dist_from_pos_y - 1.0 / boundary_threshold)
        elif dist_from_neg_y < boundary_threshold and dist_from_neg_y > 0: repulsion_force[1] += strength * (1.0 / dist_from_neg_y - 1.0 / boundary_threshold)
        return repulsion_force

    # central_field_correction - unchanged
    def central_field_correction(self, current_pos_np):
        center_of_field=np.array([0.0, 0.0]); direction_to_center = center_of_field - current_pos_np
        distance_to_center = np.linalg.norm(direction_to_center)
        if distance_to_center < 1.0: return np.zeros(2)
        direction_to_center /= distance_to_center
        max_dist_scale = 15.0; strength = 0.2 * min(distance_to_center / max_dist_scale, 1.0)
        return strength * direction_to_center

    # distance - unchanged
    def distance(self, point1, point2):
        p1=np.array(point1); p2=np.array(point2)
        if np.array_equal(p1, np.array([-100.0,-100.0])) or np.array_equal(p2, np.array([-100.0,-100.0])): return float('inf')
        return np.linalg.norm(p1 - p2)

    # calculate_orientation - unchanged
    def calculate_orientation(self, target_pos, my_pos):
        target_vec = np.array(target_pos) - np.array(my_pos)
        vec_norm = np.linalg.norm(target_vec)
        if vec_norm < 1e-6: return self.my_ori if hasattr(self, 'my_ori') else 0.0
        target_angle_rad = np.arctan2(target_vec[1], target_vec[0])
        return np.degrees(target_angle_rad)

    # are_points_collinear - unchanged
    def are_points_collinear(self, position, ball_pos, goal, tolerance=10.0):
        p1=np.array(position); p2=np.array(ball_pos); p3=np.array(goal)
        vec1=p2-p1; vec2=p3-p2
        norm1=np.linalg.norm(vec1); norm2=np.linalg.norm(vec2)
        if norm1 < 1e-6 or norm2 < 1e-6: return True
        dot_product = np.dot(vec1, vec2)
        cos_theta = np.clip(dot_product / (norm1 * norm2), -1.0, 1.0)
        angle_diff_deg = np.degrees(np.arccos(cos_theta))
        return abs(angle_diff_deg) < tolerance or abs(angle_diff_deg - 180.0) < tolerance

    # point_in_direction - unchanged
    def point_in_direction(self, position, goal, distance=0.2):
         pos_np=np.array(position); goal_np=np.array(goal); direction_vec = goal_np - pos_np
         magnitude = np.linalg.norm(direction_vec)
         if magnitude < 1e-9: return tuple(pos_np)
         unit_direction = direction_vec / magnitude; scaled_vector = unit_direction * distance
         new_position = pos_np + scaled_vector; return tuple(new_position)

    # next_position_to_startat - unchanged
    def next_position_to_startat(self, target, ball, myposition, startat, buffer_distance=0.4, angle_threshold=85):
         target=np.array(target); ball=np.array(ball); myposition=np.array(myposition); startat=np.array(startat)
         startat_to_ball = ball - startat; ball_to_mypos = myposition - ball
         norm_startat_to_ball = np.linalg.norm(startat_to_ball); norm_ball_to_mypos = np.linalg.norm(ball_to_mypos)
         if norm_startat_to_ball < 0.1 or norm_ball_to_mypos < 0.1: return tuple(startat)
         dot_product = np.dot(startat_to_ball, ball_to_mypos)
         magnitude_product = norm_startat_to_ball * norm_ball_to_mypos
         cos_angle = np.clip(dot_product / magnitude_product, -1.0, 1.0)
         angle_degrees = np.degrees(np.arccos(cos_angle))
         if angle_degrees < angle_threshold:
             perp_dir = np.array([-startat_to_ball[1], startat_to_ball[0]]) / norm_startat_to_ball
             left_of_ball = ball + perp_dir * buffer_distance; right_of_ball = ball - perp_dir * buffer_distance
             dist_left = np.linalg.norm(myposition - left_of_ball); dist_right = np.linalg.norm(myposition - right_of_ball); dist_startat = np.linalg.norm(myposition - startat)
             if dist_left <= dist_right and dist_left <= dist_startat: return tuple(left_of_ball)
             elif dist_right < dist_left and dist_right <= dist_startat: return tuple(right_of_ball)
             else: return tuple(startat)
         else: return tuple(startat)

    # get_player_ahead - unchanged
    def get_player_ahead(self, position):
        closest_ahead_pos = None; min_distance = float('inf')
        my_x = position[0]; num_players = 5
        min_ahead_dist = 1.5; min_total_dist = 1.0; max_total_dist = 15.0
        for i in range(num_players):
             if i + 1 == self.player_unum: continue
             teammate_pos = self.teammate_positions[i]
             if not np.array_equal(teammate_pos, np.array([-100.0, -100.0])) and teammate_pos[0] > my_x + min_ahead_dist:
                  current_distance = self.distance(teammate_pos, position)
                  if min_total_dist < current_distance < max_total_dist and current_distance < min_distance:
                       min_distance = current_distance; closest_ahead_pos = teammate_pos
        return tuple(closest_ahead_pos) if closest_ahead_pos is not None else tuple(position)