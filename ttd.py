import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import math
from datetime import datetime

corner_coor = [28.5,46]

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
client1_name = file_path_1.split("_")[-1].split(".")[0]
popupmsg("Please select the second client db file")
file_path_2  = filedialog.askopenfilename()
client2_name = file_path_2.split("_")[-1].split(".")[0]
popupmsg("Please select the server db file")
file_path_3  = filedialog.askopenfilename()
server_name = "server"


conn = sqlite3.connect(file_path_3)
cursor = conn.cursor()
cursor.execute("select * from PlayerConfigs;")
data = cursor.fetchall()
list_of_id = []
list_of_time = []
list_of_role = []
list_of_player = []

for row in data:
    id = row[1]
    time_stamp = datetime.strptime(((row[0])[11:23]),'%H:%M:%S.%f')
    role = row[14]
    player = row[2]
    list_of_id.append(id)
    list_of_time.append(time_stamp)
    list_of_role.append(role)
    list_of_player.append(player)

def read_player_time(file):
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
    list_of_angle = []
    for row in player_coor:
        dx = corner_coor[0] - row[0]
        dy = corner_coor[1] - row[1]
        angle = math.atan2(dy, dx)
        list_of_angle.append(angle)
    return list_of_angle
    

player1_coor = read_player_coor(file_path_1)
player2_coor = read_player_coor(file_path_2)
player1_angles = angle_calculation(corner_coor, player1_coor)
player2_angles = angle_calculation(corner_coor, player2_coor)
player1_time = read_player_time(file_path_1)
player2_time = read_player_time(file_path_2)
