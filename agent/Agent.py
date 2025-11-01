from agent.Base_Agent import Base_Agent
from math_ops.Math_Ops import Math_Ops as M
import math
import numpy as np

from strategy.Assignment import role_assignment
from strategy.Assignment import pass_reciever_selector
from strategy.Strategy import Strategy 

from formation.Formation import GeneratePlayOn
from formation.Formation import GenerateDefense
from formation.Formation import GenerateFormation_5 # <--- ADD THIS LINE



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

        # 5-Player initial positions (based on user image)
        # NEW 5-Player initial positions (Strikers 3 & 5 are ready)
        init_positions_5 = [
            [-14, 0],   # 1: Goalie
            [-9, -3],   # 2: Left Defender
            [-2.5, 1],  # 3: STRIKER 1 (Kicker) - Legal spot
            [-9, 3],    # 4: Right Defender
            [-2.5, -1]  # 5: STRIKER 2 (Receiver/Charger) - Legal spot
        ]
        self.init_pos = init_positions_5[unum-1] # initial formation
        


    def beam(self, avoid_center_circle=False):
        r = self.world.robot
        pos = self.init_pos[:] # copy position list 
        self.state = 0
        
 
        # Avoid center circle by moving the player back 
        if avoid_center_circle and np.linalg.norm(self.init_pos) < 2.5:
            pos[0] = -2.3 

        if np.linalg.norm(pos - r.loc_head_position[:2]) > 0.1 or self.behavior.is_ready("Get_Up"):
            self.scom.commit_beam(pos, M.vector_angle((-pos[0],-pos[1]))) # beam to initial position, face coordinate (0,0)
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

        if avoid_obstacles:
            target_2d, _, distance_to_final_target = self.path_manager.get_path_to_target(
                target_2d, priority_unums=priority_unums, is_aggressive=is_aggressive, timeout=timeout)
        else:
            distance_to_final_target = np.linalg.norm(np.array(target_2d) - r.loc_head_position[:2])

        self.behavior.execute("Walk", target_2d, True, orientation, is_orientation_absolute, distance_to_final_target) # Args: target, is_target_abs, ori, is_ori_abs, distance


    def kick(self, kick_direction=None, kick_distance=None, abort=False, enable_pass_command=False):
        '''
        Walk to ball and kick
        '''
        return self.behavior.execute("Dribble",None,None)

        if self.min_opponent_ball_dist < 1.45 and enable_pass_command:
            self.scom.commit_pass_command()

        self.kick_direction = self.kick_direction if kick_direction is None else kick_direction
        self.kick_distance = self.kick_distance if kick_distance is None else kick_distance

        if self.fat_proxy_cmd is None: # normal behavior
            return self.behavior.execute("Basic_Kick", self.kick_direction, abort) # Basic_Kick has no kick distance control
        else: # fat proxy behavior
            return self.fat_proxy_kick()


    def kickTarget(self, strategyData, mypos_2d=(0,0),target_2d=(0,0), abort=False, enable_pass_command=False):
        '''
        Walk to ball and kick
        '''

        # Calculate the vector from the current position to the target position
        vector_to_target = np.array(target_2d) - np.array(mypos_2d)
        
        # Calculate the distance (magnitude of the vector)
        kick_distance = np.linalg.norm(vector_to_target)
        
        # Calculate the direction (angle) in radians
        direction_radians = np.arctan2(vector_to_target[1], vector_to_target[0])
        
        # Convert direction to degrees for easier interpretation (optional)
        kick_direction = np.degrees(direction_radians)


        if strategyData.min_opponent_ball_dist < 1.45 and enable_pass_command:
            self.scom.commit_pass_command()

        self.kick_direction = self.kick_direction if kick_direction is None else kick_direction
        self.kick_distance = self.kick_distance if kick_distance is None else kick_distance

        if self.fat_proxy_cmd is None: # normal behavior
            return self.behavior.execute("Basic_Kick", self.kick_direction, abort) # Basic_Kick has no kick distance control
        else: # fat proxy behavior
            return self.fat_proxy_kick()


    def dribble(self, orientation=None, is_orientation_absolute=True, speed=1, stop=False):
        '''
        Dribble with the ball using the RL behavior.
        This function is a wrapper for the "Dribble" behavior,
        just like move() wraps "Walk" and kickTarget() wraps "Basic_Kick".
        '''
        if self.fat_proxy_cmd is not None:
            # Fat proxy doesn't have a dedicated dribble, so just move to the ball
            return self.fat_proxy_kick() 

        # When orientation is None, the Dribble behavior automatically
        # dribbles towards the opponent's goal.
        return self.behavior.execute("Dribble", orientation, is_orientation_absolute, speed, stop)

            
    # --- START OF MERGED FUNCTION ---
    # This is Amaan's dribble logic, renamed to be clear
    def dribbleToTarget(self, strategyData, MyNum=0, position=(0,0), ball_pos=(0.0, 0.0), aim=(15.5,0)):
        goal = aim
        # if strategyData.min_opponent_ball_dist > 1:
            # NOTE: potential_fields_pathfinding is very complex. Let's not use it for now
            # aim = strategyData.potential_fields_pathfinding(position, aim)
            # pass 

        startat = strategyData.point_in_direction(ball_pos, aim, -0.2) #position behind ball collinear with goal and ball
        
        # if strategyData.distance(position, startat) > 0.7:
            # NOTE: next_position_to_startat is also complex. Let's simplify.
            # startat = strategyData.next_position_to_startat(aim, ball_pos, position, startat)
            # pass

        # Corrected condition: Check PLAYER's position, not the goal's
        if strategyData.ball_dist <= 0.5 and strategyData.distance(position, goal) < 5 and position[0] > 11.0: #if I am close enough and near goal, kick!
            return self.kickTarget(strategyData, strategyData.mypos, goal)
        
        elif not(strategyData.are_points_collinear(position, ball_pos, aim)):#check if 3 points arent collinear w tolerance this means im not in line so move towards colinear point
            strategyData.my_desired_position = (startat)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            # --- MODIFIED: Added timeout=999999 to "remove" timeout ---
            return self.move(strategyData.my_desired_position, orientation=strategyData.ball_dir, avoid_obstacles=True, timeout=999999)
        
        elif strategyData.ball_dist > 0.5: #im now colinear so now go close enough to ball
            strategyData.point_in_direction(position, aim)
            strategyData.my_desired_position = (strategyData.ball_2d)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            # --- MODIFIED: Added timeout=999999 to "remove" timeout ---
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, timeout=999999)
        
        else: #ball_dist is now less than 0.5 and im in line so i can move forward
            towards = strategyData.point_in_direction(position, aim, 4)
            strategyData.my_desired_position = (towards)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            # --- MODIFIED: Added timeout=999999 to "remove" timeout ---
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=False, timeout=999999)
    # --- END OF MERGED FUNCTION ---

    def think_and_send(self):
        
        behavior = self.behavior
        strategyData = Strategy(self.world)
        d = self.world.draw
        
        # Convert None positions to a default far-away location for calculations
        # This is a safety check to prevent crashes if a player is not seen
        default_pos = np.array([-100.0, -100.0])
        strategyData.teammate_positions = [pos if pos is not None else default_pos for pos in strategyData.teammate_positions]
        strategyData.opponent_positions = [pos if pos is not None else default_pos for pos in strategyData.opponent_positions]


        if strategyData.play_mode == self.world.M_GAME_OVER:
            pass
        elif strategyData.PM_GROUP == self.world.MG_ACTIVE_BEAM:
            self.beam()
        elif strategyData.PM_GROUP == self.world.MG_PASSIVE_BEAM:
            self.beam(True) # avoid center circle
        elif self.state == 1 or (behavior.is_ready("Get_Up") and self.fat_proxy_cmd is None):
            self.state = 0 if behavior.execute("Get_Up") else 1

        elif (strategyData.PM_GROUP == self.world.MG_THEIR_KICK):
            # USE ATTACKER (PLAYER 5) TO CHARGE
            CHARGER_UNUM = 5 
            
            if strategyData.robot_model.unum == CHARGER_UNUM:
                # Move to the edge of the center circle
                self.move(target_2d=(-2.5, 0), orientation=strategyData.ball_dir)
            else:
                # All other players hold their initial position
                self.move(self.init_pos, orientation=strategyData.ball_dir)


        # --- START OF CHANGE ---
        # Replaced kickTarget with dribble for set plays
        elif (strategyData.play_mode == self.world.M_OUR_KICKOFF):
            # NEW AGGRESSIVE PLAN: Player 3 kicks the ball forward, and Player 5
            # runs onto it from a legal starting position.
            KICKER_UNUM = 3
            RECEIVER_UNUM = 5
            
            # The KICK'S target (in opponent's half)
            KICK_TARGET_POS = (-0, -0.5)
            # The RECEIVER'S legal starting spot (in our half)
            RECEIVER_START_POS = (-1, -3) 
            
            if strategyData.robot_model.unum == KICKER_UNUM:
                # Move to ball and kick it to the forward target
                self.kickTarget(strategyData, strategyData.mypos, KICK_TARGET_POS)
                
            elif strategyData.robot_model.unum == RECEIVER_UNUM:
                # Move to the legal "ready" spot and face the ball
                self.move(target_2d=RECEIVER_START_POS, orientation=strategyData.ball_dir)
                
            else:
                # All other players (1, 2, 4) hold their initial position
                self.move(self.init_pos, orientation=strategyData.ball_dir)


        elif (strategyData.play_mode == self.world.M_OUR_GOAL_KICK):
            if strategyData.robot_model.unum == 1:
                # --- MODIFIED: Use dribbleToTarget ---
                return self.dribbleToTarget(strategyData, 
                                            MyNum=strategyData.robot_model.unum, 
                                            position=strategyData.mypos, 
                                            ball_pos=strategyData.ball_2d, 
                                            aim=(15.5, 0)) # Aim for goal
        # --- END OF CHANGE ---
        else:
            # This is the FIX: Only call select_skill() if the game is in PlayOn
            if strategyData.play_mode == self.world.M_PLAY_ON:
                self.select_skill(strategyData)
            else:
                # This will now correctly do nothing during M_BEFORE_KICKOFF
                # and all other unhandled modes, letting our kickoff logic work.
                pass


        #--------------------------------------- 3. Broadcast
        self.radio.broadcast()

        #--------------------------------------- 4. Send to server
        if self.fat_proxy_cmd is None: # normal behavior
            self.scom.commit_and_send( strategyData.robot_model.get_command() )
        else: # fat proxy behavior
            self.scom.commit_and_send( self.fat_proxy_cmd.encode() ) 
            self.fat_proxy_cmd = ""


    def select_skill(self,strategyData):
        #--------------------------------------- 2. Decide action

        drawer = self.world.draw
        
        path_draw_options = self.path_manager.draw_options

        target = (15,0) # Opponents Goal
        
        # --- START OF "STALL" EXPLOIT LOGIC (v9 - Hunter/Blocker) ---
        
        # 1. Define our roles
        HUNTER_UNUM = 1                  # Player 1 will hunt Opp 5
        SPOT_BLOCKER_UNUMS = [2, 4]      # Player 2 & 4 will block Opp 5's spot
        TARGET_OPPONENT_INDEX = 4        # Target opponent player 5 (index 4)
        
        BALL_ATTACKER_UNUM = 5           # Your Striker 2
        # Player 3 will fall through to normal logic
        
        my_unum = strategyData.robot_model.unum
        
        # This is the dummy position used in think_and_send to clean the list
        default_pos = np.array([-100.0, -100.0]) 
        
        # 2. Define the fallback spot for Opponent 5 (from baseline's Formation.py)
        #    Their Player 5 is at np.array([12, 0])
        if strategyData.side == 0: # We are LEFT, opponent is RIGHT
            # Opponent's formation is mirrored: (x, y) -> (-x, -y)
            OPPONENT_5_SPOT = np.array([-12.0, 0.0])
        else: # We are RIGHT, opponent is LEFT
            # Opponent's formation is absolute
            OPPONENT_5_SPOT = np.array([12.0, 0.0])


        if my_unum == HUNTER_UNUM:
            # --- HUNTER LOGIC ---
            target_opp_pos = strategyData.opponent_positions[TARGET_OPPONENT_INDEX]

            if not np.array_equal(target_opp_pos, default_pos):
                # Opponent 5 is visible! Move to their position.
                strategyData.my_desired_position = target_opp_pos
                drawer.annotation(tuple(target_opp_pos), f"HUNTING OPP 5" , drawer.Color.red, "exploit")
            else:
                # Opponent 5 is NOT visible. Go to their known formation spot.
                strategyData.my_desired_position = OPPONENT_5_SPOT
                drawer.annotation(tuple(OPPONENT_5_SPOT), f"HUNTING OPP 5 (SPOT)" , drawer.Color.orange, "exploit")

            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, timeout=999999)

        elif my_unum in SPOT_BLOCKER_UNUMS:
            # --- SPOT BLOCKER LOGIC ---
            strategyData.my_desired_position = OPPONENT_5_SPOT # Default: go to the spot
            drawer.annotation(tuple(OPPONENT_5_SPOT), f"BLOCKING OPP 5 SPOT" , drawer.Color.cyan, "exploit")

            # Check if opp 5 is visible AND close to their spot
            target_opp_pos = strategyData.opponent_positions[TARGET_OPPONENT_INDEX]
            if not np.array_equal(target_opp_pos, default_pos):
                # Check distance from opponent to their spot (4m^2 = 2m radius)
                if np.sum((target_opp_pos - OPPONENT_5_SPOT) ** 2) < 4.0:
                    # Opponent is close! Switch to pushing them.
                    strategyData.my_desired_position = target_opp_pos
                    drawer.annotation(tuple(target_opp_pos), f"PUSHING OPP 5" , drawer.Color.red, "exploit")
            
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, timeout=999999)

        elif my_unum == BALL_ATTACKER_UNUM:
            # Your primary Attacker's job is to take the ball
            drawer.annotation((0,10.5), "STALL: ATTACKING BALL" , drawer.Color.green, "status")
            return self.dribbleToTarget(strategyData, 
                                        MyNum=my_unum, 
                                        position=strategyData.mypos, 
                                        ball_pos=strategyData.ball_2d, 
                                        aim=(15.5, 0)) # Aim for goal
        
        # --- END OF "STALL" EXPLOIT LOGIC ---

        # --- ORIGINAL LOGIC (for Player 3 ONLY) ---
        
        #------------------------------------------------------
        #Role Assignment
        formation_positions = []
        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            drawer.annotation((0,10.5), "Role Assignment Phase" , drawer.Color.yellow, "status")
        else:
            drawer.clear("status")    


        # --- NEW 5-PLAYER FORMATION LOGIC ---
        
        # 1. Select the best 5-player formation based on the ball's X position
        formation_positions = GenerateFormation_5(strategyData.ball_2d[0])

        # 2. Get the list of our 5 teammates
        current_teammates = strategyData.teammate_positions
        
        # Filter out any None or dummy values
        valid_teammates = [pos for pos in current_teammates if pos is not None and not np.array_equal(pos, default_pos)]
        
        # 3. Handle if we don't see all 5 teammates (e.g., use dummy positions for unseen players)
        num_teammates_seen = len(valid_teammates)
        if num_teammates_seen < 5:
            # Note: This simple padding might not be ideal, but it matches the old logic.
            # It's better to use last-known positions if possible.
            dummy_pos = np.array([-100.0, -100.0]) 
            padded_teammates = valid_teammates + [dummy_pos] * (5 - num_teammates_seen)
        else:
            padded_teammates = valid_teammates[:5] # Use the first 5 seen

        # 4. Call the 5-player role_assignment
        # Ensure our formation list also has 5 positions
        padded_formation = formation_positions[:5] 
        if len(padded_formation) < 5:
            dummy_pos = np.array([-100.0, -100.0])
            padded_formation = padded_formation + [dummy_pos] * (5 - len(padded_formation))

        point_preferences = role_assignment(padded_teammates, padded_formation)
        # --- END NEW 5-PLAYER LOGIC ---
        
        if strategyData.active_player_unum == strategyData.robot_model.unum:  # I am the active player
            if strategyData.min_teammate_ball_dist < strategyData.min_opponent_ball_dist:
                if 0.0 <=strategyData.ball_speed <= 0.0:
                    strategyData.my_desired_position = strategyData.ball_2d   # Go to the ball
                    strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d)  
        else:
            # Check if self.player_unum is in point_preferences before accessing
            if strategyData.player_unum in point_preferences:
                strategyData.my_desired_position = point_preferences[strategyData.player_unum]  # Follow formation
            else:
                # Fallback: if not assigned, just go to init_pos
                strategyData.my_desired_position = self.init_pos
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d)

        drawer.line(strategyData.mypos, strategyData.my_desired_position, 2,drawer.Color.blue,"target line")

        # --- START OF CHANGE ---
        # Removed all pass/kick logic.
        # If not in formation, active player dribbles, others move.
        if not strategyData.IsFormationReady(point_preferences):     
            if strategyData.active_player_unum == strategyData.robot_model.unum:  # I am the active player
                # --- MODIFIED: Use dribbleToTarget ---
                return self.dribbleToTarget(strategyData, 
                                            MyNum=strategyData.robot_model.unum, 
                                            position=strategyData.mypos, 
                                            ball_pos=strategyData.ball_2d, 
                                            aim=(15.5, 0)) # Aim for goal
            else:
                # Follow formation
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)
        
        #------------------------------------------------------
        #Pass Selector
        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            drawer.annotation((0,10.5), "Dribbling to Goal" , drawer.Color.green, "status") # Changed status
        else:
            drawer.clear_player()

        # If in formation, active player dribbles, others move.
        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            # --- MODIFIED: Use dribbleToTarget ---
            return self.dribbleToTarget(strategyData, 
                                        MyNum=strategyData.robot_model.unum, 
                                        position=strategyData.mypos, 
                                        ball_pos=strategyData.ball_2d, 
                                        aim=(15.5, 0)) # Aim for goal
        else:
            # Check if self.player_unum is in point_preferences before accessing
            if strategyData.player_unum in point_preferences:
                strategyData.my_desired_position = point_preferences[strategyData.player_unum]
            else:
                strategyData.my_desired_position = self.init_pos
            return self.move(strategyData.my_desired_position, orientation=strategyData.ball_dir)
        # --- END OF CHANGE ---

    def fat_proxy_kick(self):
        w = self.world
        r = self.world.robot 
        ball_2d = w.ball_abs_pos[:2]
        my_head_pos_2d = r.loc_head_position[:2]

        if np.linalg.norm(ball_2d - my_head_pos_2d) < 0.25:
            # fat proxy kick arguments: power [0,10]; relative horizontal angle [-180,180]; vertical angle [0,70]
            self.fat_proxy_cmd += f"(proxy kick 10 {M.normalize_deg( self.kick_direction  - r.imu_torso_orientation ):.2f} 20)" 
            self.fat_proxy_walk = np.zeros(3) # reset fat proxy walk
            return True
        else:
            self.fat_proxy_move(ball_2d-(-0.1,0), None, True) # ignore obstacles
            return False


    def fat_proxy_move(self, target_2d, orientation, is_orientation_absolute):
        r = self.world.robot

        target_dist = np.linalg.norm(np.array(target_2d) - r.loc_head_position[:2])
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