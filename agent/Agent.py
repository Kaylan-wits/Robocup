from agent.Base_Agent import Base_Agent
from math_ops.Math_Ops import Math_Ops as M
import math
import numpy as np

# Corrected imports for Assignment
from strategy.Assignment import role_assignment
from strategy.Assignment import find_safe_pass_target

# Strategy and Formation imports
from strategy.Strategy import Strategy
from formation.Formation import GeneratePlayOn
from formation.Formation import GenerateDefense


class Agent(Base_Agent):
    def __init__(self, host:str, agent_port:int, monitor_port:int, unum:int,
                 team_name:str, enable_log, enable_draw, wait_for_server=True, is_fat_proxy=False) -> None:

        # define robot type based on unum (assuming 5 players, adjust if needed)
        # Using a simple mapping for 5 players: 0=GK, 1,2=DEF, 3=MID, 4=FWD
        # You might need to adjust this based on your desired robot types
        robot_type = (0, 1, 1, 2, 4)[unum-1] if unum <= 5 else 0 # Default type 0 if unum > 5

        # Initialize base agent
        super().__init__(host, agent_port, monitor_port, unum, robot_type, team_name, enable_log, enable_draw, True, wait_for_server, None)

        self.enable_draw = enable_draw
        self.state = 0  # 0-Normal, 1-Getting up, 2-Kicking
        self.kick_direction = 0
        self.kick_distance = 0
        self.fat_proxy_cmd = "" if is_fat_proxy else None
        self.fat_proxy_walk = np.zeros(3) # filtered walk parameters for fat proxy

        # Define initial positions for 5 players (adjust as needed)
        # Using the base 5v5 attack formation positions
        self.init_pos = [
            (-14, 0),   # Goalkeeper
            (-7, 0),    # Central Defender
            (1, 0),     # Central Midfielder
            (8, -4),    # Left Forward
            (8, 4)      # Right Forward
        ][unum-1] if unum <= 5 else (-100,-100) # Dummy pos if unum > 5

        # Caching variables
        self.last_assignment_time_ms = 0
        self.cached_point_preferences = None
        self.last_formation_mode = "attack" # Start in attack mode

    def beam(self, avoid_center_circle=False):
        r = self.world.robot
        # Ensure init_pos is a mutable list for modification
        pos = list(self.init_pos[:]) # copy position tuple/list and make it a list
        self.state = 0

        # Safety check: Robot position might be None initially
        robot_pos = r.loc_head_position[:2] if r.loc_head_position is not None else (0,0)

        # Avoid center circle by moving the player back
        if avoid_center_circle and np.linalg.norm(self.init_pos) < 2.5:
            pos[0] = -2.3

        if np.linalg.norm(np.array(pos) - np.array(robot_pos)) > 0.1 or self.behavior.is_ready("Get_Up"):
             # Calculate angle safely
             angle_target = (-pos[0], -pos[1])
             beam_angle = M.vector_angle(angle_target) if not (pos[0] == 0 and pos[1] == 0) else 0.0
             self.scom.commit_beam(pos, beam_angle)
        else:
            if self.fat_proxy_cmd is None: # normal behavior
                self.behavior.execute("Zero_Bent_Knees_Auto_Head")
            else: # fat proxy behavior
                self.fat_proxy_cmd += "(proxy dash 0 0 0)"
                self.fat_proxy_walk = np.zeros(3) # reset fat proxy walk

    def move(self, target_2d=(0,0), orientation=None, is_orientation_absolute=True,
             avoid_obstacles=True, priority_unums=[], is_aggressive=False, timeout=3000):
        ''' Walk to target position '''
        r = self.world.robot
        # Safety check: Robot position might be None
        robot_pos = r.loc_head_position[:2] if r.loc_head_position is not None else (0,0)

        if self.fat_proxy_cmd is not None: # fat proxy behavior
            self.fat_proxy_move(target_2d, orientation, is_orientation_absolute)
            return

        if avoid_obstacles:
            target_2d, _, distance_to_final_target = self.path_manager.get_path_to_target(
                target_2d, priority_unums=priority_unums, is_aggressive=is_aggressive, timeout=timeout)
        else:
            distance_to_final_target = np.linalg.norm(np.array(target_2d) - np.array(robot_pos))

        # Ensure target_2d is valid before executing walk
        if target_2d is None:
            # Fallback if pathfinding fails or target is invalid
            target_2d = robot_pos # Move to current position (stand still)
            distance_to_final_target = 0.0

        self.behavior.execute("Walk", target_2d, True, orientation, is_orientation_absolute, distance_to_final_target)

    # Note: Simplified kick function - primarily uses kickTarget now
    def kick(self, kick_direction=None, kick_distance=None, abort=False, enable_pass_command=False):
        ''' Basic kick behavior trigger - often superseded by kickTarget '''
        # Defaulting to Basic_Kick if called directly
        self.kick_direction = self.kick_direction if kick_direction is None else kick_direction
        return self.behavior.execute("Basic_Kick", self.kick_direction, abort)

    def kickTarget(self, strategyData, mypos_2d=(0,0),target_2d=(0,0), abort=False, enable_pass_command=False):
        ''' Calculate direction and execute basic kick '''
        # Safety checks for positions
        if mypos_2d is None or target_2d is None:
            return self.behavior.execute("Zero_Bent_Knees_Auto_Head") # Stand still if positions invalid

        vector_to_target = np.array(target_2d) - np.array(mypos_2d)
        kick_distance = np.linalg.norm(vector_to_target)

        # Handle zero vector case
        if kick_distance == 0:
            kick_direction = 0.0
        else:
            direction_radians = np.arctan2(vector_to_target[1], vector_to_target[0])
            kick_direction = np.degrees(direction_radians)

        # min_opponent_ball_dist might not exist if Strategy failed, add check
        if hasattr(strategyData, 'min_opponent_ball_dist') and strategyData.min_opponent_ball_dist < 1.45 and enable_pass_command:
            self.scom.commit_pass_command()

        self.kick_direction = kick_direction # Use calculated direction

        if self.fat_proxy_cmd is None: # normal behavior
            return self.behavior.execute("Basic_Kick", self.kick_direction, abort)
        else: # fat proxy behavior
            return self.fat_proxy_kick() # Fat proxy kick handles its own logic

    # --- SIMPLE AGGRESSIVE DRIBBLE ---
    def dribbleToTarget(self, strategyData, MyNum=0, position=(0,0), ball_pos=(0.0), aim=(15.5,0)):
        """
        A simple, aggressive dribble function.
        1. Get behind the ball (relative to the aim point).
        2. Push the ball towards the aim point.
        """
        # Safety checks
        if position is None or ball_pos is None or aim is None:
             return self.move(self.init_pos) # Go to init pos if data invalid

        goal_target = (15.5, -0.5) # Aim for bottom corner

        position_behind_ball = strategyData.point_in_direction(ball_pos, goal_target, -0.2)
        # Handle case where point_in_direction might fail
        if position_behind_ball is None: position_behind_ball = ball_pos

        dist_to_ideal_spot = strategyData.distance(position, position_behind_ball)

        # ball_dist might not exist if Strategy failed
        current_ball_dist = strategyData.ball_dist if hasattr(strategyData, 'ball_dist') else float('inf')

        if current_ball_dist > 0.4 or dist_to_ideal_spot > 0.3:
            # Move to the "ideal spot" behind the ball.
            strategyData.my_desired_position = (position_behind_ball)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=True)
        else:
            # Move straight through the ball to the goal.
            strategyData.my_desired_position = (goal_target)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(goal_target)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=False)
    # --- END OF SIMPLE DRIBBLE ---

    # --- CORRECTED think_and_send ---
    def think_and_send(self):
        behavior = self.behavior
        # --- Use try-except for Strategy creation ---
        try:
            strategyData = Strategy(self.world)
        except Exception as e:
            # If Strategy creation fails, log error and stand still
            print(f"Error creating Strategy object: {e}")
            if self.fat_proxy_cmd is None:
                 self.behavior.execute("Zero_Bent_Knees_Auto_Head")
                 self.scom.commit_and_send(self.world.robot.get_command())
            else:
                 self.fat_proxy_cmd += "(proxy dash 0 0 0)"
                 self.scom.commit_and_send(self.fat_proxy_cmd.encode())
                 self.fat_proxy_cmd = ""
            return # Exit function early
        # --- End try-except ---

        d = self.world.draw

        # Convert None positions to a default far-away location AFTER Strategy creation
        default_pos = np.array([-100.0, -100.0])
        # Check if attributes exist before list comprehension
        if hasattr(strategyData, 'teammate_positions'):
            strategyData.teammate_positions = [pos if pos is not None else default_pos for pos in strategyData.teammate_positions]
        else:
            strategyData.teammate_positions = [default_pos] * 5 # Placeholder

        if hasattr(strategyData, 'opponent_positions'):
             strategyData.opponent_positions = [pos if pos is not None else default_pos for pos in strategyData.opponent_positions]
        else:
             strategyData.opponent_positions = [default_pos] * 5 # Placeholder


        # --- Main Logic Flow ---
        if strategyData.play_mode == self.world.M_GAME_OVER:
            pass # Do nothing
        elif strategyData.PM_GROUP == self.world.MG_ACTIVE_BEAM:
            self.beam()
        elif strategyData.PM_GROUP == self.world.MG_PASSIVE_BEAM:
            self.beam(True) # avoid center circle
        elif self.state == 1 or (behavior.is_ready("Get_Up") and self.fat_proxy_cmd is None):
            self.state = 0 if behavior.execute("Get_Up") else 1

        # --- Corrected Kick-off and Other Modes Logic ---
        elif (strategyData.play_mode == self.world.M_OUR_KICKOFF):
            # Player 3 (Central Mid) kicks, Player 4 receives
            if strategyData.robot_model.unum == 3:
                pass_target = (0.5, -1.0)
                self.kickTarget(strategyData, strategyData.mypos, pass_target)
            elif strategyData.robot_model.unum == 4:
                receive_spot = (0.5, -1.0)
                self.move(receive_spot, orientation=strategyData.ball_dir)
            else: # Players 1, 2, 5
                self.move(self.init_pos, orientation=strategyData.ball_dir)

        elif (strategyData.play_mode == self.world.M_OUR_GOAL_KICK):
            # Goalie (Player 1) kicks
            if strategyData.robot_model.unum == 1:
                self.kickTarget(strategyData,strategyData.mypos,(5, 5)) # Pass to defender
            else: # Players 2, 3, 4, 5
                self.move(self.init_pos, orientation=strategyData.ball_dir)

        elif (strategyData.PM_GROUP == self.world.MG_THEIR_KICK):
            # Player 3 (Central Mid) intercepts
            if strategyData.robot_model.unum == 3:
                intercept_pos = (1.6, 0.0)
                self.move(intercept_pos, orientation=strategyData.ball_dir)
            else: # Players 1, 2, 4, 5
                self.move(self.init_pos, orientation=strategyData.ball_dir)

        elif (strategyData.play_mode == self.world.M_PLAY_ON):
             # Only run select_skill in Play On
            self.select_skill(strategyData)

        else:
            # Catches M_BEFORE_KICKOFF, KickIn, CornerKick etc.
            # Default: Hold initial position
            self.move(self.init_pos, orientation=strategyData.ball_dir)
        # --- End Corrected Logic ---

        #--------------------------------------- 3. Broadcast
        self.radio.broadcast()

        #--------------------------------------- 4. Send to server
        if self.fat_proxy_cmd is None: # normal behavior
             # Safety check for get_command result
             command = strategyData.robot_model.get_command()
             if command is not None:
                  self.scom.commit_and_send(command)
             # else: print("Warning: get_command returned None") # Optional debug
        else: # fat proxy behavior
            self.scom.commit_and_send( self.fat_proxy_cmd.encode() )
            self.fat_proxy_cmd = ""

    # --- select_skill with "Shoot > Pass > Dribble" ---
    def select_skill(self,strategyData):
        drawer = self.world.draw
        path_draw_options = self.path_manager.draw_options # Assuming this exists

        target = (15,0) # Opponents Goal (General target)
        NUM_PLAYERS_ON_TEAM = 5

        #------------------------------------------------------
        # Role Assignment Caching
        current_time_ms = self.world.time_local_ms # Assuming world has time
        current_formation_mode = "attack" # Default

        visible_opponents = [pos for pos in strategyData.opponent_positions if pos[0] != -100.0]

        # Use safe attribute access
        min_opp_dist = strategyData.min_opponent_ball_dist if hasattr(strategyData,'min_opponent_ball_dist') else float('inf')
        min_team_dist = strategyData.min_teammate_ball_dist if hasattr(strategyData,'min_teammate_ball_dist') else float('inf')

        if len(visible_opponents) > 0 and (min_opp_dist + 1.0 < min_team_dist):
            current_formation_mode = "defense"
        else:
            current_formation_mode = "attack"

        if (current_time_ms - self.last_assignment_time_ms > 2000) or \
           (current_formation_mode != self.last_formation_mode) or \
           (self.cached_point_preferences is None):

            self.last_assignment_time_ms = current_time_ms
            self.last_formation_mode = current_formation_mode

            formation_positions = []
            if current_formation_mode == "defense":
                formation_positions = GenerateDefense(visible_opponents)
                if drawer: drawer.annotation((0,10.5), "Mode: DEFENSE" , drawer.Color.red, "status")
            else: # Attack
                formation_positions = GeneratePlayOn(strategyData.ball_2d[0])
                if drawer: drawer.annotation((0,10.5), "Mode: ATTACK / PLAY ON" , drawer.Color.green, "status")

            # Padding Logic (Corrected for safety)
            current_teammates = strategyData.teammate_positions
            # Ensure current_teammates is a list
            if not isinstance(current_teammates, list): current_teammates = []
            valid_teammates = [pos for pos in current_teammates if pos is not None and not np.array_equal(pos, np.array([-100.0, -100.0]))]
            num_teammates = len(valid_teammates)
            dummy_pos = np.array([-100.0, -100.0])

            if num_teammates < NUM_PLAYERS_ON_TEAM:
                padded_teammates = valid_teammates + [dummy_pos] * (NUM_PLAYERS_ON_TEAM - num_teammates)
            else:
                padded_teammates = valid_teammates[:NUM_PLAYERS_ON_TEAM]

            current_formation = formation_positions
            if not isinstance(current_formation, list): current_formation = [] # Ensure list
            num_formation = len(current_formation)
            if num_formation < NUM_PLAYERS_ON_TEAM:
                padded_formation = current_formation + [dummy_pos] * (NUM_PLAYERS_ON_TEAM - num_formation)
            else:
                padded_formation = current_formation[:NUM_PLAYERS_ON_TEAM]

            # Run assignment safely
            try:
                 self.cached_point_preferences = role_assignment(padded_teammates, padded_formation)
            except Exception as e:
                 print(f"Error during role assignment: {e}")
                 # Fallback: Assign players to initial positions if assignment fails
                 self.cached_point_preferences = {i+1: self.init_pos for i in range(NUM_PLAYERS_ON_TEAM)}


        # Use cached preferences safely
        point_preferences = self.cached_point_preferences
        if point_preferences is None:
             # Failsafe if cache somehow still None
             return self.move(self.init_pos, orientation=strategyData.ball_dir)

        # --- "Shoot > Pass > Dribble" LOGIC ---
        # Use safe attribute access for active player check
        active_unum = strategyData.active_player_unum if hasattr(strategyData,'active_player_unum') else 1

        if active_unum == strategyData.robot_model.unum: # I am the active player
            if drawer: drawer.annotation((0,10.5), "Role: ACTIVE" , drawer.Color.yellow, "status")

            goal_target = (15.5, -0.5) # Aim bottom corner

            # --- 1. CAN I SHOOT? ---
            if strategyData.distance(strategyData.mypos, goal_target) < 8.0 and strategyData.mypos[0] > 9.0:
                if drawer: drawer.annotation((0,9.5), "Status: SHOOTING" , drawer.Color.green, "status_2")
                return self.kickTarget(strategyData, strategyData.mypos, goal_target)

            # --- 2. CAN I MAKE A SAFE PASS? ---
            safe_target = find_safe_pass_target(
                strategyData.player_unum,
                strategyData.mypos,
                strategyData.teammate_positions, # Already filtered None/dummy
                strategyData.opponent_positions # Already filtered None/dummy
            )

            if (safe_target is not None):
                if drawer:
                    drawer.annotation((0,9.5), "Status: PASSING" , drawer.Color.green, "status_2")
                    drawer.line(strategyData.mypos, safe_target, 2, drawer.Color.green,"safe_pass")
                return self.kickTarget(strategyData, strategyData.mypos, safe_target)

            # --- 3. IF NOT, DRIBBLE ---
            else:
                if drawer:
                    drawer.annotation((0,9.5), "Status: DRIBBLING" , drawer.Color.blue, "status_2")
                    drawer.clear("safe_pass")
                return self.dribbleToTarget(strategyData, strategyData.player_unum, strategyData.mypos, strategyData.ball_2d, goal_target)

        else: # I am NOT the active player
            if drawer: drawer.clear_player() # Clear personal drawings

            # Move to assigned formation position safely
            my_target_pos = self.init_pos # Default to init_pos
            if strategyData.player_unum in point_preferences:
                # Ensure the preference is not None before assigning
                pref = point_preferences[strategyData.player_unum]
                if pref is not None:
                     my_target_pos = pref

            # Use safe ball_dir access
            orient = strategyData.ball_dir if hasattr(strategyData, 'ball_dir') else 0.0
            return self.move(my_target_pos, orientation=orient)

    #--------------------------------------- Fat proxy auxiliary methods (UNCHANGED)
    def fat_proxy_kick(self):
        w = self.world
        r = self.world.robot
        # Add safety checks
        ball_2d = w.ball_abs_pos[:2] if w.ball_abs_pos is not None else (0,0)
        my_head_pos_2d = r.loc_head_position[:2] if r.loc_head_position is not None else (0,0)
        imu_ori = r.imu_torso_orientation if r.imu_torso_orientation is not None else 0.0

        if np.linalg.norm(np.array(ball_2d) - np.array(my_head_pos_2d)) < 0.25:
            self.fat_proxy_cmd += f"(proxy kick 10 {M.normalize_deg( self.kick_direction - imu_ori ):.2f} 20)"
            self.fat_proxy_walk = np.zeros(3)
            return True
        else:
            # Calculate target safely
            target = np.array(ball_2d) - np.array([-0.1, 0])
            self.fat_proxy_move(tuple(target), None, True) # Convert back to tuple
            return False

    def fat_proxy_move(self, target_2d, orientation, is_orientation_absolute):
        r = self.world.robot
        # Add safety checks
        robot_pos = r.loc_head_position[:2] if r.loc_head_position is not None else (0,0)
        imu_ori = r.imu_torso_orientation if r.imu_torso_orientation is not None else 0.0
        if target_2d is None: target_2d = robot_pos # Fallback if target is None

        target_dist = np.linalg.norm(np.array(target_2d) - np.array(robot_pos))
        target_dir = M.target_rel_angle(robot_pos, imu_ori, target_2d)

        if target_dist > 0.1 and abs(target_dir) < 8:
            self.fat_proxy_cmd += (f"(proxy dash {100} {0} {0})")
            return

        if target_dist < 0.1:
            if is_orientation_absolute:
                 # Safety check for orientation
                 if orientation is None: orientation = imu_ori # Use current if None
                 orientation = M.normalize_deg( orientation - imu_ori )
            # Safety check for orientation if it became None
            if orientation is None: orientation = 0.0
            target_dir = np.clip(orientation, -60, 60)
            self.fat_proxy_cmd += (f"(proxy dash {0} {0} {target_dir:.1f})")
        else:
            self.fat_proxy_cmd += (f"(proxy dash {20} {0} {target_dir:.1f})")