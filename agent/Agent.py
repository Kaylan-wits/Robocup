# agent/Agent.py
from agent.Base_Agent import Base_Agent
from math_ops.Math_Ops import Math_Ops as M
import math
import numpy as np

from strategy.Assignment import role_assignment
from strategy.Assignment import pass_reciever_selector
from strategy.Strategy import Strategy
# --- ADDED IMPORT ---
from strategy.Strategy import CLIP_X_MIN, CLIP_X_MAX, CLIP_Y_MIN, CLIP_Y_MAX
# --- END IMPORT ---

from formation.Formation import GeneratePlayOn
from formation.Formation import GenerateDefense



class Agent(Base_Agent):
    def __init__(self, host:str, agent_port:int, monitor_port:int, unum:int,
                 team_name:str, enable_log, enable_draw, wait_for_server=True, is_fat_proxy=False) -> None:

        # define robot type
        robot_type = (0,1,1,1,2,3,3,3,4,4,4)[unum-1]

        # Initialize base agent
        # Args: Server IP, Agent Port, Monitor Port, Uniform No., Robot Type, Team Name, Enable Log, Enable Draw, play mode correction, Wait for Server, Hear Callback
        super().__init__(host, agent_port, monitor_port, unum, robot_type, team_name, enable_log, enable_draw, True, wait_for_server, None)

        self.enable_draw = enable_draw
        self.state = 0  # 0-Normal, 1-Getting up, 2-Kicking
        self.kick_direction = 0
        self.kick_distance = 0
        self.fat_proxy_cmd = "" if is_fat_proxy else None
        self.fat_proxy_walk = np.zeros(3) # filtered walk parameters for fat proxy

        self.init_pos = ([-14,0],[-9,-5],[-9,0],[-9,5],[-5,-5],[-5,0],[-5,5],[-2,-6],[-2,-2.5],[-2,2.5],[-2,6])[unum-1] # initial formation


    def beam(self, avoid_center_circle=False):
        r = self.world.robot
        pos = list(self.init_pos[:]) # copy position list ensure it's mutable
        self.state = 0


        # Avoid center circle by moving the player back
        if avoid_center_circle and np.linalg.norm(self.init_pos) < 2.5:
            pos[0] = -2.3

        # Ensure pos is a numpy array for subtraction
        pos_np = np.array(pos)
        current_pos_np = np.array(r.loc_head_position[:2]) if r.loc_head_position is not None else np.array([0.0, 0.0])


        if np.linalg.norm(pos_np - current_pos_np) > 0.1 or self.behavior.is_ready("Get_Up"):
             # Use tuple for scom.commit_beam position argument
            self.scom.commit_beam(tuple(pos_np), M.vector_angle((-pos_np[0],-pos_np[1]))) # beam to initial position, face coordinate (0,0)
        else:
            if self.fat_proxy_cmd is None: # normal behavior
                self.behavior.execute("Zero_Bent_Knees_Auto_Head")
            else: # fat proxy behavior
                self.fat_proxy_cmd += "(proxy dash 0 0 0)"
                self.fat_proxy_walk = np.zeros(3) # reset fat proxy walk


    def move(self, target_2d=(0,0), orientation=None, is_orientation_absolute=True,
             avoid_obstacles=True, priority_unums=[], is_aggressive=False, timeout=3000):
        '''
        Walk to target position
        '''
        r = self.world.robot

        if self.fat_proxy_cmd is not None: # fat proxy behavior
            self.fat_proxy_move(target_2d, orientation, is_orientation_absolute) # ignore obstacles
            return

        # Ensure target_2d is suitable for path manager (expects tuple or list)
        target_2d_input = tuple(target_2d) if isinstance(target_2d, np.ndarray) else target_2d


        if avoid_obstacles:
            target_2d_path, _, distance_to_final_target = self.path_manager.get_path_to_target(
                target_2d_input, priority_unums=priority_unums, is_aggressive=is_aggressive, timeout=timeout)
        else:
            current_pos_np = np.array(r.loc_head_position[:2]) if r.loc_head_position is not None else np.array([0.0, 0.0])
            target_2d_np = np.array(target_2d_input)
            distance_to_final_target = np.linalg.norm(target_2d_np - current_pos_np)
            target_2d_path = target_2d_input # No path modification if not avoiding obstacles


        # Ensure target_2d_path is suitable for behavior.execute (expects tuple or list)
        target_2d_execute = tuple(target_2d_path) if isinstance(target_2d_path, np.ndarray) else target_2d_path

        self.behavior.execute("Walk", target_2d_execute, True, orientation, is_orientation_absolute, distance_to_final_target) # Args: target, is_target_abs, ori, is_ori_abs, distance


    # Removed the illegal 'kick' function wrapper for 'Dribble' behavior.

    def kickTarget(self, strategyData, mypos_2d=(0,0),target_2d=(0,0), abort=False, enable_pass_command=False):
        '''
        Walk to ball and kick using Basic_Kick behavior.
        '''

        # Ensure inputs are numpy arrays for calculations
        mypos_np = np.array(mypos_2d)
        target_np = np.array(target_2d)

        # Calculate the vector from the current position to the target position
        vector_to_target = target_np - mypos_np

        # Calculate the distance (magnitude of the vector)
        kick_distance = np.linalg.norm(vector_to_target)

        # Calculate the direction (angle) in radians
        # Avoid division by zero or invalid arctan2 input if vector is zero
        if vector_to_target.any(): # Check if vector is not [0, 0]
            direction_radians = np.arctan2(vector_to_target[1], vector_to_target[0])
        else:
            direction_radians = 0.0 # Default direction if target is current position

        # Convert direction to degrees for easier interpretation (optional)
        kick_direction = np.degrees(direction_radians)


        # Pass command logic (seems fine, keep it)
        if strategyData.min_opponent_ball_dist < 1.45 and enable_pass_command:
            self.scom.commit_pass_command()

        # Update kick direction (this seems okay, but Basic_Kick might ignore distance)
        self.kick_direction = kick_direction # Always use the calculated direction for this specific kick
        self.kick_distance = kick_distance # Store distance, though Basic_Kick might not use it


        if self.fat_proxy_cmd is None: # normal behavior
            # Execute Basic_Kick with the calculated direction
            return self.behavior.execute("Basic_Kick", self.kick_direction, abort) # Basic_Kick uses direction, ignores distance
        else: # fat proxy behavior
            return self.fat_proxy_kick()

    # Removed the illegal 'dribble' function wrapper for 'Dribble' behavior.

    # --- START OF LEGAL DRIBBLE LOGIC ---
    # This function uses only move and kickTarget to advance the ball
    def dribbleToTarget(self, strategyData, aim=(15.5,0)):
        """
        Implements a simple, rule-compliant dribble towards a target (aim).
        It uses sequences of move() to get behind the ball and kickTarget()
        to push it forward.
        """
        drawer = self.world.draw # Get drawer instance
        my_pos = strategyData.mypos # Current position tuple
        ball_pos = tuple(strategyData.ball_2d) # Ball position tuple
        goal = tuple(aim) # Target position tuple

        # Constants for dribble behavior
        KICK_RANGE = 0.5 # How close player needs to be to kick
        ALIGNMENT_TOLERANCE = 15.0 # Degrees +/- for being "behind" the ball
        APPROACH_DIST = 0.4 # How close to get to the ball before kicking
        KICK_FORWARD_DIST = 2.0 # How far to kick the ball each time
        SHOOT_RANGE = 7.0 # How close to goal to attempt a shot
        SHOOT_X_THRESHOLD = 10.0 # Only shoot if past this X-coordinate


        # 1. Check if close enough to goal to shoot directly
        if strategyData.distance(my_pos, goal) < SHOOT_RANGE and my_pos[0] > SHOOT_X_THRESHOLD:
            if not strategyData.is_path_blocked(my_pos, goal, buffer=0.8):
                # --- FIXED COLOR ---
                drawer.annotation((0, 8.5), f"Dribble: Shooting" , drawer.Color.orange, "dribble_status")
                # --- END FIX ---
                return self.kickTarget(strategyData, my_pos, goal)

        # 2. Check if player is close enough to the ball to kick it
        if strategyData.ball_dist < KICK_RANGE:
            # Player is near the ball. Kick it forward towards the aim point.
            kick_target_pos = strategyData.point_in_direction(ball_pos, goal, distance=KICK_FORWARD_DIST)
            # --- FIXED COLOR ---
            drawer.annotation((0, 8.5), f"Dribble: Kicking Forward" , drawer.Color.orange, "dribble_status")
            # --- END FIX ---
            return self.kickTarget(strategyData, my_pos, kick_target_pos)

        # 3. Player is not close enough to kick. Need to move towards the ball.
        else:
            # Calculate the ideal position slightly behind the ball, aligned with the goal
            ideal_behind_pos = strategyData.point_in_direction(ball_pos, goal, distance=-0.2) # Target slightly behind ball

            # Check if player is already reasonably aligned behind the ball
            is_collinear = strategyData.are_points_collinear(my_pos, ball_pos, goal, tolerance=ALIGNMENT_TOLERANCE)

            if is_collinear and strategyData.distance(my_pos, ball_pos) < 1.5: # If aligned and close, move directly to ball approach point
                target_pos = strategyData.point_in_direction(ball_pos, my_pos, distance=APPROACH_DIST) # Target approach point near ball
                target_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos) # Face the ball
                drawer.annotation((0, 8.5), f"Dribble: Approaching Ball" , drawer.Color.cyan, "dribble_status")
                return self.move(target_pos, orientation=target_orientation, avoid_obstacles=True)
            else: # Not aligned or too far away, move to the ideal spot behind the ball
                target_pos = ideal_behind_pos
                target_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos) # Face the ball
                drawer.annotation((0, 8.5), f"Dribble: Aligning Behind Ball" , drawer.Color.cyan, "dribble_status")
                # Use obstacle avoidance when aligning from potentially further away
                return self.move(target_pos, orientation=target_orientation, avoid_obstacles=True)
    # --- END OF LEGAL DRIBBLE LOGIC ---

    def think_and_send(self):

        behavior = self.behavior
        strategyData = Strategy(self.world)
        drawer = self.world.draw # Use alias 'drawer'

        # Convert None positions to a default far-away location for calculations
        # This is a safety check to prevent crashes if a player is not seen
        default_pos = np.array([-100.0, -100.0])
        # Ensure positions are numpy arrays *before* passing to Strategy if needed,
        # but Strategy init already handles this conversion.
        # Let Strategy handle internal types.

        # --- Game State Handling ---
        if strategyData.play_mode == self.world.M_GAME_OVER:
            pass # Do nothing
        elif strategyData.PM_GROUP == self.world.MG_ACTIVE_BEAM:
            self.beam()
        elif strategyData.PM_GROUP == self.world.MG_PASSIVE_BEAM:
            self.beam(True) # avoid center circle
        elif self.state == 1 or (behavior.is_ready("Get_Up") and self.fat_proxy_cmd is None):
             # Handle getting up state
            self.state = 0 if behavior.execute("Get_Up") else 1
        elif (strategyData.PM_GROUP == self.world.MG_THEIR_KICK):
             # Move to initial position and face the ball during opponent's kick
            self.move(self.init_pos, orientation=strategyData.ball_dir)

        # --- Set Plays Handling (Using kickTarget) ---
        elif (strategyData.play_mode == self.world.M_OUR_KICKOFF):
            # Example: Player 9 takes kickoff, kicks towards opponent side
            # Adjust player number if needed (using 5 for 5v5 example)
            if strategyData.robot_model.unum == 5: # Assuming player 5 is designated kicker
                drawer.annotation((0, 8.5), f"Set Play: Kickoff" , drawer.Color.yellow, "setplay_status")
                return self.kickTarget(strategyData, strategyData.mypos, (5, 0)) # Kick towards center field
            else:
                 # Other players hold position or move slightly
                 self.move(self.init_pos, orientation=strategyData.ball_dir)

        elif (strategyData.play_mode == self.world.M_OUR_GOAL_KICK):
            # Goalie (Player 1) takes goal kick
            if strategyData.robot_model.unum == 1:
                drawer.annotation((0, 8.5), f"Set Play: Goal Kick" , drawer.Color.yellow, "setplay_status")
                 # Find best target (e.g., teammate or clear space)
                kick_target, kick_type = strategyData.find_best_kick_target()
                if kick_target is not None:
                     return self.kickTarget(strategyData, strategyData.mypos, tuple(kick_target))
                else:
                     # Fallback kick if no target found
                     return self.kickTarget(strategyData, strategyData.mypos, (0, 0)) # Kick towards center
            else:
                 # Other players move to formation/receive position
                 self.select_skill(strategyData) # Let select_skill handle non-kicker positioning

        # --- ADD HANDLING FOR OTHER SET PLAYS (Kick In, Free Kick, Corner) ---
        # Example for Kick In:
        elif strategyData.play_mode == self.world.M_OUR_KICK_IN:
             # Determine which player takes the kick in (closest eligible?)
             # For simplicity, assume active player takes it if close enough
             if strategyData.active_player_unum == strategyData.robot_model.unum and strategyData.ball_dist < 1.0:
                 drawer.annotation((0, 8.5), f"Set Play: Kick In" , drawer.Color.yellow, "setplay_status")
                 kick_target, kick_type = strategyData.find_best_kick_target()
                 if kick_target is not None:
                      return self.kickTarget(strategyData, strategyData.mypos, tuple(kick_target))
                 else:
                      return self.kickTarget(strategyData, strategyData.mypos, (strategyData.ball_2d[0], 0)) # Kick towards center line
             else:
                  # Move to formation or support position
                  self.select_skill(strategyData)


        # --- Default PlayOn or other modes ---
        else:
            if strategyData.play_mode != self.world.M_BEFORE_KICKOFF:
                drawer.clear("setplay_status") # Clear set play status if in PlayOn
                self.select_skill(strategyData)
            else:
                # Before kick off, just stay put (or beam if needed)
                 self.beam(True) # Use beam logic to hold position

        #--------------------------------------- 3. Broadcast
        self.radio.broadcast()

        #--------------------------------------- 4. Send to server
        if self.fat_proxy_cmd is None: # normal behavior
            command = strategyData.robot_model.get_command()
            # Basic check for None command to prevent errors
            if command:
                self.scom.commit_and_send(command)
            # else:
                # print(f"Warning: Player {strategyData.player_unum} generated None command.")
                # Optionally send a default safe command like standing still
                # self.behavior.execute("Zero_Bent_Knees_Auto_Head")
                # self.scom.commit_and_send(strategyData.robot_model.get_command())
        else: # fat proxy behavior
            if self.fat_proxy_cmd: # Ensure command is not empty
                self.scom.commit_and_send( self.fat_proxy_cmd.encode() )
            self.fat_proxy_cmd = "" # Reset fat proxy command


    def select_skill(self,strategyData):
        #--------------------------------------- 2. Decide action

        drawer = self.world.draw

        path_draw_options = self.path_manager.draw_options

        target = (15,0) # Opponents Goal
        #------------------------------------------------------
        #Role Assignment & Formation Logic (Keep as before)
        formation_positions = []
        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player
            # Clear status from previous logic if needed
            drawer.clear("status")
            # drawer.annotation((0,10.5), "Assigning Roles..." , drawer.Color.yellow, "status") # Optional temp status
        else:
             drawer.clear("status")
             drawer.clear("action_status") # Clear action status for non-active players
             drawer.clear("dribble_status") # Clear dribble status


        # Determine formation based on opponent proximity
        visible_opponents_np = [pos for pos in strategyData.opponent_positions if not np.array_equal(pos, np.array([-100.0, -100.0]))]
        # Convert to list of tuples if GenerateDefense expects that
        visible_opponents = [tuple(p) for p in visible_opponents_np]


        use_defense = False
        if len(visible_opponents) > 0:
            # Increased margin
            if strategyData.min_opponent_ball_dist + 1.0 < strategyData.min_teammate_ball_dist:
                formation_positions_np = GenerateDefense(visible_opponents_np) # Pass numpy arrays if function expects them
                drawer.annotation((0,10.5), "Mode: DEFENSE" , drawer.Color.red, "status") #
                use_defense = True
            else: # Attack/Play On
                # Pass ball coordinates as floats
                formation_positions_np = GeneratePlayOn(strategyData.ball_2d[0], strategyData.ball_2d[1])
                drawer.annotation((0,10.5), "Mode: ATTACK / PLAY ON" , drawer.Color.green, "status") #
        else: # No opponents visible, default to attack
            formation_positions_np = GeneratePlayOn(strategyData.ball_2d[0], strategyData.ball_2d[1])
            drawer.annotation((0,10.5), "Mode: ATTACK / PLAY ON" , drawer.Color.green, "status") #

        # Ensure formation_positions are numpy arrays before padding logic
        formation_positions = [np.array(p) for p in formation_positions_np]


        # Pad teammate positions if needed (using numpy arrays)
        current_teammates_np = strategyData.teammate_positions # These are already numpy arrays from Strategy init
        valid_teammates_np = [pos for pos in current_teammates_np if pos is not None and not np.array_equal(pos, np.array([-100.0, -100.0]))]
        num_teammates = len(valid_teammates_np)
        dummy_pos_np = np.array([-100.0, -100.0])

        # Padding logic needs lists of tuples for role_assignment
        if num_teammates < 11:
            padded_teammates_tuples = [tuple(p) for p in valid_teammates_np] + [tuple(dummy_pos_np)] * (11 - num_teammates)
        else:
            padded_teammates_tuples = [tuple(p) for p in valid_teammates_np[:11]]

        # Pad formation positions (convert numpy arrays to tuples for role_assignment)
        current_formation = formation_positions # List of numpy arrays
        num_formation = len(current_formation)
        if num_formation < 11:
            padded_formation_tuples = [tuple(p) for p in current_formation] + [tuple(dummy_pos_np)] * (11 - num_formation)
        else:
            padded_formation_tuples = [tuple(p) for p in current_formation[:11]]


        # Now call role_assignment with guaranteed 11-element lists of tuples
        point_preferences = role_assignment(padded_teammates_tuples, padded_formation_tuples)
        # point_preferences is now a dict {unum: tuple(x,y)}
        # --- END ROLE ASSIGNMENT ---


        # --- Set my_desired_position based on role ---
        my_role_target_pos_tuple = None # Initialize
        if strategyData.player_unum in point_preferences:
            my_role_target_pos_tuple = point_preferences[strategyData.player_unum]


        if strategyData.active_player_unum != strategyData.robot_model.unum: # Only set desired pos if NOT active
             # Non-active player follows formation or fallback
             if my_role_target_pos_tuple is not None and my_role_target_pos_tuple != (-100.0,-100.0) :
                  # Check if support logic adjustment is needed (only in attack mode)
                  if not use_defense:
                      active_player_pos_np = strategyData.teammate_positions[strategyData.active_player_unum - 1]
                      is_active_player_valid = not np.array_equal(active_player_pos_np, np.array([-100.0, -100.0]))

                      if is_active_player_valid:
                          active_player_x = active_player_pos_np[0]
                          my_formation_x = my_role_target_pos_tuple[0]
                          is_active_ahead = active_player_x > 0 and active_player_x > my_formation_x + 4.0

                          if is_active_ahead:
                              support_offset_x = -4.0
                              side_offset_y = 5.0 if strategyData.player_unum % 2 == 0 else -5.0
                              support_target_np = active_player_pos_np + np.array([support_offset_x, side_offset_y])

                              blend_factor = np.clip((active_player_x - (my_formation_x + 4.0)) / 10.0, 0.0, 0.8)

                              current_target_np = np.array(my_role_target_pos_tuple)
                              blended_target_np = (1.0 - blend_factor) * current_target_np + blend_factor * support_target_np

                              # --- FIXED CLIP ---
                              # Clip using the imported constants directly
                              blended_target_np[0] = np.clip(blended_target_np[0], CLIP_X_MIN, CLIP_X_MAX)
                              blended_target_np[1] = np.clip(blended_target_np[1], CLIP_Y_MIN, CLIP_Y_MAX)
                              # --- END FIX ---

                              strategyData.my_desired_position = tuple(blended_target_np) # Store as tuple
                          else:
                               # Not supporting, use original role target
                               strategyData.my_desired_position = my_role_target_pos_tuple # Already clipped in GeneratePlayOn/Defense
                      else:
                           # Active player not valid, use original role target
                           strategyData.my_desired_position = my_role_target_pos_tuple
                  else:
                       # In defense mode, just use the role target
                       strategyData.my_desired_position = my_role_target_pos_tuple
             else:
                 # Fallback: if not assigned or invalid, just go to init_pos
                 strategyData.my_desired_position = self.init_pos # Already a tuple
             # Calculate desired orientation (face ball)
             strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d) # Target ball


        # Draw line from current pos to desired pos (ensure tuples)
        drawer.line(tuple(strategyData.mypos), tuple(strategyData.my_desired_position), 2,drawer.Color.blue,"target line")


        # --- Action Selection ---
        if strategyData.active_player_unum == strategyData.robot_model.unum:  # I am the active player
            drawer.clear("dribble_status") # Clear old dribble status first
            # Decide between kicking (pass/shoot/clear) or dribbling
            kick_target, kick_type = strategyData.find_best_kick_target()

            if kick_target is not None:
                # Good kick option available
                drawer.annotation((0, 9.5), f"Action: {kick_type}" , drawer.Color.white, "action_status")
                return self.kickTarget(strategyData, strategyData.mypos, tuple(kick_target))
            else:
                # No good kick, fallback to dribbleToTarget logic
                drawer.annotation((0, 9.5), f"Action: Dribble" , drawer.Color.orange, "action_status")
                # Call the rule-compliant dribble logic function
                return self.dribbleToTarget(strategyData, aim=target) # Pass goal as aim

        else: # I am NOT the active player
            # Follow assigned formation/support position (my_desired_position was set above)
            drawer.annotation((0, 9.5), f"Action: Move to Formation" , drawer.Color.cyan, "action_status")
            # Ensure orientation is towards the ball
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d)
            return self.move(tuple(strategyData.my_desired_position), orientation=strategyData.my_desired_orientation, avoid_obstacles=True) # Use obstacle avoidance


    #--------------------------------------- Fat proxy auxiliary methods
    def fat_proxy_kick(self):
        w = self.world
        r = self.world.robot
        # Ensure ball_abs_pos exists and has at least 2 elements
        ball_2d = np.array(w.ball_abs_pos[:2]) if w.ball_abs_pos and len(w.ball_abs_pos) >= 2 else np.array([0.0, 0.0])
        # Ensure loc_head_position exists and has at least 2 elements
        my_head_pos_2d = np.array(r.loc_head_position[:2]) if r.loc_head_position and len(r.loc_head_position) >= 2 else np.array([0.0, 0.0])


        if np.linalg.norm(ball_2d - my_head_pos_2d) < 0.25:
            # fat proxy kick arguments: power [0,10]; relative horizontal angle [-180,180]; vertical angle [0,70]
            kick_angle_rel = M.normalize_deg( self.kick_direction  - r.imu_torso_orientation ) if hasattr(r, 'imu_torso_orientation') else self.kick_direction
            self.fat_proxy_cmd += f"(proxy kick 10 {kick_angle_rel:.2f} 20)"
            self.fat_proxy_walk = np.zeros(3) # reset fat proxy walk
            return True
        else:
            # Calculate target behind ball correctly
            target_behind_ball = ball_2d - np.array([0.1, 0.0]) # Example: target 0.1m behind ball
            self.fat_proxy_move(tuple(target_behind_ball), None, True) # ignore obstacles
            return False


    def fat_proxy_move(self, target_2d, orientation, is_orientation_absolute):
        r = self.world.robot
         # Ensure loc_head_position exists and has at least 2 elements
        my_head_pos_2d = np.array(r.loc_head_position[:2]) if r.loc_head_position and len(r.loc_head_position) >= 2 else np.array([0.0, 0.0])
        target_2d_np = np.array(target_2d)

        target_dist = np.linalg.norm(target_2d_np - my_head_pos_2d)

        # Ensure imu_torso_orientation exists
        current_orientation = r.imu_torso_orientation if hasattr(r, 'imu_torso_orientation') else 0.0
        target_dir = M.target_rel_angle(my_head_pos_2d, current_orientation, target_2d_np)


        if target_dist > 0.1 and abs(target_dir) < 8:
            self.fat_proxy_cmd += (f"(proxy dash 100 0 0)") # Simplified dash command
            return

        final_turn_angle = 0.0
        if target_dist < 0.1:
            if orientation is not None:
                if is_orientation_absolute:
                    # Calculate relative orientation if absolute orientation is given
                    orientation = M.normalize_deg( orientation - current_orientation )
                # Clip the relative orientation
                final_turn_angle = np.clip(orientation, -60, 60)
            else:
                 # If no orientation specified when close, use target_dir (usually small)
                 final_turn_angle = np.clip(target_dir, -60, 60)
            # Command to turn in place
            self.fat_proxy_cmd += (f"(proxy dash 0 0 {final_turn_angle:.1f})")
        else:
             # Command to dash towards target while turning
             turn_component = np.clip(target_dir, -60, 60) # Turn towards target while moving
             self.fat_proxy_cmd += (f"(proxy dash 20 0 {turn_component:.1f})") # Reduced speed for more control