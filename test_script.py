import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

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

conn = sqlite3.connect(file_path_1)
cursor = conn.cursor()
cursor.execute("select * from Player_Action;")
data = cursor.fetchall()
last_state = ''
id = 0
round_starts = []
for row in data:
    state = row[6]
    if state != last_state:
        if state == "initialNetworkedState":
            round_starts.append(row[0])
        last_state = state
round_starts.append(row[0])

def read_from_db(file):
    conn = sqlite3.connect(file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Remote_Player_Action')
    data = cursor.fetchall()
    hits = []
    r = 1
    sum = 0
    print(round_starts[3])
    print(round_starts[4])
    for row in data:
        if (row[0] < round_starts[r]):
            sum += 1
        else:
            hits.append(sum)
            sum = 1
            r += 1
        if (file == file_path_1):
            print(row, " _ round " + str(r))
    hits.append(sum)
    return hits


client2hits = read_from_db(file_path_1)
client1hits = read_from_db(file_path_2)

client1_roundwins = 0
client2_roundwins = 0
for i in range(len(client1hits)):
    print("Round ", i+1)
    print(client1_name + " : " + str(client1hits[i]) + "  -  " +client2_name + " : " + str(client2hits[i]))
    if (client1hits[i] > client2hits[i]):
        client1_roundwins += 1
    elif (client2hits[i] > client1hits[i]):
        client2_roundwins += 1

print("Total Rounds Won:")
print(client1_name + " won " + str(client1_roundwins) + " rounds")
print(client2_name + " won " + str(client2_roundwins) + " rounds")
if (client1_roundwins > client2_roundwins):
    print(client1_name + " wins!")
elif (client2_roundwins > client1_roundwins):
    print(client2_name + " wins!")
else:
    print("Tie!")