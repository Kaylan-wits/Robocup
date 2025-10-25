from agent.Base_Agent import Base_Agent
from math_ops.Math_Ops import Math_Ops as M
import math
import numpy as np

from strategy.Assignment import role_assignment
from strategy.Assignment import pass_reciever_selector
from strategy.Strategy import Strategy 

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
            
    # --- START OF MERGED FUNCTION ---
    # This is Amaan's dribble logic, renamed to be clear
    def dribbleToTarget(self, strategyData, MyNum=0, position=(0,0), ball_pos=(0.0), aim=(15.5,0)):
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
            return self.move(strategyData.my_desired_position, orientation=strategyData.ball_dir, avoid_obstacles=True)
        
        elif strategyData.ball_dist > 0.5: #im now colinear so now go close enough to ball
            strategyData.point_in_direction(position, aim)
            strategyData.my_desired_position = (strategyData.ball_2d)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)
        
        else: #ball_dist is now less than 0.5 and im in line so i can move forward
            towards = strategyData.point_in_direction(position, aim, 4)
            strategyData.my_desired_position = (towards)
            strategyData.my_desired_orientation = strategyData.GetDirectionRelativeToMyPositionAndTarget(strategyData.my_desired_position)
            return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation, avoid_obstacles=False)
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
            self.move(self.init_pos, orientation=strategyData.ball_dir)
        elif (strategyData.play_mode == self.world.M_OUR_KICKOFF):
            if strategyData.robot_model.unum == 9:
                self.kickTarget(strategyData,strategyData.mypos,(15,10))
        elif (strategyData.play_mode == self.world.M_OUR_GOAL_KICK):
            if strategyData.robot_model.unum == 1:
                self.kickTarget(strategyData,strategyData.mypos,(15,0))
        else:
            if strategyData.play_mode != self.world.M_BEFORE_KICKOFF:
                self.select_skill(strategyData)
            else:
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
        #------------------------------------------------------
        #Role Assignment
        formation_positions = []
        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            drawer.annotation((0,10.5), "Role Assignment Phase" , drawer.Color.yellow, "status")
        else:
            drawer.clear("status")    


        # Determine formation based on opponent proximity
        visible_opponents = [pos for pos in strategyData.opponent_positions if pos[0] != -100.0] #

        if len(visible_opponents) > 0:
            # --- MODIFICATION: Increased margin from 0.3 to 1.0 ---
            if strategyData.min_opponent_ball_dist + 1.0 < strategyData.min_teammate_ball_dist:
                formation_positions = GenerateDefense(visible_opponents) #
                drawer.annotation((0,10.5), "Mode: DEFENSE" , drawer.Color.red, "status") #
            # --- ADDED ELSE BLOCK ---
            else: # Opponent is not significantly closer, stay in attack
                # Pass ball's X coordinate to the dynamic formation generator
                formation_positions = GeneratePlayOn(strategyData.ball_2d[0]) #
                drawer.annotation((0,10.5), "Mode: ATTACK / PLAY ON" , drawer.Color.green, "status") #
        # --- ADDED OUTER ELSE BLOCK ---
        else: # No opponents visible, default to attack
            formation_positions = GeneratePlayOn(strategyData.ball_2d[0]) #
            drawer.annotation((0,10.5), "Mode: ATTACK / PLAY ON" , drawer.Color.green, "status") #



        # Pad teammate positions if needed
        current_teammates = strategyData.teammate_positions
        # Filter out any None or dummy values before padding
        valid_teammates = [pos for pos in current_teammates if pos is not None and not np.array_equal(pos, np.array([-100.0, -100.0]))]
        num_teammates = len(valid_teammates)
        dummy_pos = np.array([-100.0, -100.0])
        if num_teammates < 11:
            padded_teammates = valid_teammates + [dummy_pos] * (11 - num_teammates)
        else:
            padded_teammates = valid_teammates[:11] # Take first 11 valid

        # Pad formation positions if needed (double check, Formation.py should handle this)
        current_formation = formation_positions
        num_formation = len(current_formation)
        if num_formation < 11:
            padded_formation = current_formation + [dummy_pos] * (11 - num_formation)
        else:
            padded_formation = current_formation[:11]

        # Now call role_assignment with guaranteed 11-element lists
        point_preferences = role_assignment(padded_teammates, padded_formation)
        # --- END PADDING FIX ---
        
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

        if not strategyData.IsFormationReady(point_preferences):   
            target,second_target = pass_reciever_selector(strategyData.player_unum, strategyData.teammate_positions,strategyData.opponent_positions,(15,0))
            if strategyData.active_player_unum == strategyData.robot_model.unum:  # I am the active player
                if (target is not None):
                    drawer.line(strategyData.mypos, target, 2,drawer.Color.red,"pass line")
                    return self.kickTarget(strategyData,strategyData.mypos,target)
                elif(second_target is not None):
                    return self.kickTarget(strategyData,strategyData.mypos,second_target)
                else:
                    # --- MODIFICATION ---
                    # Calling the dribble function instead of kickTarget
                    return self.dribbleToTarget(strategyData, strategyData.player_unum, strategyData.mypos, strategyData.ball_2d, (15,0.5))
                    # --- END MODIFICATION ---
            else:
                return self.move(strategyData.my_desired_position, orientation=strategyData.my_desired_orientation)
        
        #------------------------------------------------------
        #Pass Selector
        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            drawer.annotation((0,10.5), "Pass Selector Phase" , drawer.Color.yellow, "status")
        else:
            drawer.clear_player()

        if strategyData.active_player_unum == strategyData.robot_model.unum: # I am the active player 
            target,second_target = pass_reciever_selector(strategyData.player_unum, strategyData.teammate_positions,strategyData.opponent_positions,(15,0))
            if (target is not None):
                drawer.line(strategyData.mypos, target, 2,drawer.Color.red,"pass line")
                return self.kickTarget(strategyData,strategyData.mypos,target)
            elif(second_target is not None):
                return self.kickTarget(strategyData,strategyData.mypos,second_target)
            else:
                # --- MODIFICATION ---
                # Calling the dribble function instead of kickTarget
                return self.dribbleToTarget(strategyData, strategyData.player_unum, strategyData.mypos, strategyData.ball_2d, (15,0.5))
                # --- END MODIFICATION ---
        else:
            # Check if self.player_unum is in point_preferences before accessing
            if strategyData.player_unum in point_preferences:
                strategyData.my_desired_position = point_preferences[strategyData.player_unum]
            else:
                strategyData.my_desired_position = self.init_pos
            return self.move(strategyData.my_desired_position, orientation=strategyData.ball_dir)

    #--------------------------------------- Fat proxy auxiliary methods

 