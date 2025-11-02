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
            [-2.1, 1.],  # 3: STRIKER 1 (Kicker) - Legal spot
            [-9, 3],    # 4: Right Defender
            [-2.2, 0]   # 5: STRIKER 2 (Receiver/Charger) - Legal spot
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

            
    # --- THIS IS THE FUNCTION WE ARE NOW USING ---
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
    # --- END OF FUNCTION ---

    def think_and_send(self):
        
        behavior = self.behavior
        strategyData = Strategy(self.world)
        d = self.world.draw
        
        # Convert None positions to a default far-away location for calculations
        default_pos = np.array([-100.0, -100.0])
        strategyData.teammate_positions = [pos if pos is not None else default_pos for pos in strategyData.teammate_positions]
        strategyData.opponent_positions = [pos if pos is not None else default_pos for pos in strategyData.opponent_positions]

        # --- KICKOFF PARAMETERS (we define them once up here) ---
        KICKER_UNUM = 3
        RECEIVER_UNUM = 5
        KICK_TARGET_POS = (1, 0)
        RECEIVER_START_POS = (0, -1) 
        
        # --- YOUR NEW STATE CHECK ---
        # Check if the ball is still at the center (within 0.5m)
        ball_at_center = np.linalg.norm(strategyData.ball_2d) < 0.5


        if strategyData.play_mode == self.world.M_GAME_OVER:
            pass
        elif strategyData.PM_GROUP == self.world.MG_ACTIVE_BEAM:
            self.beam()
        elif strategyData.PM_GROUP == self.world.MG_PASSIVE_BEAM:
            self.beam(True) # avoid center circle
        elif self.state == 1 or (behavior.is_ready("Get_Up") and self.fat_proxy_cmd is None):
            self.state = 0 if behavior.execute("Get_Up") else 1

        # --- OUR_KICKOFF (Stays the same, with Player 3 kicking) ---
        elif (strategyData.play_mode == self.world.M_OUR_KICKOFF):
            if strategyData.robot_model.unum == KICKER_UNUM:
                self.kickTarget(strategyData, strategyData.mypos, KICK_TARGET_POS)
            elif strategyData.robot_model.unum == RECEIVER_UNUM:
                self.move(target_2d=RECEIVER_START_POS, orientation=strategyData.ball_dir)
            else:
                self.move(self.init_pos, orientation=strategyData.ball_dir)


        elif (strategyData.play_mode == self.world.M_THEIR_GOAL_KICK or
              strategyData.play_mode == self.world.M_THEIR_FREE_KICK or
              strategyData.play_mode == self.world.M_THEIR_KICK_IN or
              strategyData.play_mode == self.world.M_THEIR_CORNER_KICK):
            
            self.select_skill(strategyData)

        elif (strategyData.play_mode == self.world.M_OUR_GOAL_KICK or
              strategyData.play_mode == self.world.M_OUR_FREE_KICK or
              strategyData.play_mode == self.world.M_OUR_KICK_IN or
              strategyData.play_mode == self.world.M_OUR_CORNER_KICK):
            
            pass # Do nothing, wait for timeout
            
        else:
            # This is the main PlayOn logic
            if strategyData.play_mode == self.world.M_PLAY_ON:
                
                # --- START OF YOUR NEW LOGIC ---
                # IF: It's PlayOn
                # AND: The ball is still at the center
                if ball_at_center:
                    
                    # RUN "THEIR KICKOFF" PLAY
                    # (This is your new idea)
                    if strategyData.robot_model.unum == 5:
                        # Player 5 (Attacker) charges the ball
                        self.kickTarget(strategyData, strategyData.mypos, KICK_TARGET_POS)
                    else:
                        # All other players (1, 2, 3, 4) run select_skill
                        # to go to their "jail" spots immediately.
                        self.select_skill(strategyData)
                
                else:
                    # EITHER: It's normal play
                    # OR: The ball has been kicked from center
                    # -> Run the normal logic
                    self.select_skill(strategyData)
                # --- END OF YOUR NEW LOGIC ---

            else:
                # This covers M_BEFORE_KICKOFF, etc.
                pass


        #--------------------------------------- 3. Broadcast
        self.radio.broadcast()

        #--------------------------------------- 4. Send to server
        if self.fat_proxy_cmd is None: # normal behavior
            self.scom.commit_and_send( strategyData.robot_model.get_command() )
        else: # fat proxy behavior
            self.scom.commit_and_send( self.fat_proxy_cmd.encode() ) 
            self.fat_proxy_cmd = ""


    # --- customDribbleAndShoot HAS BEEN REMOVED ---

    def customDribbleAndShoot(self, strategyData):
        '''
        This is your "good old" dribble function (tolerance=0.45)
        simplified to remove all unnecessary pass/keeper logic.
        
        ADDED: "Tap-in" logic.
        '''
        # --- PARAMETERS ---
        GOAL_POS = (15.5, 0.7)      # Aim for the TOP corner
        X_POSITION_TO_SHOOT = 11.0  # How close to goal before shooting (for both players)
        
        # --- Get current data ---
        my_pos = strategyData.mypos
        my_unum = strategyData.robot_model.unum
        ball_pos = strategyData.ball_2d
        ball_dist = strategyData.ball_dist

        # --- "TAP-IN" PARAMETERS ---
        opp_keeper_pos = strategyData.opponent_positions[0] # Keeper is Player 1 (index 0)
        TAP_IN_X_POS = 14.0 # How close to goal (X) to start walking it in
        PUSH_DIST = 0.4     # How close ball must be to be "pushing"

        # --- START OF "TAP-IN" LOGIC ---
        is_in_shoot_x_zone = my_pos[0] > X_POSITION_TO_SHOOT
        is_at_goal_mouth = my_pos[0] > TAP_IN_X_POS 
        is_past_keeper = my_pos[0] > opp_keeper_pos[0]
        has_ball = ball_dist <= PUSH_DIST

        if is_at_goal_mouth and is_past_keeper and has_ball:
            # We are past the keeper and at the goal. Just walk it in.
            goal_dir = strategyData.GetDirectionRelativeToMyPositionAndTarget(GOAL_POS)
            return self.move(GOAL_POS, orientation=goal_dir, avoid_obstacles=False, timeout=999999)
        # --- END OF "TAP-IN" LOGIC ---


        # 1. CHECK TO SHOOT
        # If the "tap-in" failed, we fall back to a normal kick.
        if my_pos[0] > X_POSITION_TO_SHOOT and ball_dist < 0.5:
            return self.kickTarget(strategyData, my_pos, GOAL_POS)

        # --- START OF DRIBBLE "STUCK" FIX ---

        # 2. CHECK ALIGNMENT
        # Check if the player, the ball, and the goal are in a straight line.
        is_aligned = strategyData.are_points_collinear(my_pos, ball_pos, GOAL_POS, tolerance=0.45)

        # Check if we are aligned BUT IN FRONT of the ball (i.e., ball is behind us)
        is_in_front_of_ball = is_aligned and my_pos[0] > ball_pos[0] and my_pos[0] < GOAL_POS[0]

        # We must align IF:
        #   a) We are not aligned at all
        #   b) We ARE aligned, but we are in front of the ball (and not right on top of it)
        if (not is_aligned) or (is_in_front_of_ball and ball_dist > 0.4):
            # STAGE 1: ALIGN
            # 'startat' is a point 0.2m behind the ball, on the line to the goal.
            startat = strategyData.point_in_direction(ball_pos, GOAL_POS, -0.2)
            # Move to this alignment spot, facing the ball
            return self.move(startat, orientation=strategyData.ball_dir, avoid_obstacles=True, timeout=999999)

        # --- END OF DRIBBLE "STUCK" FIX ---

        elif ball_dist > 0.4:
            # STAGE 2: APPROACH
            # We ARE aligned AND behind the ball, but too far to push. Move closer to the ball.
            goal_dir = strategyData.GetDirectionRelativeToMyPositionAndTarget(GOAL_POS)
            return self.move(ball_pos, orientation=goal_dir, avoid_obstacles=True, timeout=999999)

        else:
            # STAGE 3: PUSH
            # We ARE aligned AND close enough. Push the ball forward.
            push_target = strategyData.point_in_direction(my_pos, GOAL_POS, 4)
            goal_dir = strategyData.GetDirectionRelativeToMyPositionAndTarget(push_target)
            # Move fast, don't avoid obstacles (since opponents are frozen)
            return self.move(push_target, orientation=goal_dir, avoid_obstacles=False, timeout=999999)


    # --- THIS IS YOUR FRIEND'S "JAIL" STRATEGY ---
