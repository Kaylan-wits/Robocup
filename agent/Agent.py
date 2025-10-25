from agent.Base_Agent import Base_Agent
from math_ops.Math_Ops import Math_Ops as M
import math
import numpy as np

# Import necessary functions from other files
from strategy.Assignment import role_assignment, pass_reciever_selector
from strategy.Strategy import Strategy
# --- UPDATED IMPORTS ---
from formation.Formation import GenerateOffense, GenerateDefense 
# -----------------------

class Agent(Base_Agent):
    def __init__(self, host:str, agent_port:int, monitor_port:int, unum:int,
                 team_name:str, enable_log, enable_draw, wait_for_server=True, is_fat_proxy=False) -> None:

        # define robot type - Assuming 11 players for role assignment
        # If running with 5, ensure roles in Strategy.py only use 1-5
        robot_type = (0,1,1,1,2,3,3,3,4,4,4)[unum-1] if unum <= 11 else 0 # Default type if unum > 11

        # Initialize base agent
        super().__init__(host, agent_port, monitor_port, unum, robot_type, team_name, enable_log, enable_draw, True, wait_for_server, None)

        self.enable_draw = enable_draw
        self.state = 0  # 0-Normal, 1-Getting up
        # Removed kicking state as newKickdef handles movement

        # --- ADDED FROM PROXY VERSION ---
        self.kick_direction = 0
        self.kick_distance = 0
        self.fat_proxy_cmd = "" if is_fat_proxy else None
        self.fat_proxy_walk = np.zeros(3) # filtered walk parameters for fat proxy
        # --------------------------------

        # Initial positions for an 11-player setup (adjust if using 5)
        # Based roughly on amaan-hans and muzzaam/test34 initial positions
        self.init_pos = (
            [-14,0], [-11,4], [-11,-4], [-11, 0], # Goalie, 3 Defenders
            [-5,-5], [-5, 0], [-5, 5],           # 3 Midfielders
            [-1,-6], [-1,-2.5], [-1,2.5],        # 3 Attackers/Wingers
            [10, 0]                              # Cherry Picker (adjust X as needed)
        )[unum-1] if unum <= 11 else [-1, 0]     # Default pos if unum > 11


    def beam(self, avoid_center_circle=False):
        r = self.world.robot
        # Ensure init_pos is treated as a mutable list for modification
        pos = list(self.init_pos[:]) # copy position list
        self.state = 0

        # Avoid center circle by moving the player back
        if avoid_center_circle and np.linalg.norm(self.init_pos) < 2.5:
             # Check if pos has at least one element before modifying
            if len(pos) > 0:
                pos[0] = -2.3

        # Convert pos back to tuple for beam function if needed, or ensure beam accepts list
        beam_pos_tuple = tuple(pos)

        # Ensure loc_head_position exists before calculating norm
        current_pos_2d = r.loc_head_position[:2] if r.loc_head_position is not None else np.array([0,0])

        if np.linalg.norm(np.array(beam_pos_tuple) - current_pos_2d) > 0.1 or self.behavior.is_ready("Get_Up"):
             # Beam facing center (0,0) - adjust angle calculation if pos can be empty
            angle = M.vector_angle((-beam_pos_tuple[0], -beam_pos_tuple[1])) if len(beam_pos_tuple) >= 2 else 0
            self.scom.commit_beam(beam_pos_tuple, angle)
        else:
            # --- MODIFIED FOR PROXY ---
            if self.fat_proxy_cmd is None: # normal behavior
                self.behavior.execute("Zero_Bent_Knees_Auto_Head")
            else: # fat proxy behavior
                self.fat_proxy_cmd += "(proxy dash 0 0 0)"
                self.fat_proxy_walk = np.zeros(3) # reset fat proxy walk
            # --------------------------


    def move(self, target_2d=(0,0), orientation=None, is_orientation_absolute=True,
             avoid_obstacles=True, priority_unums=[], is_aggressive=False, timeout=3000):
        
        # --- ADDED FROM PROXY VERSION ---
        if self.fat_proxy_cmd is not None: # fat proxy behavior
            self.fat_proxy_move(target_2d, orientation, is_orientation_absolute) # ignore obstacles
            return
        # --------------------------------
        
        r = self.world.robot
        # Ensure robot position is valid before proceeding
        if r.loc_head_position is None:
            # print(f"Player {self.world.robot.unum}: Cannot move, position unknown.")
            return # Skip move if position unknown

        current_pos_2d = r.loc_head_position[:2]
        target_np = np.array(target_2d) # Ensure target is numpy array

        # Basic check for valid target coordinates (e.g., within reasonable field bounds)
        if not (-20 < target_np[0] < 20 and -15 < target_np[1] < 15):
             # print(f"Player {self.world.robot.unum}: Invalid move target {target_np}, staying put.")
             target_np = current_pos_2d # Stay put if target is invalid

        distance_to_final_target = np.linalg.norm(target_np - current_pos_2d)

        if avoid_obstacles:
            # Path manager might return original target if pathfinding fails or times out
            planned_target, _, distance_to_final_target_pf = self.path_manager.get_path_to_target(
                target_np, priority_unums=priority_unums, is_aggressive=is_aggressive, timeout=timeout)
            # Ensure planned_target is valid before using it
            if planned_target is not None:
                target_np = np.array(planned_target)
                distance_to_final_target = distance_to_final_target_pf # Update distance based on pathfinding
            # else: Keep original target_np if pathfinding returned None

        # Ensure orientation is valid if provided
        if orientation is not None:
            orientation = M.normalize_deg(orientation) # Normalize angle

        # Execute walk - ensure target_np is tuple if required by behavior
        self.behavior.execute("Walk", tuple(target_np), True, orientation, is_orientation_absolute, distance_to_final_target)


    # kick and kickTarget are deprecated, use newKickdef for ball interactions
    # Keep the stubs if other parts of the system might still call them initially
    def kick(self, *args, **kwargs):
        # print(f"Player {self.world.robot.unum}: Deprecated kick() called, use newKickdef()")
        
        # --- ADDED FOR PROXY (fallback) ---
        if self.fat_proxy_cmd is not None:
            self.kick_direction = 0 # Default aim forward
            return self.fat_proxy_kick()
        # ----------------------------------
            
        # Optionally, redirect to a basic move towards ball or do nothing
        return self.move(self.world.ball_abs_pos[:2]) # Example: move towards ball

    def kickTarget(self, *args, **kwargs):
        # print(f"Player {self.world.robot.unum}: Deprecated kickTarget() called, use newKickdef()")
         # Optionally, redirect to newKickdef with default aim
        strategyData = kwargs.get('strategyData', Strategy(self.world)) # Get strategyData if passed
        mypos_2d = kwargs.get('mypos_2d', strategyData.mypos)
        target_2d = kwargs.get('target_2d', (15.5, 0)) # Default aim
        
        # --- ADDED FOR PROXY (in case stub is called) ---
        if self.fat_proxy_cmd is not None:
            vector_to_target = np.array(target_2d) - np.array(mypos_2d)
            self.kick_distance = np.linalg.norm(vector_to_target)
            direction_radians = np.arctan2(vector_to_target[1], vector_to_target[0])
            self.kick_direction = np.degrees(direction_radians)
            return self.fat_proxy_kick()
        # ------------------------------------------------
            
        return self.newKickdef(strategyData, strategyData.player_unum, mypos_2d, strategyData.ball_2d, target_2d)


    def think_and_send(self):
        behavior = self.behavior
        # Ensure world object is valid before creating Strategy
        if self.world is None or self.world.robot is None:
             # print("World object not ready, skipping think cycle.")
             # Send a minimal command (e.g., stand still) or just return
             self.scom.commit_and_send( b"(he1 0)(he2 0)" ) # Example minimal command
             return

        try:
             strategyData = Strategy(self.world)
        except Exception as e:
             # print(f"Error creating Strategy object: {e}")
             self.scom.commit_and_send( b"(he1 0)(he2 0)" ) # Send minimal command on error
             return

        d = self.world.draw

        # --- Game State Logic ---
        if strategyData.play_mode == self.world.M_GAME_OVER:
            pass # Do nothing
        elif strategyData.PM_GROUP == self.world.MG_ACTIVE_BEAM:
            self.beam()
        elif strategyData.PM_GROUP == self.world.MG_PASSIVE_BEAM:
            self.beam(True) # avoid center circle
        
        # --- MODIFIED FOR PROXY ---
        elif self.state == 1 or (behavior.is_ready("Get_Up") and self.fat_proxy_cmd is None): # Check state first
        # --------------------------
            # Make sure Get_Up behavior exists and can be executed
            if hasattr(behavior, 'execute') and callable(getattr(behavior, 'execute')):
                 try:
                     self.state = 0 if behavior.execute("Get_Up") else 1
                 except Exception as e:
                     # print(f"Error executing Get_Up: {e}")
                     self.state = 0 # Assume recovered or reset state
            else:
                 # print("Behavior object cannot execute Get_Up.")
                 self.state = 0 # Reset state if behavior is problematic

        # --- Set Piece / Defensive Logic ---
        elif (strategyData.PM_GROUP == self.world.MG_THEIR_KICK): # Opponent's kick/corner/kickin etc.
             # All players go to initial positions (defensive posture)
             self.move(self.init_pos, orientation=strategyData.ball_dir)

        elif (strategyData.play_mode == self.world.M_OUR_KICKOFF):
             # Player 9 (example) takes kickoff - pass to cherry picker or shoot
             if strategyData.player_unum == 9:
                 cherry_picker_target = (10, 0) # Adjust based on actual cherry picker pos/role
                 # Check if cherry picker exists and pass if possible
                 cp_exists = len(strategyData.teammate_positions) > 10 and strategyData.teammate_positions[10] is not None
                 pass_target = strategyData.teammate_positions[10] if cp_exists else (15, 0) # Pass or shoot
                 self.newKickdef(strategyData, strategyData.player_unum, strategyData.mypos, strategyData.ball_2d, tuple(pass_target))
             else: # Others hold position or move slightly
                 self.move(self.init_pos, orientation=strategyData.ball_dir)

        elif (strategyData.play_mode == self.world.M_OUR_GOAL_KICK):
             # Player 1 (Goalie) takes goal kick - long kick towards goal or cherry picker
             if strategyData.player_unum == 1:
                 cherry_picker_target = (10, 0) # Adjust
                 cp_exists = len(strategyData.teammate_positions) > 10 and strategyData.teammate_positions[10] is not None
                 kick_target = strategyData.teammate_positions[10] if cp_exists else (15.5, 0) # Aim for CP or goal center
                 self.newKickdef(strategyData, strategyData.player_unum, strategyData.mypos, strategyData.ball_2d, tuple(kick_target))
             else: # Others spread out
                 self.move(self.init_pos, orientation=strategyData.ball_dir) # Simplified: just hold init pos

        # --- Normal Play Logic ---
        elif strategyData.play_mode != self.world.M_BEFORE_KICKOFF:
             self.select_skill(strategyData)
        else:
             pass # Before kickoff, do nothing or beam

        #--------------------------------------- 3. Broadcast
        if hasattr(self.radio, 'broadcast'): # Check if radio object exists and has broadcast method
             self.radio.broadcast()

        #--------------------------------------- 4. Send to server
        # --- MODIFIED FOR PROXY ---
        if self.fat_proxy_cmd is None: # normal behavior
            command = b"(he1 0)(he2 0)" # Default minimal command
            if hasattr(strategyData, 'robot_model') and hasattr(strategyData.robot_model, 'get_command'):
                try:
                    command = strategyData.robot_model.get_command()
                except Exception as e:
                    # print(f"Error getting command from robot model: {e}")
                    pass # Use default command
            self.scom.commit_and_send(command)
        else: # fat proxy behavior
            self.scom.commit_and_send( self.fat_proxy_cmd.encode() ) 
            self.fat_proxy_cmd = ""
        # --------------------------


    # --- Fast Dribble Function (Refined) ---
    def newKickdef(self, strategyData, MyNum=0, position=(0,0), ball_pos=(0,0), aim=(15.5, 0)):
        """
        Fast dribble/kick logic (Refined for stability and direction).
        Aligns behind the ball and moves through it.
        Uses potential fields for obstacle avoidance if aiming far and opponent is close.
        """
        # Ensure inputs are valid numpy arrays
        position = np.array(position)
        ball_pos = np.array(ball_pos)
        aim = np.array(aim)
        goal = aim # Target location (pass or shot)

        # Use potential fields to adjust aim if opponent is close and target is far
        if strategyData.min_opponent_ball_dist < 1.5 and np.linalg.norm(goal - position) > 5:
             potential_aim_tuple = strategyData.potential_fields_pathfinding(position, goal)
             if potential_aim_tuple: # Check if it's not None
                 aim = np.array(potential_aim_tuple) # Update aim only if valid

        # Calculate the position behind the ball, collinear with the aim point
        startat_tuple = strategyData.point_in_direction(ball_pos, aim, -0.25)
        startat = np.array(startat_tuple) if startat_tuple is not None else ball_pos # Fallback

        # --- SIMPLIFIED Alignment Phase ---
        current_dist_to_startat = np.linalg.norm(position - startat)
        aim_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(aim)
        alignment_tolerance = 0.3 # How close to 'startat' we need to be
        collinear_tolerance = 0.35 # How collinear we need to be

        # If not aligned (not collinear OR too far from 'startat' point)
        if current_dist_to_startat > alignment_tolerance or not strategyData.are_points_collinear(position, ball_pos, aim, tolerance=collinear_tolerance):
            strategyData.my_desired_position = tuple(startat) # Always aim for the startat point
            strategyData.my_desired_orientation = aim_orientation # Always face the kick target
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=True)
           
        # --- Dribble/Push Phase ---
        # If we are here, we are aligned and ready to push
        current_ball_dist = np.linalg.norm(position - ball_pos)

        if current_ball_dist > 0.25: # Need to get closer to ball
            strategyData.my_desired_position = tuple(ball_pos) # move expects tuple
            strategyData.my_desired_orientation = aim_orientation
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=True)

        else: # Close enough to ball, push through it
            # --- MODIFIED FOR PROXY ---
            # If we are in proxy mode, use the proxy_kick command instead of pushing
            if self.fat_proxy_cmd is not None:
                # Calculate absolute kick direction for fat_proxy_kick
                vector_to_target = aim - ball_pos # Use numpy arrays
                direction_radians = np.arctan2(vector_to_target[1], vector_to_target[0])
                self.kick_direction = np.degrees(direction_radians)
                self.kick_distance = np.linalg.norm(vector_to_target)
                return self.fat_proxy_kick()
            # --- END PROXY MODIFICATION ---
            
            # Original push logic
            towards_tuple = strategyData.point_in_direction(position, aim, 1.0)
            towards = np.array(towards_tuple) if towards_tuple is not None else aim # Fallback

            strategyData.my_desired_position = tuple(towards) # move expects tuple
            strategyData.my_desired_orientation = aim_orientation
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=False)


    def select_skill(self, strategyData):
        drawer = self.world.draw
        MyNum = strategyData.player_unum
        my_role = strategyData.my_role # Get role defined in Strategy.py (ensure this is set in Strategy.py)
        active_player = strategyData.active_player_unum
        position = strategyData.mypos # Current position tuple
        position_np = np.array(position) # Numpy array version for calculations
        ball_pos = strategyData.ball_2d # Ball position numpy array
        goal_target_tuple = (15.5, 0) # Opponent goal center tuple
        goal_target_np = np.array(goal_target_tuple) # Numpy array version
        our_goal_center_np = np.array([-15.5, 0])

        # --- Dynamic Formation Selection ---
        formation_positions = {} # Dictionary for assignments
        is_defending = False
        # Check opponent positions safely
        valid_opponents_exist = strategyData.opponent_positions and any(p is not None for p in strategyData.opponent_positions)

        # --- UPDATED TO USE strategyData ---
        if valid_opponents_exist and strategyData.min_opponent_ball_dist + 0.3 < strategyData.min_teammate_ball_dist:
             formation_positions = GenerateDefense(strategyData)
             is_defending = True
        else:
             formation_positions = GenerateOffense(strategyData)
        # ------------------------------------

        # Perform role assignment based on the chosen formation
        point_preferences = role_assignment(strategyData.teammate_positions, formation_positions)
        my_formation_spot = point_preferences.get(MyNum, self.init_pos) # Get assigned spot, fallback to init_pos


        # --- Tactical Foul Logic Removed ---


        # --- Role-Based Logic ---
        
        # --- POSITIONING LOGIC (Used by all roles when not active) ---
        def move_to_spot(spot, face_target):
            """
            Helper function for non-active player positioning.
            FIXES "TURNING BACKS" PROBLEM.
            """
            target_pos = tuple(spot)
            face_target_pos = np.array(face_target)
            target_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(face_target_pos)
            dist_to_spot = np.linalg.norm(position_np - np.array(spot))

            # If far from spot, face movement direction (orientation=None)
            # If close to spot (e.g., < 0.5m), face the ball/target
            final_orientation = target_orientation if dist_to_spot < 0.5 else None
            
            return self.move(target_pos, orientation=final_orientation, avoid_obstacles=True)
        # --- END HELPER ---


        # 1. GOALIE LOGIC (Player 1)
        if my_role == 'GOALIE':
            goalie_rest_pos = np.array([-14, 0])
            threat_distance = 7.0

            if active_player == MyNum:
                 # Pass forward using newKickdef
                 best_pass_target, _ = pass_reciever_selector(MyNum, strategyData.teammate_positions, strategyData.opponent_positions, goal_target_tuple)
                 pass_aim = np.array(best_pass_target) if best_pass_target is not None else goal_target_np
                 return self.newKickdef(strategyData, MyNum, position_np, ball_pos, pass_aim)
            elif np.linalg.norm(ball_pos - our_goal_center_np) < threat_distance:
                 # Intercept logic (simplified: move between ball and goal center y-clamped)
                 intercept_y = np.clip(ball_pos[1], -1.5, 1.5) # Clamp Y near goal posts
                 intercept_pos = (goalie_rest_pos[0], intercept_y)
                 strategyData.my_desired_position = intercept_pos
                 strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos)
                 return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=False)
            else:
                 # Return to rest pos (dynamic spot from formation)
                 return move_to_spot(my_formation_spot, ball_pos)

        # 2. CHERRY-PICKER LOGIC (Player 11)
        elif my_role == 'CHERRY_PICKER':
            if active_player == MyNum:
                 # Shoot using newKickdef
                 return self.newKickdef(strategyData, MyNum, position_np, ball_pos, goal_target_np)
            else:
                 # Go to spot, face ball
                 return move_to_spot(my_formation_spot, ball_pos)

        # 3. DEFENDER LOGIC (Players 2, 3, 4)
        elif my_role == 'DEFENDER':
            if active_player == MyNum:
                 # Pass forward using newKickdef, prioritizing Cherry Picker
                 cp_pos = strategyData.teammate_positions[10] if len(strategyData.teammate_positions) > 10 else None
                 best_pass, second_best = pass_reciever_selector(MyNum, strategyData.teammate_positions, strategyData.opponent_positions, goal_target_tuple, priority_target=cp_pos)
                 pass_aim = np.array(best_pass) if best_pass is not None else (np.array(second_best) if second_best is not None else goal_target_np)
                 return self.newKickdef(strategyData, MyNum, position_np, ball_pos, pass_aim)
            else:
                 # Go to assigned formation spot
                 return move_to_spot(my_formation_spot, ball_pos)

        # 4. MIDFIELDER LOGIC (Players 5, 6, 7, 8, 9, 10)
        elif my_role == 'MIDFIELDER':
            if active_player == MyNum:
                 # Pass to Cherry Picker > Pass Forward > Dribble/Shoot using newKickdef
                 cp_pos = strategyData.teammate_positions[10] if len(strategyData.teammate_positions) > 10 else None
                 best_pass, second_best = pass_reciever_selector(MyNum, strategyData.teammate_positions, strategyData.opponent_positions, goal_target_tuple, priority_target=cp_pos)

                 pass_aim = goal_target_np # Default to shooting
                 if best_pass is not None:
                     pass_aim = np.array(best_pass)
                 elif second_best is not None:
                     pass_aim = np.array(second_best)

                 return self.newKickdef(strategyData, MyNum, position_np, ball_pos, pass_aim)
            else:
                 # Go to assigned formation spot
                 return move_to_spot(my_formation_spot, ball_pos)

        # Fallback if role is undefined
        else:
             # Default to moving to formation spot
             return move_to_spot(my_formation_spot, ball_pos)


    # --- ADDED FAT PROXY METHODS ---

    def fat_proxy_kick(self):
        w = self.world
        r = self.world.robot 
        ball_2d = w.ball_abs_pos[:2]
        my_head_pos_2d = r.loc_head_position[:2]

        if np.linalg.norm(ball_2d - my_head_pos_2d) < 0.25:
            # fat proxy kick arguments: power [0,10]; relative horizontal angle [-180,180]; vertical angle [0,70]
            self.fat_proxy_cmd += f"(proxy kick 10 {M.normalize_deg( self.kick_direction - r.imu_torso_orientation ):.2f} 20)" 
            self.fat_proxy_walk = np.zeros(3) # reset fat proxy walk
            return True
        else:
            # Fixed syntax: ball_2d - np.array([-0.1, 0]) moves to (ball_x + 0.1, ball_y)
            self.fat_proxy_move(ball_2d - np.array([-0.1, 0]), None, True) # ignore obstacles
            return False


    def fat_proxy_move(self, target_2d, orientation, is_orientation_absolute):
        r = self.world.robot

        target_dist = np.linalg.norm(target_2d - r.loc_head_position[:2])
        target_dir = M.target_rel_angle(r.loc_head_position[:2], r.imu_torso_orientation, target_2d)

        if target_dist > 0.1 and abs(target_dir) < 8:
            self.fat_proxy_cmd += (f"(proxy dash {100} {0} {0})")
            return

        if target_dist < 0.1:
            if orientation is None: # Handle case where orientation is None
                target_dir = 0
            elif is_orientation_absolute:
                orientation = M.normalize_deg( orientation - r.imu_torso_orientation )
                target_dir = np.clip(orientation, -60, 60)
            else: # Orientation is relative
                target_dir = np.clip(orientation, -60, 60)
            self.fat_proxy_cmd += (f"(proxy dash {0} {0} {target_dir:.1f})")
        else:
            self.fat_proxy_cmd += (f"(proxy dash {20} {0} {target_dir:.1f})")