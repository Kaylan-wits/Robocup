from agent.Base_Agent import Base_Agent
from math_ops.Math_Ops import Math_Ops as M
import math
import numpy as np

from strategy.Assignment import role_assignment
from strategy.Assignment import pass_reciever_selector
from strategy.Strategy import Strategy 

from formation.Formation import GeneratePlayOn
from formation.Formation import GenerateDefense
from formation.Formation import GenerateFormation_5 



class Agent(Base_Agent):
    def __init__(self, host:str, agent_port:int, monitor_port:int, unum:int,
                 team_name:str, enable_log, enable_draw, wait_for_server=True, is_fat_proxy=False) -> None:
        
        
        robot_type = (0,1,1,1,2,3,3,3,4,4,4)[unum-1]

        
        
        super().__init__(host, agent_port, monitor_port, unum, robot_type, team_name, enable_log, enable_draw, True, wait_for_server, None)

        self.enable_draw = enable_draw
        self.state = 0  
        self.kick_direction = 0
        self.kick_distance = 0
        self.fat_proxy_cmd = "" if is_fat_proxy else None
        self.fat_proxy_walk = np.zeros(3) 

        
        
        
        init_positions_5 = [
            [-14, 0],   
            [-9, -3],   
            [-2.1, 1.],  
            [-9, 3],    
            [-2.2, 0]   
        ]
        self.init_pos = init_positions_5[unum-1] 
        


    def beam(self, avoid_center_circle=False):
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
        '''
        Walk to target position
        '''
        r = self.world.robot

        if self.fat_proxy_cmd is not None: 
            self.fat_proxy_move(target_2d, orientation, is_orientation_absolute) 
            return

        if avoid_obstacles:
            target_2d, _, distance_to_final_target = self.path_manager.get_path_to_target(
                target_2d, priority_unums=priority_unums, is_aggressive=is_aggressive, timeout=timeout)
        else:
            distance_to_final_target = np.linalg.norm(np.array(target_2d) - r.loc_head_position[:2])

        self.behavior.execute("Walk", target_2d, True, orientation, is_orientation_absolute, distance_to_final_target) 


    def kick(self, kick_direction=None, kick_distance=None, abort=False, enable_pass_command=False):
        '''
        Walk to ball and kick
        '''
        return self.behavior.execute("Dribble",None,None)

        if self.min_opponent_ball_dist < 1.45 and enable_pass_command:
            self.scom.commit_pass_command()

        self.kick_direction = self.kick_direction if kick_direction is None else kick_direction
        self.kick_distance = self.kick_distance if kick_distance is None else kick_distance

        if self.fat_proxy_cmd is None: 
            return self.behavior.execute("Basic_Kick", self.kick_direction, abort) 
        else: 
            return self.fat_proxy_kick()


    def kickTarget(self, strategyData, mypos_2d=(0,0),target_2d=(0,0), abort=False, enable_pass_command=False):
        '''
        Walk to ball and kick
        '''

        
        vector_to_target = np.array(target_2d) - np.array(mypos_2d)
        
        
        kick_distance = np.linalg.norm(vector_to_target)
        
        
        direction_radians = np.arctan2(vector_to_target[1], vector_to_target[0])
        
        
        kick_direction = np.degrees(direction_radians)


        if strategyData.min_opponent_ball_dist < 1.45 and enable_pass_command:
            self.scom.commit_pass_command()

        self.kick_direction = self.kick_direction if kick_direction is None else kick_direction
        self.kick_distance = self.kick_distance if kick_distance is None else kick_distance

        if self.fat_proxy_cmd is None: 
            return self.behavior.execute("Basic_Kick", self.kick_direction, abort) 
        else: 
            return self.fat_proxy_kick()


    def dribble(self, orientation=None, is_orientation_absolute=True, speed=1, stop=False):
        '''
        Dribble with the ball using the RL behavior.
        This function is a wrapper for the "Dribble" behavior,
        just like move() wraps "Walk" and kickTarget() wraps "Basic_Kick".
        '''
        if self.fat_proxy_cmd is not None:
            
            return self.fat_proxy_kick() 

        
        return self.behavior.execute("Dribble", orientation, is_orientation_absolute, speed, stop)

        
    

    def think_and_send(self):
        
        behavior = self.behavior
        strategyData = Strategy(self.world)
        d = self.world.draw
        
        
        default_pos = np.array([-100.0, -100.0])
        strategyData.teammate_positions = [pos if pos is not None else default_pos for pos in strategyData.teammate_positions]
        strategyData.opponent_positions = [pos if pos is not None else default_pos for pos in strategyData.opponent_positions]

        
        KICKER_UNUM = 3
        RECEIVER_UNUM = 5
        KICK_TARGET_POS = (1, 0)
        RECEIVER_START_POS = (0, -1) 
        
        
        
        ball_at_center = np.linalg.norm(strategyData.ball_2d) < 0.5


        if strategyData.play_mode == self.world.M_GAME_OVER:
            pass
        elif strategyData.PM_GROUP == self.world.MG_ACTIVE_BEAM:
            self.beam()
        elif strategyData.PM_GROUP == self.world.MG_PASSIVE_BEAM:
            self.beam(True) 
        elif self.state == 1 or (behavior.is_ready("Get_Up") and self.fat_proxy_cmd is None):
            self.state = 0 if behavior.execute("Get_Up") else 1

        
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
            
            pass 
            
        else:
            
            if strategyData.play_mode == self.world.M_PLAY_ON:
                
                
                
                if ball_at_center:
                    
                    
                    if strategyData.robot_model.unum == 5:
                        
                        self.kickTarget(strategyData, strategyData.mypos, KICK_TARGET_POS)
                    else:
                        
                        
                        
                        self.select_skill(strategyData)
                
                else:
                    
        
                    
                    self.select_skill(strategyData)
                

            else:
                
                pass


        
        self.radio.broadcast()

        
        if self.fat_proxy_cmd is None: 
            self.scom.commit_and_send( strategyData.robot_model.get_command() )
        else: 
            self.scom.commit_and_send( self.fat_proxy_cmd.encode() ) 
            self.fat_proxy_cmd = ""


    

    def customDribbleAndShoot(self, strategyData):
        
        GOAL_POS = (15.5, 0.7)      
        X_POSITION_TO_SHOOT = 11.0  
        
        
        my_pos = strategyData.mypos
        my_unum = strategyData.robot_model.unum
        ball_pos = strategyData.ball_2d
        ball_dist = strategyData.ball_dist

        
        opp_keeper_pos = strategyData.opponent_positions[0] 
        TAP_IN_X_POS = 14.0 
        PUSH_DIST = 0.4     

        
        is_in_shoot_x_zone = my_pos[0] > X_POSITION_TO_SHOOT
        is_at_goal_mouth = my_pos[0] > TAP_IN_X_POS 
        is_past_keeper = my_pos[0] > opp_keeper_pos[0]
        has_ball = ball_dist <= PUSH_DIST

        if is_at_goal_mouth and is_past_keeper and has_ball:
            
            goal_dir = strategyData.GetDirectionRelativeToMyPositionAndTarget(GOAL_POS)
            return self.move(GOAL_POS, orientation=goal_dir, avoid_obstacles=False, timeout=999999)
        
        
        
        if my_pos[0] > X_POSITION_TO_SHOOT and ball_dist < 0.5:
            return self.kickTarget(strategyData, my_pos, GOAL_POS)

        

        
        is_aligned = strategyData.are_points_collinear(my_pos, ball_pos, GOAL_POS, tolerance=0.45)

        is_in_front_of_ball = is_aligned and my_pos[0] > ball_pos[0] and my_pos[0] < GOAL_POS[0]

        
        
        if (not is_aligned) or (is_in_front_of_ball and ball_dist > 0.4):
            
            
            startat = strategyData.point_in_direction(ball_pos, GOAL_POS, -0.2)
            
            return self.move(startat, orientation=strategyData.ball_dir, avoid_obstacles=True, timeout=999999)

        

        elif ball_dist > 0.4:
            
            
            goal_dir = strategyData.GetDirectionRelativeToMyPositionAndTarget(GOAL_POS)
            return self.move(ball_pos, orientation=goal_dir, avoid_obstacles=True, timeout=999999)

        else:
            
            
            push_target = strategyData.point_in_direction(my_pos, GOAL_POS, 4)
            goal_dir = strategyData.GetDirectionRelativeToMyPositionAndTarget(push_target)
            
            return self.move(push_target, orientation=goal_dir, avoid_obstacles=False, timeout=999999)


    
    def select_skill(self,strategyData):
        
        drawer = self.world.draw
        
        path_draw_options = self.path_manager.draw_options

        target = (15,0) 

        DISTANCE_TOLERANCE = 0.15
        
        
        HUNTER_UNUMS = []           
        RIGHT_BLOCKER_UNUM = 1      
        

        
        BACK_BLOCKER_UNUM = 2       
        FRONT_BLOCKER_UNUM = 4      
        
        
        LEFT_BLOCKER_UNUM = 3       
        
        
        TARGET_OPPONENT_INDEX = 4       
        
        my_unum = strategyData.robot_model.unum
        
        default_pos = np.array([-100.0, -100.0]) 
        
        OPPONENT_5_SPOT = np.array([-12.0, 0.0])
        OUR_NET_POS = (-15.5, 0.0) 
        
        
        
        
        


        if my_unum in HUNTER_UNUMS:
            
            target_opp_pos = strategyData.opponent_positions[TARGET_OPPONENT_INDEX]

            if not np.array_equal(target_opp_pos, default_pos):
                strategyData.my_desired_position = target_opp_pos
                drawer.annotation(tuple(target_opp_pos), f"HUNTING OPP 5" , drawer.Color.red, "exploit")
            else:
                strategyData.my_desired_position = OPPONENT_5_SPOT
                drawer.annotation(tuple(OPPONENT_5_SPOT), f"HUNTING OPP 5 (SPOT)" , drawer.Color.orange, "exploit")

            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, timeout=999999)

        
        elif my_unum == RIGHT_BLOCKER_UNUM:
            
            player_1_target = OPPONENT_5_SPOT + np.array([0, -0.265]) 
            
            
            desired_orientation_degs = 90.0 
            drawer.annotation(tuple(player_1_target), f"RIGHT BLOCK (FACE -Y)" , drawer.Color.red, "exploit")
            
            
            strategyData.my_desired_position = player_1_target

            return self.move(
                strategyData.my_desired_position, 
                orientation=desired_orientation_degs, 
                is_orientation_absolute=True,
                avoid_obstacles=True,
                is_aggressive=False,
                timeout=999999
            )
        

        
        
        elif my_unum == LEFT_BLOCKER_UNUM:
            
            
            
            player_3_target = OPPONENT_5_SPOT + np.array([0, 0.265]) 
            final_orientation_degs = -90.0 
            
            
            distance_to_target = np.linalg.norm(np.array(strategyData.mypos) - player_3_target)
            
            
            if distance_to_target < DISTANCE_TOLERANCE:
                
                
                desired_orientation_degs = final_orientation_degs
                drawer.annotation(tuple(player_3_target), f"LEFT BLOCK (TURNING)" , drawer.Color.green, "exploit")
            else:
                
                
                desired_orientation_degs = strategyData.GetDirectionRelativeToMyPositionAndTarget(player_3_target)
                drawer.annotation(tuple(player_3_target), f"LEFT BLOCK (MOVING)" , drawer.Color.green, "exploit")
            
            
            strategyData.my_desired_position = player_3_target

            
            return self.move(
                strategyData.my_desired_position, 
                orientation=desired_orientation_degs, 
                is_orientation_absolute=True,
                avoid_obstacles=True,
                is_aggressive=False, 
                timeout=999999
            )
        

        
        elif my_unum == FRONT_BLOCKER_UNUM:
            
            player_4_target = strategyData.point_in_direction(
                position=OPPONENT_5_SPOT, 
                goal=OUR_NET_POS, 
                distance=0.265 
            )

            
            desired_orientation_degs = M.target_abs_angle(strategyData.mypos, OUR_NET_POS)
            drawer.annotation(tuple(player_4_target), f"FRONT BLOCK (FACE NET)" , drawer.Color.blue, "exploit")
            
            
            strategyData.my_desired_position = player_4_target

            return self.move(
                strategyData.my_desired_position, 
                orientation=desired_orientation_degs, 
                is_orientation_absolute=True,
                avoid_obstacles=True,
                is_aggressive=False,
                timeout=999999
            )
        

        
        elif my_unum == BACK_BLOCKER_UNUM:
            
            player_2_target = strategyData.point_in_direction(
                position=OPPONENT_5_SPOT, 
                goal=OUR_NET_POS, 
                distance=-0.265 
            )
            
            
            desired_orientation_degs = M.target_abs_angle(strategyData.mypos, OUR_NET_POS)
            drawer.annotation(tuple(player_2_target), f"BACK BLOCK (FACE NET)" , drawer.Color.cyan, "exploit")
            
            
            strategyData.my_desired_position = player_2_target
            
            return self.move(
                strategyData.my_desired_position, 
                orientation=desired_orientation_degs, 
                is_orientation_absolute=True,
                avoid_obstacles=True,
                is_aggressive=False,
                timeout=999999
            )
        

        
        
        
        
        
        
        formation_positions = []
        if strategyData.active_player_unum == strategyData.robot_model.unum: 
            drawer.annotation((0,10.5), "Role Assignment Phase" , drawer.Color.yellow, "status")
        else:
            drawer.clear("status") 	


        
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
        
        
        if strategyData.active_player_unum == strategyData.robot_model.unum: 	
            if strategyData.min_teammate_ball_dist < strategyData.min_opponent_ball_dist:
                if 0.0 <=strategyData.ball_speed <= 0.0:
                    strategyData.my_desired_position = strategyData.ball_2d
                    strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d) 	
        else:
            
            is_attacker = (my_unum == 5)
            
            if is_attacker:
                if strategyData.player_unum in point_preferences:
                    
                    strategyData.my_desired_position = point_preferences[strategyData.player_unum]
                else:
                    
                    strategyData.my_desired_position = self.init_pos
            elif strategyData.player_unum in point_preferences:
                
                strategyData.my_desired_position = point_preferences[strategyData.player_unum]
            else:
                
                strategyData.my_desired_position = self.init_pos
            
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.ball_2d)

        drawer.line(strategyData.mypos, strategyData.my_desired_position, 2,drawer.Color.blue,"target line")

        if not strategyData.IsFormationReady(point_preferences): 	
            if strategyData.active_player_unum == strategyData.robot_model.unum: 	
                
                return self.customDribbleAndShoot(strategyData)
            else:
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)
        
        
        
        if strategyData.active_player_unum == strategyData.robot_model.unum: 
            drawer.annotation((0,10.5), "Dribbling to Goal" , drawer.Color.green, "status")
        else:
            drawer.clear_player()

        if strategyData.active_player_unum == strategyData.robot_model.unum: 
            
            return self.customDribbleAndShoot(strategyData)
        else:
            if strategyData.player_unum in point_preferences:
                
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
            
            self.fat_proxy_cmd += f"(proxy kick 10 {M.normalize_deg( self.kick_direction 	- r.imu_torso_orientation ):.2f} 20)" 
            self.fat_proxy_walk = np.zeros(3) 
            return True
        else:
            self.fat_proxy_move(ball_2d-(-0.1,0), None, True) 
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