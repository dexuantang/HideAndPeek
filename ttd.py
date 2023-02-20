import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import math
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

corner_coor = [28.4,45.9] #corner coordinate for calculating player's angle between the wall 
#get the latest time stamp where the sum of the angle of the two players equals to pi/2 
#(players have line of sight when the sum of the angle is larger than 90 degrees)
#calculate the time between first hit and latest line of sight event (this is time to damage)
#get the average time to damage for both players for each round

#This script calculated ttd for a single round for both players. Data across all rounds are then manually stiched together in excel for analysis

##Get db file path
def popupmsg(msg):
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text=msg, font=("Verdana", 10))
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    B1.pack()

# Gets player id from file name, so it is sensitive to filepath name
# if player IDs are incorrect, check folder names in file path
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

popupmsg("Please select save directory")
savedir = filedialog.askdirectory()

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
list_of_latency = []

for row in data:
    id = row[1]
    time_stamp = datetime.strptime(((row[0])[11:23]),'%H:%M:%S.%f')
    role = row[14]
    player = row[2]
    latency = row[15]
    list_of_id.append(id)
    server_time.append(time_stamp)
    list_of_role.append(role)
    list_of_player.append(player)
    list_of_latency.append(latency)
    
    server_data = np.array([np.array(server_time), np.array(list_of_id), np.array(list_of_player), np.array(list_of_role), np.array(list_of_latency)])
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
        dx = abs(corner_coor[0] - row[0])
        dy = abs(corner_coor[1] - row[1])
        angle = math.atan(dx/dy)
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
                        role.append('PEEKER')
                    else:
                        role.append('DEFENDER')
            else:
                if (server_data[0, i] <= player_time[j]):
                    round_id.append(server_data_peeker[1,i])
                    if (server_data[2, i] == player_id):
                        role.append('PEEKER')
                    else:
                        role.append('DEFENDER')
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

def sum_angles_near_timestamp(arr1, arr2, time_threshold=0.015):
    ## arrs are player_data 
    ##unfinished
    ## this is a function that should be able to match up the time stamps for summing the angles
    result = []
    for i in range(arr1.shape[1]):
        angle_sum = arr1[0, i]
        time_at_sum = arr1[1, i]
        for j in range(arr2.shape[1]):
            time_diff = abs((arr2[1, j] - arr1[1, i]).total_seconds())
            if time_diff <= time_threshold:
                angle_sum -= arr2[0, j]
                time_at_sum = arr2[1, j]
                break
        result.append((time_at_sum, abs(angle_sum)))
    return np.array(result)

def split_log (player_data):
    round_list = []
    for i in range(54):
        index = np.where(player_data[2, :] == i)
        nround = player_data[: , index[0]]
        round_list.append(nround)
    return round_list

# filter out angles that are extremly large
def tlos (angle_sums_time, angle_threshold = 0.02):
    result = []
    peek_time = 0
    for i in range(angle_sums_time.shape[0]):
        if abs(angle_sums_time[i, 1]) <= angle_threshold:
            peek_time = angle_sums_time[i, 0]
            result.append((peek_time, angle_sums_time[i, 1]))
    return np.array(result)

def thits (player1_data_round, player2_data_round):
    result = []
    p1_index = np.where(player1_data_round[4, :] == 'hit')
    p1_result = player1_data_round[:, p1_index[0]]
    p2_index = np.where(player2_data_round[4, :] == 'hit')
    p2_result = player2_data_round[:, p2_index[0]]
    unsorted = np.hstack((p1_result, p2_result))
    result = unsorted[:, np.argsort(unsorted[1, :])]
    return result

# find local minimum by going backward till angle startes to increase
# local minimum should be at time at sight
def ttd(tlos, thits):
    ttd = []
    time_at_sight = []
    role = []
    result = []
    round_id = []
    last_angle = 10
    flag = 0
    for i in range(thits.shape[1]):
        time_at_damage = thits[1, i]
        flag = 0
        for j in range(tlos.shape[0]):
            curr_tlos = tlos[((tlos.shape[0] - 1) - j),0]
            curr_angle = tlos[((tlos.shape[0] - 1) - j),1]
            if time_at_damage - timedelta(0,5) <= curr_tlos <= time_at_damage - timedelta(0,0.22): #looking angles between 0.1 sec before hit to 5sec before hit
                if (curr_angle > last_angle) and (flag == 0):
                    time_at_sight = curr_tlos
                    ttd = time_at_damage - time_at_sight
                    role = thits[3,i]
                    round_id = thits[2,i]
                    flag = 1
                last_angle = curr_angle
        result.append((ttd, time_at_sight, role, round_id))
    return np.array(result)[1:,:]

