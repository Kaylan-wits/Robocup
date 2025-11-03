import numpy as np
import math


NUM_PLAYERS = 5


def calculateEuclideanDistance(initialPos, formationPos):
    initialPosX, initialPosY = initialPos
    formationPosX, formationPosY = formationPos
    
    xDiff = formationPosX - initialPosX
    yDiff = formationPosY - initialPosY
    
    distance = math.sqrt((xDiff ** 2) + (yDiff ** 2))
    
    return distance

def findMinZeroRow(zeroMatrix, markedPositions):
    minRowInfo = [float('inf'), -1]

    
    for rowIndex in range(NUM_PLAYERS): 
        zeroCount = np.sum(zeroMatrix[rowIndex])
        if zeroCount > 0 and zeroCount < minRowInfo[0]:
            minRowInfo = [zeroCount, rowIndex]

    if minRowInfo[1] == -1: 
        return

    zeroColIndex = np.where(zeroMatrix[minRowInfo[1]])[0][0]
    markedPositions.append((minRowInfo[1], zeroColIndex))
    zeroMatrix[minRowInfo[1], :] = False
    zeroMatrix[:, zeroColIndex] = False

def identifyMarkedPositions(matrix):
    boolZeroMatrix = (matrix == 0)
    boolZeroMatrixCopy = boolZeroMatrix.copy()

    markedPositions = []
    while np.any(boolZeroMatrixCopy):
        findMinZeroRow(boolZeroMatrixCopy, markedPositions)

    markedRows, markedCols = zip(*markedPositions) if markedPositions else ([], [])
    unmarkedRows = list(set(range(matrix.shape[0])) - set(markedRows))

    finalMarkedCols = []
    hasUpdates = True
    while hasUpdates:
        hasUpdates = False
        for row in unmarkedRows:
            for col in range(boolZeroMatrix.shape[1]):
                if boolZeroMatrix[row, col] and col not in finalMarkedCols:
                    finalMarkedCols.append(col)
                    hasUpdates = True

        for row, col in markedPositions:
            if row not in unmarkedRows and col in finalMarkedCols:
                unmarkedRows.append(row)
                hasUpdates = True

    finalMarkedRows = list(set(range(matrix.shape[0])) - set(unmarkedRows))

    return markedPositions, finalMarkedRows, finalMarkedCols

def modifyMatrix(matrix, coveredRows, coveredCols):
    modifiedMatrix = matrix.copy()
    nonZeroElements = []
    for r in range(len(modifiedMatrix)):
        if r not in coveredRows:
            for c in range(len(modifiedMatrix[r])):
                if c not in coveredCols:
                    nonZeroElements.append(modifiedMatrix[r, c])
    
    
    if not nonZeroElements:
        return modifiedMatrix
    

    smallestValue = min(nonZeroElements)
    for r in range(len(modifiedMatrix)):
        if r not in coveredRows:
            modifiedMatrix[r] -= smallestValue
    for c in coveredCols:
        modifiedMatrix[:, c] += smallestValue
            
    return modifiedMatrix

def hungarianMethod(matrix): 
    adjustedMatrix = matrix.copy()
    rowMin = np.min(adjustedMatrix, axis=1)
    adjustedMatrix = adjustedMatrix - rowMin[:, np.newaxis]
    colMin=np.min(adjustedMatrix, axis=0)
    adjustedMatrix= adjustedMatrix-colMin
        
    totalZeros = 0
    
    while totalZeros < NUM_PLAYERS:
        positions, markedRows, markedCols = identifyMarkedPositions(adjustedMatrix)
        totalZeros = len(markedRows) + len(markedCols)

        if totalZeros < NUM_PLAYERS:
        
            adjustedMatrix = modifyMatrix(adjustedMatrix, markedRows, markedCols)

    return positions

def role_assignment(initialPos, formation):
    
    cost_matrix = np.zeros((NUM_PLAYERS, NUM_PLAYERS))
    
    for r in range(NUM_PLAYERS):
        for c in range(NUM_PLAYERS):
    
            cost_matrix[r][c] = calculateEuclideanDistance(initialPos[r], formation[c])
    cost_copy = cost_matrix.copy()
    positions = hungarianMethod(cost_copy)
    point_preferences = {}
    for i, (row, col) in enumerate(positions):
        point_preferences[row + 1] = formation[col]
    return point_preferences


def pass_reciever_selector(player_unum, teammate_positions,opponent_positions,final_target):
    """
    Selects the target location of the player who is receiving the ball based on the closest teammate ahead.

    Parameters
    ----------
    player_unum : int
        The unique number of the player making the pass.
    teammate_positions : list of tuples
        List of (x, y) positions for all teammates.
    final_target : tuple
        The final target location you wish the ball to finish at.

    Returns
    -------
    target : tuple
        The target location in 2D of the player receiving the ball.
    """
    final_target_x, final_target_y = final_target
    final_target_x = 15
    final_target_y = 0.5
    final_target = (final_target_x,final_target_y)
    
    
    
    if player_unum - 1 >= len(teammate_positions):
        
        return None, None
    my_position = teammate_positions[player_unum - 1]   
    

    
    teammateOptimal =[]
    optimal_player = None
    optimal_distance = float('inf')
    second_target=None
    for i, teammate_position in enumerate(teammate_positions):
        
        if i == player_unum - 1:
            continue
        
        
        if teammate_position is None or my_position is None:
            continue
        

        if (teammate_position[0] - my_position[0] >= 1.5):
            distance = calculateEuclideanDistance(my_position,teammate_position)
            distance = round(distance,0)

            teammateOptimal.append((distance,teammate_position,i+1))
    teammateOptimal.sort(key=lambda x:x[0])
    
    
    if my_position is None:
        return None, None
    

    if final_target_x - my_position[0] <= 3.5 and -3 <= my_position[1] <= 3:  
        return final_target,second_target
    
    close_teammates = []
    if len(teammateOptimal) != 0:     
        distance_firstPlayer = teammateOptimal[0][0]
        for distance, teammate_position, index in teammateOptimal:
            if abs(distance-distance_firstPlayer) <= 1:
                close_teammates.append((distance,teammate_position,index))
        close_teammates.sort(key=lambda x:x[2])
        if len(close_teammates) > 1:
            optimal_distance, optimal_player,optimal_index = close_teammates[0][0],close_teammates[0][1],close_teammates[0][2]
            optimal_playerx,optimal_playery = optimal_player
            optimal_playerx = optimal_playerx + 0.5
            optimal_playery = optimal_playery +0.5
            target = (optimal_playerx,optimal_playery)
        else:
            optimal_distance, optimal_player,optimal_index = teammateOptimal[0][0],teammateOptimal[0][1],teammateOptimal[0][2]
            optimal_playerx,optimal_playery = optimal_player
            optimal_playerx = optimal_playerx + 0.5
            optimal_playery = optimal_playery +0.5
            target = (optimal_playerx,optimal_playery)
            target = optimal_player
        
        if (optimal_distance>7):
            target = None
            secondOptimal=[]
            for i, teammate_position in enumerate(teammate_positions):

                if i == player_unum - 1:
                    continue
                
                if teammate_position is None or my_position is None:
                    continue
              
                if (teammate_position[0] - my_position[0] >= -3):
                    distance = calculateEuclideanDistance(my_position,teammate_position)
                    distance = round(distance,0)
                    if distance<=5:
                        secondOptimal.append((distance,teammate_position,i+1))
            if len(secondOptimal) != 0:
                secondOptimal.sort(key=lambda x:x[0])
                second_target=secondOptimal[0][1]
    else:
        target = None
    return target,second_target