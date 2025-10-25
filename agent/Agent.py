from agent.Base_Agent import Base_Agent
from math_ops.Math_Ops import Math_Ops as M
import math
import numpy as np

# Updated imports
from strategy.Assignment import role_assignment
from strategy.Assignment import pass_reciever_selector # Added from muzzaam/test34
from strategy.Strategy import Strategy 

# Updated imports
from formation.Formation import GeneratePlayOn # Renamed from GenerateBasicFormation
from formation.Formation import GenerateDefense # Added from muzzaam/test34


class Agent(Base_Agent):
    def __init__(self, host:str, agent_port:int, monitor_port:int, unum:int,
                 team_name:str, enable_log, enable_draw, wait_for_server=True, is_fat_proxy=False) -> None:
        
        robot_type = (0,1,1,1,2,3,3,3,4,4,4)[unum-1] # Using 11 player numbers from amaan-hans

        super().__init__(host, agent_port, monitor_port, unum, robot_type, team_name, enable_log, enable_draw, True, wait_for_server, None)

        self.enable_draw = enable_draw
        self.state = 0
        self.kick_direction = 0
        self.kick_distance = 0
        self.fat_proxy_cmd = "" if is_fat_proxy else None
        self.fat_proxy_walk = np.zeros(3) 

        # Using 11 player initial positions from amaan-hans
        self.init_pos = ([-14,0],[-9,-5],[-9,0],[-9,5],[-5,-5],[-5,0],[-5,5],[-2,-6],[-2,-2.5],[-2,2.5],[-2,6])[unum-1]


    def beam(self, avoid_center_circle=False):
        # (Beam logic remains mostly the same as baseline)
        r = self.world.robot
        pos = self.init_pos[:] 
        self.state = 0

        if avoid_center_circle and np.linalg.norm(self.init_pos) < 2.5:
            pos[0] = -2.3 

        if np.linalg.norm(pos - r.loc_head_position[:2]) > 0.1 or self.behavior.is_ready("Get_Up"):
            self.scom.commit_beam(pos, M.vector_angle((-pos[0],-pos[1]))) 
        else:
            if self.fat_proxy_cmd is None:
                self.behavior.execute("Zero_Bent_Knees_Auto_Head")
            else: 
                self.fat_proxy_cmd += "(proxy dash 0 0 0)"
                self.fat_proxy_walk = np.zeros(3)


    def move(self, target_2d=(0,0), orientation=None, is_orientation_absolute=True,
             avoid_obstacles=True, priority_unums=[], is_aggressive=False, timeout=3000):
        # (Move logic remains the same as baseline)
        r = self.world.robot
        if self.fat_proxy_cmd is not None: 
            self.fat_proxy_move(target_2d, orientation, is_orientation_absolute)
            return

        if avoid_obstacles:
            target_2d, _, distance_to_final_target = self.path_manager.get_path_to_target(
                target_2d, priority_unums=priority_unums, is_aggressive=is_aggressive, timeout=timeout)
        else:
            distance_to_final_target = np.linalg.norm(target_2d - r.loc_head_position[:2])

        self.behavior.execute("Walk", target_2d, True, orientation, is_orientation_absolute, distance_to_final_target)

    # Note: We are keeping kickTarget for compatibility, but primarily using newKickdef logic
    def kickTarget(self, strategyData, mypos_2d=(0,0),target_2d=(0,0), abort=False, enable_pass_command=False):
        # Simplified kickTarget - it will now mostly rely on the logic within newKickdef
        # Calculate direction for compatibility if newKickdef needs it
        vector_to_target = np.array(target_2d) - np.array(mypos_2d)
        kick_direction = np.degrees(np.arctan2(vector_to_target[1], vector_to_target[0]))
        
        # --- Directly call the fast dribble/kick logic ---
        return self.newKickdef(strategyData, strategyData.player_unum, mypos_2d, strategyData.ball_2d, tuple(target_2d))

    def think_and_send(self):
        behavior = self.behavior
        strategyData = Strategy(self.world)
        d = self.world.draw

        # --- Game Mode Logic ---
        if strategyData.play_mode == self.world.M_GAME_OVER:
            pass # Do nothing
        elif strategyData.PM_GROUP == self.world.MG_ACTIVE_BEAM:
            self.beam()
        elif strategyData.PM_GROUP == self.world.MG_PASSIVE_BEAM:
            self.beam(True) # avoid center circle
        elif self.state == 1 or (behavior.is_ready("Get_Up") and self.fat_proxy_cmd is None):
            self.state = 0 if behavior.execute("Get_Up") else 1 # Getting up state handling
        
        # --- Set Piece Logic (from muzzaam/test34 & amaan-hans) ---
        elif (strategyData.PM_GROUP == self.world.MG_THEIR_KICK): # If opponent has any kick
            # All players go defensive
            formation_positions = GenerateDefense(strategyData.opponent_positions)
            point_preferences = role_assignment(strategyData.teammate_positions, formation_positions)
            my_defensive_pos = point_preferences.get(strategyData.player_unum, self.init_pos) # Default to init_pos if assignment fails
            self.move(my_defensive_pos, orientation=strategyData.ball_dir) # Go to defensive spot, face ball
        
        elif (strategyData.play_mode == self.world.M_OUR_KICKOFF):
            # Aggressive kickoff: Player 10 passes forward immediately to player 9 (or cherry-picker if defined)
            if strategyData.player_unum == 10: # Assuming player 10 takes kickoff
                 # Find player 9's position, or default forward
                 target_player_pos = strategyData.teammate_positions[8] if strategyData.teammate_positions[8] is not None else (5, 0) 
                 # Use newKickdef for the kickoff pass/dribble
                 self.newKickdef(strategyData, strategyData.player_unum, strategyData.mypos, strategyData.ball_2d, tuple(target_player_pos))
            else:
                 self.move(self.init_pos, orientation=strategyData.ball_dir) # Others hold position initially

        elif (strategyData.play_mode == self.world.M_OUR_GOAL_KICK):
             # Aggressive Goal Kick: Goalie (Player 1) tries to score directly
             if strategyData.player_unum == 1:
                 goal_target = (15.5, 0) # Opponent goal center
                 self.newKickdef(strategyData, strategyData.player_unum, strategyData.mypos, strategyData.ball_2d, goal_target)
             else:
                 # Other players move to offensive formation spots
                 formation_positions = GeneratePlayOn()
                 point_preferences = role_assignment(strategyData.teammate_positions, formation_positions)
                 my_offensive_pos = point_preferences.get(strategyData.player_unum, self.init_pos)
                 self.move(my_offensive_pos, orientation=strategyData.ball_dir) # Go to spot, face ball

        # --- Tactical Foul Logic ---
        elif strategyData.should_commit_tactical_foul():
            foul_target_opponent = strategyData.get_tactical_foul_target()
            if foul_target_opponent is not None:
                # Move aggressively into the back of the target opponent
                # Calculate position slightly behind the opponent
                foul_move_target = strategyData.point_in_direction(foul_target_opponent, strategyData.mypos, -0.5) 
                self.move(foul_move_target, avoid_obstacles=False, is_aggressive=True)
            else:
                 # If no suitable target, fall back to normal play
                 if strategyData.play_mode != self.world.M_BEFORE_KICKOFF:
                    self.select_skill(strategyData)
                 else:
                     pass # Do nothing before kickoff
        
        # --- Default Play On Logic ---
        else:
            if strategyData.play_mode != self.world.M_BEFORE_KICKOFF:
                self.select_skill(strategyData)
            else:
                pass # Do nothing before kickoff

        self.radio.broadcast()

        if self.fat_proxy_cmd is None:
            self.scom.commit_and_send( strategyData.robot_model.get_command() )
        else: 
            self.scom.commit_and_send( self.fat_proxy_cmd.encode() ) 
            self.fat_proxy_cmd = ""

    # --- Fast Dribble Function (from amaan-hans) ---
    def newKickdef(self, strategyData, MyNum=0, position=(0,0), ball_pos=(0,0), aim=(15.5, 0)):
        """
        Fast dribble/kick logic. Aligns behind the ball and moves through it.
        Uses potential fields for obstacle avoidance if aiming far and opponent is close.
        """
        goal = aim # Target location (pass or shot)
        
        # Use potential fields to adjust aim if opponent is close and target is far
        if strategyData.min_opponent_ball_dist < 1.5 and strategyData.distance(position, goal) > 5:
             aim = strategyData.potential_fields_pathfinding(position, goal)

        # Calculate the position behind the ball, collinear with the aim point
        startat = strategyData.point_in_direction(ball_pos, aim, -0.25) # Slightly adjust distance 

        # If far from alignment spot, navigate around ball if necessary
        if strategyData.distance(position, startat) > 0.6: # Increased distance threshold
            startat = strategyData.next_position_to_startat(aim, ball_pos, position, startat)
            # Move towards the calculated 'startat' position, facing the ball
            strategyData.my_desired_position = tuple(startat)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos) # Face ball while aligning
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=True) # Avoid obstacles when aligning

        # If not collinear (within tolerance), move to the alignment spot 'startat'
        elif not strategyData.are_points_collinear(position, ball_pos, aim, tolerance=0.5): # Increased tolerance
            strategyData.my_desired_position = tuple(startat)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos) # Face ball
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=True)

        # If collinear but still too far from the ball, move closer to the ball
        elif strategyData.ball_dist > 0.35: # Slightly increased ball distance threshold
            strategyData.my_desired_position = tuple(ball_pos)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(aim) # Face target
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=True) # Avoid obstacles approaching ball

        # If collinear and close enough, execute the "fast dribble" by moving through the ball
        else: 
            # Calculate a point well beyond the target to ensure moving through the ball
            towards = strategyData.point_in_direction(position, aim, 4) # Move 4m in the target direction
            strategyData.my_desired_position = tuple(towards)
            # Maintain orientation towards the final aim point
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(aim) 
            # IMPORTANT: Disable obstacle avoidance to move through the ball
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=False)


    def select_skill(self, strategyData):
        drawer = self.world.draw
        MyNum = strategyData.player_unum
        my_role = strategyData.my_role # Get role defined in Strategy.py
        active_player = strategyData.active_player_unum
        position = strategyData.mypos
        ball_pos = strategyData.ball_2d
        goal_target = (15.5, 0) # Center of opponent goal

        # --- Dynamic Formation Selection (from muzzaam/test34) ---
        formation_positions = []
        is_defending = False
        # Use opponent positions only if the list is not empty
        # Make sure opponent_positions is not None before checking its contents
        if strategyData.opponent_positions and any(pos is not None for pos in strategyData.opponent_positions):
            if strategyData.min_opponent_ball_dist + 0.3 < strategyData.min_teammate_ball_dist:
                formation_positions = GenerateDefense(strategyData.opponent_positions)
                is_defending = True
            else:
                formation_positions = GeneratePlayOn()
        else: # Default to PlayOn if no opponent data
             formation_positions = GeneratePlayOn()

        point_preferences = role_assignment(strategyData.teammate_positions, formation_positions)
        my_formation_spot = point_preferences.get(MyNum, self.init_pos) # Default to init_pos if assignment fails


        # --- Role-Based Logic ---

        # 1. GOALIE LOGIC (Player 1)
        if my_role == 'GOALIE':
            goalie_rest_pos = (-14, 0)
            threat_distance = 7.0 # How close ball must be for goalie to engage

            if active_player == MyNum: # Goalie has the ball
                 # Pass to the furthest forward teammate who is open
                 best_pass_target, _ = pass_reciever_selector(MyNum, strategyData.teammate_positions, strategyData.opponent_positions, goal_target)
                 if best_pass_target is not None:
                     return self.newKickdef(strategyData, MyNum, position, ball_pos, tuple(best_pass_target))
                 else: # If no good pass, just clear it towards opponent goal
                     return self.newKickdef(strategyData, MyNum, position, ball_pos, goal_target)

            elif strategyData.distance(ball_pos, (-15,0)) < threat_distance: # Ball is dangerously close
                # Move to intercept: Position self between ball and center of goal
                intercept_pos = strategyData.point_on_line_segment(ball_pos, (-15,0), goalie_rest_pos[0]) # Point on goal line between ball/goal
                # Adjust Y slightly based on ball Y to cover angle, but clamp near goal posts (-1.5 to 1.5 approx)
                intercept_y = np.clip(ball_pos[1] * 0.8, -1.5, 1.5)

                # Ensure intercept_pos is not None before accessing index 0
                final_intercept_pos = (intercept_pos[0], intercept_y) if intercept_pos is not None else (goalie_rest_pos[0], intercept_y)

                strategyData.my_desired_position = final_intercept_pos
                strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos) # Face the ball
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=False) # Direct move, ignore others near goal

            else: # Ball is far, stay at rest position
                strategyData.my_desired_position = goalie_rest_pos
                strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos) # Face the ball
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)

        # 2. CHERRY-PICKER LOGIC (Player 11 - Exploiting No Offside)
        elif my_role == 'CHERRY_PICKER':
            cherry_pick_spot = (14, 0) # Position right in front of opponent goal

            if active_player == MyNum: # Cherry-picker has the ball
                # Shoot immediately!
                return self.newKickdef(strategyData, MyNum, position, ball_pos, goal_target)
            else: # Wait at the spot, facing the ball for a pass
                strategyData.my_desired_position = cherry_pick_spot
                strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos)
                # Don't worry about formation, just go to the spot
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=True)

        # 3. DEFENDER LOGIC (Players 2, 3, 4)
        elif my_role == 'DEFENDER':
            if active_player == MyNum: # Defender has the ball
                 # Pass to Cherry Picker or another open forward player
                 # --- SAFETY CHECK ---
                 cherry_picker_pos = None
                 if len(strategyData.teammate_positions) > 10 and strategyData.teammate_positions[10] is not None:
                      cherry_picker_pos = strategyData.teammate_positions[10] # Assuming player 11 is cherry picker
                 # --- END SAFETY CHECK ---

                 best_pass_target, second_best = pass_reciever_selector(MyNum, strategyData.teammate_positions, strategyData.opponent_positions, goal_target, priority_target=cherry_picker_pos)

                 if best_pass_target is not None:
                     return self.newKickdef(strategyData, MyNum, position, ball_pos, tuple(best_pass_target))
                 elif second_best is not None:
                     return self.newKickdef(strategyData, MyNum, position, ball_pos, tuple(second_best))
                 else: # Clear towards goal if no pass
                     return self.newKickdef(strategyData, MyNum, position, ball_pos, goal_target)
            else: # Defender doesn't have ball - go to formation spot
                strategyData.my_desired_position = my_formation_spot
                strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos)
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)

        # 4. MIDFIELDER LOGIC (Players 5, 6, 7, 8, 9, 10)
        elif my_role == 'MIDFIELDER':
            if active_player == MyNum: # Midfielder has the ball
                 # Primary goal: Pass to Cherry Picker. Secondary: Pass to other open forward. Tertiary: Dribble/Shoot.
                 # --- SAFETY CHECK ---
                 cherry_picker_pos = None
                 if len(strategyData.teammate_positions) > 10 and strategyData.teammate_positions[10] is not None:
                      cherry_picker_pos = strategyData.teammate_positions[10] # Assuming player 11 is cherry picker
                 # --- END SAFETY CHECK ---

                 best_pass_target, second_best = pass_reciever_selector(MyNum, strategyData.teammate_positions, strategyData.opponent_positions, goal_target, priority_target=cherry_picker_pos)

                 if best_pass_target is not None:
                      # Check if best pass is the cherry picker (and cherry_picker_pos is valid)
                      if cherry_picker_pos is not None and np.array_equal(best_pass_target, cherry_picker_pos):
                           # Pass directly to cherry picker spot, might lead slightly
                           pass_target = strategyData.point_in_direction(best_pass_target, goal_target, 0.5)
                           # Ensure pass_target is not None before converting to tuple
                           return self.newKickdef(strategyData, MyNum, position, ball_pos, tuple(pass_target)) if pass_target is not None else self.newKickdef(strategyData, MyNum, position, ball_pos, goal_target) # Fallback to shooting
                      else:
                           return self.newKickdef(strategyData, MyNum, position, ball_pos, tuple(best_pass_target))
                 elif second_best is not None:
                     return self.newKickdef(strategyData, MyNum, position, ball_pos, tuple(second_best))
                 else: # If no passes, dribble towards goal using fast dribble
                     return self.newKickdef(strategyData, MyNum, position, ball_pos, goal_target)

            else: # Midfielder doesn't have ball - go to formation spot
                strategyData.my_desired_position = my_formation_spot
                strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos)
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)

        # Fallback (shouldn't happen with defined roles)
        else:
             strategyData.my_desired_position = my_formation_spot
             strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(ball_pos)
             return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)


    # --- Fat proxy methods remain the same ---
    # ... (keep existing fat_proxy_kick and fat_proxy_move) ...
    def fat_proxy_kick(self):
        # ... (keep existing fat_proxy_kick)
        w = self.world
        r = self.world.robot
        ball_2d = w.ball_abs_pos[:2]
        my_head_pos_2d = r.loc_head_position[:2]

        if np.linalg.norm(ball_2d - my_head_pos_2d) < 0.25:
            self.fat_proxy_cmd += f"(proxy kick 10 {M.normalize_deg( self.kick_direction  - r.imu_torso_orientation ):.2f} 20)"
            self.fat_proxy_walk = np.zeros(3)
            return True
        else:
            self.fat_proxy_move(ball_2d-(-0.1,0), None, True)
            return False


    def fat_proxy_move(self, target_2d, orientation, is_orientation_absolute):
        # ... (keep existing fat_proxy_move)
        r = self.world.robot
        target_dist = np.linalg.norm(target_2d - r.loc_head_position[:2])
        target_dir = M.target_rel_angle(r.loc_head_position[:2], r.imu_torso_orientation, target_2d)

        if target_dist > 0.1 and abs(target_dir) < 8:
            self.fat_proxy_cmd += (f"(proxy dash {100} {0} {0})")
            return

        if target_dist < 0.1:
            if is_orientation_absolute:
                orientation = M.normalize_deg( orientation - r.imu_torso_orientation )
            target_dir = np.clip(orientation, -60, 60)
            self.fat_proxy_cmd += (f"(proxy dash {0} {0} {target_dir:.1f})")
        else:
            self.fat_proxy_cmd += (f"(proxy dash {20} {0} {target_dir:.1f})")