# ttd method of finding the min value using numpy argmin within a certain time frame going backward from the time of damage
# this method does not provide good data
# def ttd(tlos, thits):
#     ttd = []
#     time_at_sight = []
#     role = []
#     result = []
#     round_id = []
#     for i in range(thits.shape[1]):
#         time_at_damage = thits[1, i]
#         for j in range(tlos.shape[0]):
#             curr_tlos = tlos[((tlos.shape[0] - 1) - j),0]
#             if time_at_damage - timedelta(0,0.5) <= curr_tlos <= time_at_damage:
#                 if (((tlos.shape[0] - 1) - j)-20) >= 0:
#                     time_frame = tlos[(((tlos.shape[0] - 1) - j)-20):((tlos.shape[0] - 1) - j),0]
#                     angles_at_time_frame = tlos[(((tlos.shape[0] - 1) - j)-20):((tlos.shape[0] - 1) - j),1]
#                 else:
#                     time_frame = tlos[:((tlos.shape[0] - 1) - j),0]
#                     angles_at_time_frame = tlos[:((tlos.shape[0] - 1) - j),1]
#                 time_at_sight_idx = np.argmin(angles_at_time_frame)
#                 time_at_sight = time_frame[time_at_sight_idx]   
#                 ttd = time_at_damage - time_at_sight
#                 role = thits[3,i]
#                 round_id = thits[2,i]
#         result.append((ttd, time_at_sight, role, round_id))
#     return np.array(result)[1:,:]
        
def add_latency(ttd, server_data):
    lat = np.empty([1,1])
    for i in range(ttd.shape[0]):
        lat_idx = np.where(((server_data[1,:] == ttd[i, 3]) & (server_data[3,:] == ttd[i, 2])))
        lat = np.append(lat,(server_data[4, lat_idx]))
    return lat[1:]
        

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

player1_data_rounds = split_log(player1_data)
player2_data_rounds = split_log(player2_data)

out = []

for i in range(54):

    y = sum_angles_near_timestamp(player1_data_rounds[i], player2_data_rounds[i])
    z = tlos(y)
    w = thits(player1_data_rounds[i], player2_data_rounds[i])
    td = ttd(z, w)
    j = 0
    last_tlos = []
    while 1:
        if j > td.shape[0] -1:
            break
        c_tlos = td[j, 1]
        if c_tlos == last_tlos:
            td = np.delete(td, j, 0)
            j = -1
        j = j+1
        last_tlos = c_tlos
    i = 0
    while 1:
        if i > td.shape[0] -1:
            break
        if td[i, 0] == []:
            td = np.delete(td, i, 0)
            i = -1
        i = i+1
    lat = add_latency(td, server_data)
    if len(td.shape) == 2:
        a = np.column_stack((td, lat))
    out.append(a) #output is a list of np arrays, first col is ttd, secon

peeker_ttd = np.array([])
defender_ttd = np.array([])
peeker_lat = np.array([])
defender_lat = np.array([])
for i in range(54):
    curr_round = out[i]
    peeker_idx = np.where(curr_round[:, 2] == 'PEEKER')
    peeker_ttd = np.concatenate((peeker_ttd, np.ravel(curr_round[peeker_idx, [0]])))
    peeker_lat = np.concatenate((peeker_lat, np.ravel(curr_round[peeker_idx, [4]])))
    defender_idx = np.where(curr_round[:, 2] == 'DEFENDER')
    defender_ttd = np.concatenate((defender_ttd, np.ravel(curr_round[defender_idx, [0]])))
    defender_lat = np.concatenate((defender_lat, np.ravel(curr_round[defender_idx, [4]])))
    
d_ttd = np.hstack(defender_ttd)
p_ttd = np.hstack(peeker_ttd)
d_lat = np.stack(defender_lat)
p_lat = np.stack(peeker_lat)

df1 = pd.DataFrame({"defender_ttd" : d_ttd, "defender_lat": d_lat})
df2 = pd.DataFrame({"peeker_ttd" : p_ttd, "peeker_lat": p_lat})
df1.to_csv((savedir + "/defender.csv"), index=False)
df2.to_csv((savedir + "/peeker.csv"), index=False)
    