# --- THIS IS YOUR FRIEND'S "JAIL" STRATEGY ---
    def select_skill(self,strategyData):
        #--------------------------------------- 2. Decide action

        drawer = self.world.draw
        
        path_draw_options = self.path_manager.draw_options

        target = (15,0) # Opponents Goal

        DISTANCE_TOLERANCE = 0.15
        
        # --- NEW ---
        # REMOVED SPIN_INCREMENT_DEGS and DISTANCE_TOLERANCE
        # --- END NEW ---
        
        # --- START OF 2v1 STALL EXPLOIT LOGIC ---
        
        # 1. Define our roles
        # --- MODIFICATION: Player 1 is now a blocker ---
        HUNTER_UNUMS = []           # No full-time hunters
        RIGHT_BLOCKER_UNUM = 1      # Player 1 blocks the right side
        # --- END MODIFICATION ---

        # "Sandwich" roles for Player 2 and 4
        BACK_BLOCKER_UNUM = 2       # Player 2 will stand "behind" the spot
        FRONT_BLOCKER_UNUM = 4      # Player 4 will stand "in front" of the spot
        
        # --- MODIFICATION: Player 3 is now a blocker ---
        LEFT_BLOCKER_UNUM = 3       # Player 3 blocks the left side
        # --- END MODIFICATION ---
        
        TARGET_OPPONENT_INDEX = 4       # Target opponent player 5 (index 4)
        
        my_unum = strategyData.robot_model.unum
        
        default_pos = np.array([-100.0, -100.0]) 
        
        OPPONENT_5_SPOT = np.array([-12.0, 0.0])
        OUR_NET_POS = (-15.5, 0.0) # Our goal
        
        
        # --- MODIFICATION: Removed dynamic role for Player 3 ---
        # --- END OF DYNAMIC ROLE ---


        if my_unum in HUNTER_UNUMS:
            # --- HUNTER LOGIC (now empty, but kept for potential future use) ---
            target_opp_pos = strategyData.opponent_positions[TARGET_OPPONENT_INDEX]

            if not np.array_equal(target_opp_pos, default_pos):
                strategyData.my_desired_position = target_opp_pos
                drawer.annotation(tuple(target_opp_pos), f"HUNTING OPP 5" , drawer.Color.red, "exploit")
            else:
                strategyData.my_desired_position = OPPONENT_5_SPOT
                drawer.annotation(tuple(OPPONENT_5_SPOT), f"HUNTING OPP 5 (SPOT)" , drawer.Color.orange, "exploit")

            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, timeout=999999)

        # --- MODIFICATION: Player 1 (Right Blocker) ---
        elif my_unum == RIGHT_BLOCKER_UNUM:
            # --- "RIGHT BLOCKER" LOGIC (Player 1) ---
            player_1_target = OPPONENT_5_SPOT + np.array([0, -0.265]) # -0.3 is "right"
            
            # --- MODIFIED: Removed spin logic ---
            desired_orientation_degs = 90.0 # Face -Y
            drawer.annotation(tuple(player_1_target), f"RIGHT BLOCK (FACE -Y)" , drawer.Color.red, "exploit")
            # --- END MODIFICATION ---
            
            strategyData.my_desired_position = player_1_target

            return self.move(
                strategyData.my_desired_position, 
                orientation=desired_orientation_degs, 
                is_orientation_absolute=True,
                avoid_obstacles=True,
                is_aggressive=False,
                timeout=999999
            )
        # --- END MODIFICATION ---

        # --- MODIFICATION: Player 3 (Left Blocker) ---
        # --- MODIFICATION: New block for Player 3 (Left Blocker) ---
        elif my_unum == LEFT_BLOCKER_UNUM:
            # --- "LEFT BLOCKER" LOGIC (Player 3) ---
            
            # This is the final target position and orientation
            player_3_target = OPPONENT_5_SPOT + np.array([0, 0.265]) # +0.3 is "left"
            final_orientation_degs = -90.0 # Face +Y
            
            # Check distance to the target spot
            distance_to_target = np.linalg.norm(np.array(strategyData.mypos) - player_3_target)
            
            # --- START OF 2-STAGE FIX ---
            if distance_to_target < DISTANCE_TOLERANCE:
                # STAGE 2: TURN
                # We are at the spot, so stop moving and face the final direction
                desired_orientation_degs = final_orientation_degs
                drawer.annotation(tuple(player_3_target), f"LEFT BLOCK (TURNING)" , drawer.Color.green, "exploit")
            else:
                # STAGE 1: MOVE
                # We are far, so move directly *at* the target (this is faster)
                desired_orientation_degs = strategyData.GetDirectionRelativeToMyPositionAndTarget(player_3_target)
                drawer.annotation(tuple(player_3_target), f"LEFT BLOCK (MOVING)" , drawer.Color.green, "exploit")
            # --- END OF 2-STAGE FIX ---
            
            strategyData.my_desired_position = player_3_target

            # Call move with the dynamically set orientation
            return self.move(
                strategyData.my_desired_position, 
                orientation=desired_orientation_degs, 
                is_orientation_absolute=True,
                avoid_obstacles=True,
                is_aggressive=False, # Strictly stand there
                timeout=999999
            )
        # --- END MODIFICATION ---

        # --- MODIFICATION: Player 4 (Front Blocker) ---
        elif my_unum == FRONT_BLOCKER_UNUM:
            # --- "FRONT BLOCKER" LOGIC (Player 4) ---
            player_4_target = strategyData.point_in_direction(
                position=OPPONENT_5_SPOT, 
                goal=OUR_NET_POS, 
                distance=0.265 # 0.3m "in front"
            )

            # --- MODIFIED: Removed spin logic ---
            desired_orientation_degs = M.target_abs_angle(strategyData.mypos, OUR_NET_POS)
            drawer.annotation(tuple(player_4_target), f"FRONT BLOCK (FACE NET)" , drawer.Color.blue, "exploit")
            # --- END MODIFICATION ---
            
            strategyData.my_desired_position = player_4_target

            return self.move(
                strategyData.my_desired_position, 
                orientation=desired_orientation_degs, 
                is_orientation_absolute=True,
                avoid_obstacles=True,
                is_aggressive=False,
                timeout=999999
            )
        # --- END MODIFICATION ---

        # --- MODIFICATION: Player 2 (Back Blocker) ---
        elif my_unum == BACK_BLOCKER_UNUM:
            # --- "BACK BLOCKER" LOGIC (Player 2) ---
            player_2_target = strategyData.point_in_direction(
                position=OPPONENT_5_SPOT, 
                goal=OUR_NET_POS, 
                distance=-0.265 # 0.3m "behind"
            )
            
            # --- MODIFIED: Removed spin logic ---
            desired_orientation_degs = M.target_abs_angle(strategyData.mypos, OUR_NET_POS)
            drawer.annotation(tuple(player_2_target), f"BACK BLOCK (FACE NET)" , drawer.Color.cyan, "exploit")
            # --- END MODIFICATION ---
            
            strategyData.my_desired_position = player_2_target
            
            return self.move(
                strategyData.my_desired_position, 
                orientation=desired_orientation_degs, 
                is_orientation_absolute=True,
                avoid_obstacles=True,
                is_aggressive=False,
                timeout=999999
            )
        # --- END MODIFICATION ---

        # --- END OF "STALL" EXPLOIT LOGIC ---
        
        # --- ATTACKER LOGIC (Now ONLY for Player 5) ---
        
        #------------------------------------------------------
        #Role Assignment
        formation_positions = []
        if strategyData.active_player_unum == strategyData.robot_model.unum: 
            drawer.annotation((0,10.5), "Role Assignment Phase" , drawer.Color.yellow, "status")
        else:
            drawer.clear("status")    


        # --- NEW 5-PLAYER FORMATION LOGIC ---
        formation_positions = GenerateFormation_5(strategyData.ball_2d[0])
        current_teammates = strategyData.teammate_positions
        valid_teammates = [pos for pos in current_teammates if pos is not None and not np.array_equal(pos, default_pos)]
        
        num_teammates_seen = len(valid_teammates)
        if num_teammates_seen < 5:
            dummy_pos = np.array([-100.0, -100.0]) 
            padded_teammates = valid_teammates + [dummy_pos] * (5 - num_teammates_seen)
        else:
            padded_teammates = valid_teammates[:5]

        padded_formation = formation_positions[:5] 
        if len(padded_formation) < 5:
            dummy_pos = np.array([-100.0, -100.0])
            padded_formation = padded_formation + [dummy_pos] * (5 - len(padded_formation))

        point_preferences = role_assignment(padded_teammates, padded_formation)
        # --- END NEW 5-PLAYER LOGIC ---
        
        if strategyData.active_player_unum == strategyData.robot_model.unum:  # I am the active player
            if strategyData.min_teammate_ball_dist < strategyData.min_opponent_ball_dist:
                if 0.0 <=strategyData.ball_speed <= 0.0:
                    strategyData.my_desired_position = strategyData.ball_2d
                    strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d)  
        else:
            # --- Player 3 is a blocker, so this logic is only for Player 5 ---
            is_attacker = (my_unum == 5)
            
            if is_attacker:
                if strategyData.player_unum in point_preferences:
                    # Use normal formation spot
                    strategyData.my_desired_position = point_preferences[strategyData.player_unum]
                else:
                    # Fallback
                    strategyData.my_desired_position = self.init_pos
            elif strategyData.player_unum in point_preferences:
                # This block will now only be entered by Player 5
                strategyData.my_desired_position = point_preferences[strategyData.player_unum]
            else:
                # Fallback
                strategyData.my_desired_position = self.init_pos
            
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d)

        drawer.line(strategyData.mypos, strategyData.my_desired_position, 2,drawer.Color.blue,"target line")

        if not strategyData.IsFormationReady(point_preferences):    
            if strategyData.active_player_unum == strategyData.robot_model.unum:  # I am the active player
                # --- MODIFIED: CALLING dribbleToTarget ---
                return self.customDribbleAndShoot(strategyData)
            else:
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)
        
        #------------------------------------------------------
        #Pass Selector
        if strategyData.active_player_unum == strategyData.robot_model.unum: 
            drawer.annotation((0,10.5), "Dribbling to Goal" , drawer.Color.green, "status")
        else:
            drawer.clear_player()

        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            # --- MODIFIED: CALLING dribbleToTarget ---
            return self.customDribbleAndShoot(strategyData)
        else:
            if strategyData.player_unum in point_preferences:
                # --- Player 3 is a blocker, so this logic is only for Player 5 ---
                is_attacker = (my_unum == 5)
                
                if is_attacker:
                    strategyData.my_desired_position = point_preferences[strategyData.player_unum]
                else:
                    strategyData.my_desired_position = point_preferences[strategyData.player_unum]
            else:
                strategyData.my_desired_position = self.init_pos
            return self.move(strategyData.my_desired_position, orientation=strategyData.ball_dir)


        
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