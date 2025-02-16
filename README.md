# discord-bot

Bot Capabilities:

1.	Add users manually 
2.	Add users automaticly when they first write in general
3.	Delete users
4.	Change the value of users. 
5.	Show all users' values.(In a list)
6.	Show a user's value via DM.
7.	Track people messages in certain channels to add certain value when they write in chat 

Commands:

·	!add_user <user>: Adds a user with a base value of 0. (Admin only)  
·	!change_value  <user> <amount>: Changes a user's value by the specified amount. (Admin only) 
·	!delete_user <user>: Deletes a user. (Admin only)  
·	!change_name  <user> <new_name>: Changes a user's name. (Admin  only)  
·	!show_all: Shows all users' values. (Admin only)  
·	!show_value: Shows the value of the user who invoked the command via DM.  
·	!change_value_name <new_name>: Changes the name of the value (e.g., points, score). (Admin only) 
· !show_value <user>

Setup guide

Install the required libraries: 
  pip install discord.py
Create a config.txt  file and add your bot token in it. (SAME DIRECTORY!)
user_values.json automaticly generates itself if there is none

