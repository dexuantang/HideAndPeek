import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import math
from datetime import datetime, timedelta
import numpy as np

corner_coor = [28.5,46] #corner coordinate for calculating player's angle between the wall 
#get the latest time stamp where the sum of the angle of the two players equals to pi/2 
#(players have line of sight when the sum of the angle is larger than 90 degrees)
#calculate the time between first hit and latest line of sight event (this is time to damage)
#get the average time to damage for both players for each round

#currently the scipt is able to generate "player1_data" and "player2_data" arrays that contain all information 
#that is needed to calculate time to damage. These arrays have rows of "player angle to corner", "time", "trialID" "role" "hit"
#data points before the first round are marked with -1.
##Get db file path
def popupmsg(msg):
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text=msg, font=("Verdana", 10))
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    B1.pack()

root = tk.Tk()
root.withdraw()
popupmsg("Please select the first client db file")
file_path_1 = filedialog.askopenfilename()
client1_id = file_path_1.split("-")[7]
popupmsg("Please select the second client db file")
file_path_2  = filedialog.askopenfilename()
client2_id = file_path_2.split("-")[7]
popupmsg("Please select the server db file")
file_path_3  = filedialog.askopenfilename()
server_name = "server"

## Get server_data and split the data for peeker and defender. 
## The rows for server_data, server_data_peeker, server_data_defender are "time" "trailID" "playerID" and "role"

conn = sqlite3.connect(file_path_3)
cursor = conn.cursor()
cursor.execute("select * from PlayerConfigs;")
data = cursor.fetchall()
list_of_id = []
server_time = []
list_of_role = []
list_of_player = []
server_data = []

for row in data:
    id = row[1]
    time_stamp = datetime.strptime(((row[0])[11:23]),'%H:%M:%S.%f')
    role = row[14]
    player = row[2]
    list_of_id.append(id)
    server_time.append(time_stamp)
    list_of_role.append(role)
    list_of_player.append(player)
    
    server_data = np.array([np.array(server_time), np.array(list_of_id), np.array(list_of_player), np.array(list_of_role)])
    server_data_peeker = server_data[:,::2]
    server_data_defender= server_data[:,1::2]
    

def read_player_time(file):
    ##get time stamp from Player_Action
    player_time = []
    conn = sqlite3.connect(file)
    cursor = conn.cursor()
    cursor.execute("select * from Player_Action;")
    data = cursor.fetchall()
    for row in data:
        time = datetime.strptime(((row[0])[11:23]),'%H:%M:%S.%f')
        player_time.append(time)
    return player_time

def read_player_coor(file):
    ##get coordinates from Player_Action
    coor = []
    conn = sqlite3.connect(file)
    cursor = conn.cursor()
    cursor.execute("select * from Player_Action;")
    data = cursor.fetchall()
    for row in data:
        x = row[3]
        y = row[4]
        coor.append([x,y])
    return coor

def angle_calculation(corner_coor, player_coor):
    ## calculate the angle between the player and the wall in radians
    ## the sign of the output may not be correct
    list_of_angle = []
    for row in player_coor:
        dx = corner_coor[0] - row[0]
        dy = corner_coor[1] - row[1]
        angle = math.atan2(dy, dx)
        list_of_angle.append(angle)
    return list_of_angle
    

def read_round_id (server_data, player_time, player_id):
    ## Add trialID obtained from server to all data points in player action in client log
    round_id = []
    role = []
    for i in range(server_data.shape[1]):
        for j in range(len(player_time)):
            if (i+1 < server_data.shape[1]):
                if (server_data[0, i] <= player_time[j] < server_data[0, i+1]):
                    round_id.append(server_data[1,i])
                    if (server_data[2, i] == player_id):
                        role.append('peeker')
                    else:
                        role.append('defender')
            else:
                if (server_data[0, i] <= player_time[j]):
                    round_id.append(server_data_peeker[1,i])
                    if (server_data[2, i] == player_id):
                        role.append('peeker')
                    else:
                        role.append('defender')
    round_id = np.pad(round_id, (((len(player_time) - len(round_id)) ,0)), 'constant', constant_values = (-1,-1))
    role = np.pad(role, (((len(player_time) - len(role)) ,0)), 'constant', constant_values = (-1,-1))
    return [round_id , role]

def read_hits (file):
    ## get hit data and time stamp from remote player action
    time = []
    hit = []
    conn = sqlite3.connect(file)
    cursor = conn.cursor()
    cursor.execute("select * from Remote_Player_Action;")
    data = cursor.fetchall()
    for row in data:
        t = datetime.strptime(((row[0])[11:23]),'%H:%M:%S.%f')
        h = row[7]
        time.append(t)
        hit.append(h)
        time_hits = np.array([np.array(time), np.array(hit)])
    return time_hits

def hit_converter (time_hits, player_time):
    ## similar to read_round_id, add hit to the time stamp data in player action. not hit is marked with idle
    hit_arr = []
    for i in range(time_hits.shape[1]):
        hit_flag = 0
        for j in range(len(player_time)):
            if (i+1 < time_hits.shape[1]):
                if (time_hits[0, i] <= player_time[j] < time_hits[0, i+1]):
                    if hit_flag == 0:
                        hit_arr.append(time_hits[1,i])
                        hit_flag = 1
                    elif hit_flag == 1: 
                        hit_arr.append('idle')
            else:
                if (time_hits[0, i] <= player_time[j]):
                    if hit_flag == 0:
                        hit_arr.append(time_hits[1,i])
                        hit_flag = 1
                    elif hit_flag == 1: 
                        hit_arr.append('idle')
    hit_arr = np.pad(hit_arr, (((len(player_time) - len(hit_arr)) ,0)), 'constant', constant_values = (-1,-1))
    return hit_arr

def sum_angles_near_timestamp(arr1, arr2, time_threshold=0.5):
    ## arrs are player_data 
    ##unfinished
    ## this is a function that should be able to match up the time stamps for summing the angles
    result = []
    for i in range(arr1.shape[1]):
        angle_sum = arr1[0, i]
        original_index = i
        for j in range(arr2.shape[0]):
            time_diff = abs((arr2[1, j] - arr1[1, i]).total_seconds())
            if time_diff < time_threshold:
                angle_sum += arr2[0, j]
                original_index = j
                break
        result.append((original_index, angle_sum))
    return np.array(result)


player1_coor = read_player_coor(file_path_1)
player2_coor = read_player_coor(file_path_2)
player1_angles = angle_calculation(corner_coor, player1_coor)
player2_angles = angle_calculation(corner_coor, player2_coor)
player1_time = read_player_time(file_path_1)
player2_time = read_player_time(file_path_2)

player2_t_h = read_hits(file_path_1)
player1_t_h = read_hits(file_path_2)

hit_arr_1 = hit_converter(player1_t_h, player1_time)
hit_arr_2 = hit_converter(player2_t_h, player2_time)


player1_round_id = read_round_id (server_data_peeker, player1_time, client1_id)[0]
player1_role = read_round_id (server_data_peeker, player1_time, client1_id)[1]
player1_data = np.array([np.array(player1_angles), np.array(player1_time), np.array(player1_round_id), np.array(player1_role), np.array(hit_arr_1)])
player2_round_id = read_round_id (server_data_peeker, player2_time, client2_id)[0]
player2_role = read_round_id (server_data_peeker, player2_time, client2_id)[1]
player2_data = np.array([np.array(player2_angles), np.array(player2_time), np.array(player2_round_id), np.array(player2_role), np.array(hit_arr_2)])

x = sum_angles_near_timestamp(player1_data, player2_data)

            
            
            

    