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
            [-2.2, 0]  # 5: STRIKER 2 (Receiver/Charger) - Legal spot
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

        elif (strategyData.play_mode == self.world.M_OUR_KICKOFF):
            # This logic is correct and stays
            KICKER_UNUM = 3
            RECEIVER_UNUM = 5
            KICK_TARGET_POS = (1, 0)
            RECEIVER_START_POS = (0, -1) 
            
            if strategyData.robot_model.unum == KICKER_UNUM:
                self.kickTarget(strategyData, strategyData.mypos, KICK_TARGET_POS)
            elif strategyData.robot_model.unum == RECEIVER_UNUM:
                self.move(target_2d=RECEIVER_START_POS, orientation=strategyData.ball_dir)
            else:
                self.move(self.init_pos, orientation=strategyData.ball_dir)

        # --- THIS IS THE NEW LOGIC YOU ARE MISSING ---
        # If it's their set piece, run our main attack logic to intercept
        elif (strategyData.play_mode == self.world.M_THEIR_GOAL_KICK or
              strategyData.play_mode == self.world.M_THEIR_FREE_KICK or
              strategyData.play_mode == self.world.M_THEIR_KICK_IN or
              strategyData.play_mode == self.world.M_THEIR_CORNER_KICK):
            
            self.select_skill(strategyData)
        # --- END OF NEW LOGIC ---

        # --- "OUR SET PIECE" LOGIC (This STAYS) ---
        elif (strategyData.play_mode == self.world.M_OUR_GOAL_KICK or
              strategyData.play_mode == self.world.M_OUR_FREE_KICK or
              strategyData.play_mode == self.world.M_OUR_KICK_IN or
              strategyData.play_mode == self.world.M_OUR_CORNER_KICK):
            
            pass # Do nothing, wait for timeout
        # -----------------------------------------------
            
        else:
            # This is the main PlayOn logic
            if strategyData.play_mode == self.world.M_PLAY_ON:
                self.select_skill(strategyData)
            else:
                # This covers M_BEFORE_KICKOFF, MG_THEIR_KICK, etc.
                pass


        #--------------------------------------- 3. Broadcast
        self.radio.broadcast()

        #--------------------------------------- 4. Send to server
        if self.fat_proxy_cmd is None: # normal behavior
            self.scom.commit_and_send( strategyData.robot_model.get_command() )
        else: # fat proxy behavior
            self.scom.commit_and_send( self.fat_proxy_cmd.encode() ) 
            self.fat_proxy_cmd = ""



    def customDribbleAndShoot(self, strategyData):
        '''
        A custom, simple dribble that does not use the RL Dribble behavior.
        It uses self.move to align with the ball and push it towards the goal.
        1. Checks for a pass (if this player is the "Passer").
        2. Checks for a shot.
        3. Aligns behind the ball (with the "stuck" bug fixed).
        4. Moves through the ball to "push" it.
        '''
        # --- PARAMETERS ---
        GOAL_POS = (15.5, -0.3)      # Your Opponent goal target
        X_POSITION_TO_SHOOT = 11.0  # How close to goal before shooting
        
        # --- FIX #3: SHOOTING CHANNEL (Your new value) ---
        Y_SHOOTING_CHANNEL = 2.0    # Must be within y=2.0 and y=-2.0 to shoot
        
        # --- PASS LOGIC PARAMETERS ---
        PASSER_UNUM = 5             # Player 5 is now the Passer
        FINISHER_UNUM = 3           # Player 3 is now the Finisher
        ATTACK_ZONE_X = 10.0        # X-line to be considered "in the zone"
        KEEPER_SPOT_TOLERANCE = 1.5 # How far keeper must move from their spot to be "awake"
        MIN_PASS_SEPARATION = 2.5   # Player 3 must be at least 2.5m away (laterally)

        # --- FIX #2: GOALKEEPER THREAT ZONE (Your new logic) ---
        KEEPER_THREAT_ZONE_RADIUS = 2.0  # 2-unit radius around the keeper's default spot
        
        # --- Get current data ---
        my_pos = strategyData.mypos
        my_unum = strategyData.robot_model.unum
        ball_pos = strategyData.ball_2d
        ball_dist = strategyData.ball_dist
        
        
        # --- START OF NEW PASS LOGIC (Only runs for the "Passer" - Player 5) ---
        if my_unum == PASSER_UNUM:
            # Find the finisher (Player 3) and the keeper (Player 1 / index 0)
            finisher_pos = strategyData.teammate_positions[FINISHER_UNUM - 1]
            opp_keeper_pos = strategyData.opponent_positions[0]
            
            # Find the keeper's "stuck" spot
            OPPONENT_KEEPER_SPOT = np.array([14.0, 0.0]) # Their goal line
                
            # --- FIX #2: REVISED KEEPER LOGIC (Your logic) ---
            # 1. Check if keeper is frozen in their spot
            is_keeper_frozen = np.linalg.norm(opp_keeper_pos - OPPONENT_KEEPER_SPOT) <= KEEPER_SPOT_TOLERANCE
            
            # 2. Check if keeper is AWAKE but still INSIDE their "threat zone"
            keeper_dist_from_spot = np.linalg.norm(opp_keeper_pos - OPPONENT_KEEPER_SPOT)
            is_keeper_a_threat = (not is_keeper_frozen) and (keeper_dist_from_spot < KEEPER_THREAT_ZONE_RADIUS)
            # --- END FIX #2 ---

            # Check if both strikers are in the attack zone
            am_i_in_zone = my_pos[0] > ATTACK_ZONE_X
            is_finisher_in_zone = finisher_pos[0] > ATTACK_ZONE_X

            # "GOOD POSITION" CHECK
            is_laterally_separated = abs(finisher_pos[1] - my_pos[1]) > MIN_PASS_SEPARATION
            is_on_far_post = (finisher_pos[1] * my_pos[1]) < 0
            is_finisher_in_good_pos = is_finisher_in_zone and is_laterally_separated and is_on_far_post

            # NEW PASS CONDITION:
            # Pass ONLY IF:
            #   1. The keeper IS a threat (awake AND in their zone)
            #   2. AND I have the ball
            #   3. AND my teammate is in a good spot
            if is_keeper_a_threat and (ball_dist < 0.5) and am_i_in_zone and is_finisher_in_good_pos:
                # ...PASS to the other striker (The Finisher)
                return self.kickTarget(strategyData, my_pos, finisher_pos)
        
        # --- END OF NEW PASS LOGIC ---
        # If any pass condition fails, Player 5 will "thug it out"
        # and fall through to the dribble/shoot logic below.
        

        # --- FIX #3: "SHOOTING CHANNEL" LOGIC (Your new value) ---
        is_in_shoot_x_zone = my_pos[0] > X_POSITION_TO_SHOOT
        is_in_shoot_y_channel = abs(my_pos[1]) < Y_SHOOTING_CHANNEL

        # 1. CHECK TO SHOOT
        # Shoot if in X zone AND in Y channel AND have the ball
        if is_in_shoot_x_zone and is_in_shoot_y_channel and ball_dist < 0.5:
            return self.kickTarget(strategyData, my_pos, GOAL_POS)
        # --- END FIX #3 ---


        # --- FIX #1: "U-TURN" / "SCRAPPY DRIBBLE" FIX ---
        
        # --- START OF CHANGE ---
        # Tighter tolerance forces better alignment before PUSH stage
        is_aligned = strategyData.are_points_collinear(my_pos, ball_pos, GOAL_POS, tolerance=0.45)
        # --- END OF CHANGE ---

        is_in_front_of_ball = is_aligned and my_pos[0] > ball_pos[0] and my_pos[0] < GOAL_POS[0]

        # Using ball_dist > 0.4 for a "sticky" PUSH state
        if (not is_aligned) or (is_in_front_of_ball and ball_dist > 0.4):
            # STAGE 1: ALIGN
            # Using startat = -0.4 to give space for U-Turns
            startat = strategyData.point_in_direction(ball_pos, GOAL_POS, -0.4)
            # Move to this alignment spot, facing the ball
            return self.move(startat, orientation=strategyData.ball_dir, avoid_obstacles=True, timeout=999999)
        
        # Using ball_dist > 0.4
        elif ball_dist > 0.4:
            # STAGE 2: APPROACH
            # We ARE aligned AND behind the ball, but too far to push. Move closer to the ball.
            goal_dir = strategyData.GetDirectionRelativeToMyPositionAndTarget(GOAL_POS)
            return self.move(ball_pos, orientation=goal_dir, avoid_obstacles=True, timeout=999999)
            
        else:
            # STAGE 3: PUSH
            # We ARE aligned AND close enough (<= 0.4m). Push the ball forward.
            push_target = strategyData.point_in_direction(my_pos, GOAL_POS, 4)
            goal_dir = strategyData.GetDirectionRelativeToMyPositionAndTarget(push_target)
            return self.move(push_target, orientation=goal_dir, avoid_obstacles=False, timeout=999999)
        # --- END FIX #1 ---




    def select_skill(self,strategyData):
        #--------------------------------------- 2. Decide action

        drawer = self.world.draw
        
        path_draw_options = self.path_manager.draw_options

        target = (15,0) # Opponents Goal
        
        # --- START OF 2v1 STALL EXPLOIT LOGIC ---
        
        # 1. Define our roles
        HUNTER_UNUMS = [1]                # Player 1 is a full-time Hunter
        SPOT_BLOCKER_UNUMS = [2, 4]       # Player 2 & 4 will block Opp 5's spot
        TARGET_OPPONENT_INDEX = 4         # Target opponent player 5 (index 4)
        
        my_unum = strategyData.robot_model.unum
        
        default_pos = np.array([-100.0, -100.0]) 
        
        OPPONENT_5_SPOT = np.array([-12.0, 0.0])
        
        
        # --- NEW DYNAMIC ROLE FOR PLAYER 3 ---
        if my_unum == 3:
            if strategyData.ball_2d[0] < 1.0:
                HUNTER_UNUMS.append(3)
        # --- END OF DYNAMIC ROLE ---


        if my_unum in HUNTER_UNUMS:
            # --- HUNTER LOGIC (for Player 1 and, conditionally, Player 3) ---
            target_opp_pos = strategyData.opponent_positions[TARGET_OPPONENT_INDEX]

            if not np.array_equal(target_opp_pos, default_pos):
                strategyData.my_desired_position = target_opp_pos
                drawer.annotation(tuple(target_opp_pos), f"HUNTING OPP 5" , drawer.Color.red, "exploit")
            else:
                strategyData.my_desired_position = OPPONENT_5_SPOT
                drawer.annotation(tuple(OPPONENT_5_SPOT), f"HUNTING OPP 5 (SPOT)" , drawer.Color.orange, "exploit")

            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, timeout=999999)

        elif my_unum in SPOT_BLOCKER_UNUMS:
            # --- SPOT BLOCKER LOGIC (for Players 2 AND 4) ---
            strategyData.my_desired_position = OPPONENT_5_SPOT 
            drawer.annotation(tuple(OPPONENT_5_SPOT), f"BLOCKING OPP 5 SPOT" , drawer.Color.cyan, "exploit")

            target_opp_pos = strategyData.opponent_positions[TARGET_OPPONENT_INDEX]
            if not np.array_equal(target_opp_pos, default_pos):
                if np.sum((target_opp_pos - OPPONENT_5_SPOT) ** 2) < 4.0:
                    strategyData.my_desired_position = target_opp_pos
                    drawer.annotation(tuple(target_opp_pos), f"PUSHING OPP 5" , drawer.Color.red, "exploit")
            
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, timeout=999999)

        # --- END OF "STALL" EXPLOIT LOGIC ---
        # Player 5 (always) and Player 3 (conditionally)
        # will now execute the attacker code below.
        

        # --- ATTACKER LOGIC (for Player 5 and Player 3) ---
        
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
            # --- FIX #3: "PLAYER 3 PUSH UP" LOGIC ---
            is_finisher = (my_unum == 3 and strategyData.ball_2d[0] > 1.0)
            
            if is_finisher:
                # Override formation. Go to a "finisher spot"
                # (1.5m behind the ball, on the far post y=1.5)
                finisher_spot = (strategyData.ball_2d[0] - 1.5, 1.5)
                strategyData.my_desired_position = finisher_spot
            elif strategyData.player_unum in point_preferences:
                # Use normal formation spot
                strategyData.my_desired_position = point_preferences[strategyData.player_unum]
            else:
                # Fallback
                strategyData.my_desired_position = self.init_pos
            # --- END FIX #3 ---
            
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d)

        drawer.line(strategyData.mypos, strategyData.my_desired_position, 2,drawer.Color.blue,"target line")

        if not strategyData.IsFormationReady(point_preferences):     
            if strategyData.active_player_unum == strategyData.robot_model.unum:  # I am the active player
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
            return self.customDribbleAndShoot(strategyData)
        else:
            if strategyData.player_unum in point_preferences:
                # --- FIX #3: "PLAYER 3 PUSH UP" LOGIC (Repeated for this block) ---
                is_finisher = (my_unum == 3 and strategyData.ball_2d[0] > 1.0)
                
                if is_finisher:
                    finisher_spot = (strategyData.ball_2d[0] - 1.5, 1.5)
                    strategyData.my_desired_position = finisher_spot
                else:
                    strategyData.my_desired_position = point_preferences[strategyData.player_unum]
                # --- END FIX #3 ---
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