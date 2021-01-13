####################################
import discord
import os
from replit import db
import random
from keep_alive import keep_alive
from collections import defaultdict
import datetime
import json
import time
import asyncio
import poker
import blackjack
import game_user
####################################

client = discord.Client()

class Command:
  def __init__(self, cmd, definition):
    self.c = cmd
    self.d = definition

reg_command_list = [
  Command('$asl', 'Produces the age, sex, and location of the waifu.'),

  Command('$lottery', 'View the current lottery if in progress and learn how to join it.'),

  Command('$buygf', 'Throw all your money at the girl of your dreams at a pathetic attempt to court her. You must be willing to face rejection.'),

  Command('$date', 'Ask the girl out on a date.'),

  Command('$hello', 'Produces a random pre-defined greeting. Different greetings exist for the boyfriend.'), 

  Command('$hug', 'Gives you a hug.'),

  Command('$money', 'View current balance.'),

  Command('$d, $daily', 'Obtain a random amount of money ranging from 0-100. Can repeat this command every minute.'),

  Command('[$g, $gamble, $r, $roll] <amount>', 'Gambles specified amount of money with a chance to win nothing, double, quadruple, or octuple what you bet.'),

  Command('[$g, $gamble, $r, $roll] odds', 'Displays the odds of winning the game.'),

  Command('$top', 'View the ranking for all users based on money.'),

  Command('[$p, $poker]', 'Gamble your money in a game of 5-hand poker.'),

  Command('[$bj, $blackjack]', 'Gamble your money in a game of blackjack.'),

  Command('$slots', 'Pay $100 to play a game of slots.')
]

### Sort the reg command list ###
reg_command_list.sort(key = lambda x: x.c)

### Global Variables ###
#HUG VARIABLES#
hug_gifs = ['https://tenor.com/bkzS2.gif', 'https://tenor.com/bhd4N.gif']
no_hug_gifs = ['https://tenor.com/bkPSv.gif', 'https://tenor.com/buO1p.gif', 'https://tenor.com/HNaT.gif']

#WAIFU VARIABLES#
already_dating_gifs = ['https://tenor.com/Zl6M.gif']

gf_cost = 10000

#ROLL VARIABLES#
roll_outcomes = [0, 2, 4, 8]
roll_chances = [0.7, 0.25, 0.05, 0.01]

#bad_outcome_gifs = ['https://tenor.com/Fxvj.gif', 'https://tenor.com/znPM.gif', 'https://tenor.com/zuiS.gif']
#double_outcome_gifs = ['https://tenor.com/HgiF.gif']
quad_outcome_gifs = ['https://tenor.com/Kbvu.gif']
octo_outcome_gifs = ['https://tenor.com/4qSf.gif']

#Lottery Variables#
lottery_default_cost = 100
lottery_entry_multipliers = [0, 1, 2] # 10^x
lottery_entry_cost = lottery_default_cost ** random.choice(lottery_entry_multipliers)
lottery_pot = 0

lottery_draw = False
lottery_start_time = 0
lottery_time = 300 # 5 minutes
lottery_min_to_start = 3
lottery_num_participants = 0
lottery_participants = []
lottery_channels = []

#Slot Variables
slot_cost = 50
slot_update_time = 1
slot_time_to_reward = 5
slot_icons = [":heart:", ":apple:", ":100:", ":seven:", ":watermelon:", ":repeat:"]
#Chance of a specific icon showing up
slot_odds = [0.3, 0.15, 0.05, 0.05, 0.15, 0.3]
slot_rewards = {':heart:': 200,
                ':apple:': 500,
                ':100:': 10000,
                ':seven:': 777777,
                ':watermelon:': 1000,
                ':repeat:': 0}

start_time = datetime.datetime.now()
daily_dict = defaultdict(lambda: start_time)

waifu_data = {}

############################
### END OF GLOBAL VARIABLES#
############################

### Load the waifu data ###
with open('waifu_data.json') as file:
  waifu_data = json.load(file)

#################################

def generate_help(cmds):
  help_list = []
  for cmd in cmds:
    c = cmd.c
    d = cmd.d

    line = "**{}**: {}".format(c, d)
    help_list.append(line)

  full_help = '\n'.join(help_list)
  return full_help

### GF PURCHASE FUNCTIONS ###

async def buygf(channel, user):
  user_str = str(user)

  if waifu_data['owner'] != user_str:
    if game_user.suff_money(user_str, waifu_data["cost"]):
      total_amount = game_user.user_dict[user_str]
      prev_owner = waifu_data['owner']

      game_user.user_dict[user_str] = 0
      waifu_data['owner'] = user_str
      waifu_data["cost"] = total_amount

      game_user.save(game_user.user_dict, 'user_data.json')
      game_user.save(waifu_data, 'waifu_data.json')

      return await channel.send("{} Wow {}, I can't believe you would give me ${}. I've always had my eye on you, even when I was dating {} to be honest. {} never left me satisfied, but I'm sure a real strong, mature man like you could do an excellent job. \n https://tenor.com/view/taylor-swift-love-you-point-heart-gif-4243547".format(user.mention, user_str, total_amount, prev_owner, prev_owner))

    else:
      return await channel.send("{} Haha! You're such a funny guy to think that you could afford me. Come back when you have more money (**${}**) Mr. Trash. \n https://tenor.com/view/anime-girl-laugh-cute-gif-12252557".format(user.mention, waifu_data["cost"]))

  else:
    if game_user.suff_money(user_str, waifu_data["cost"]):
      game_user.user_dict[user_str] -= waifu_data["cost"]
      game_user.save(game_user.user_dict, 'user_data.json')

      return await channel.send("{} Aww {}, thank you for the gift, you shouldn't have! \n https://tenor.com/view/smooch-blow-kiss-gif-5581156".format(user.mention , user_str))

    else:
      return await channel.send("{} Aww sweetie, you should save your money until you can afford a better gift valued at around ${}!".format(user.mention, waifu_data["cost"]))

####ROLL FUNCTIONS####

def generate_odds():

  list_odds = []

  for index, chance in enumerate(roll_chances):
    percentage = chance * 100
    odd = "{}X = {}%".format(roll_outcomes[index], percentage)

    list_odds.append(odd)

  return list_odds
  
list_odds = ', '.join(generate_odds())

async def show_odds(channel, user):
  return await channel.send("The current odds of winning are: {}".format(list_odds))

#User gambles x amount of money. If successful, doubles their money.
async def roll(channel, user, amt):
  user_str = str(user)
  if amt > 0:
    if game_user.suff_money(user_str, amt):
      cur_money = game_user.user_dict[user_str]

      #Subtract the cost of gambling first
      game_user.user_dict[user_str] = new_money = cur_money - amt

      #Outcome of Gamble
      outcome = random.choices(roll_outcomes, weights=roll_chances, k=1)[0]

      game_user.user_dict[user_str] = new_money + (amt * outcome)

      game_user.save(game_user.user_dict, 'user_data.json')

      if outcome == 0:
        return await channel.send("{} Yikes! You were unable to win any money. You now have **${}**. You can't settle on a loss, keep gambling!!!".format(user.mention, game_user.user_dict[user_str]))

      elif outcome == 2:
        return await channel.send("{} Congratulations! Your gamble paid off and you doubled your money! You now have **${}**. Keep the good luck rolling, **GO AGAIN**!!!".format(user.mention, game_user.user_dict[user_str]))

      elif outcome == 4:
        return await channel.send("{} HOLY SHIT! You quadrupled your money with a risky gamble. You now have **${}**. Keep the good luck rolling, GO AGAIN!!! \n {}".format(user.mention, game_user.user_dict[user_str], random.choice(quad_outcome_gifs)))
      
      else:
        return await channel.send("{} YOU LUCKY BAKA! You octupled your money with a risky gamble. You now have **${}**. Keep the good luck rolling, GO AGAIN!!! \n {}".format(user.mention, game_user.user_dict[user_str], random.choice(octo_outcome_gifs)))

    else:
      await channel.send("{} You have insufficient funds, please change the amount you would like to gamble or rethink your life choices.".format(user.mention))
  else:
    return await channel.send("{} Please enter a valid amount.".format(user.mention))
###########

### MONEY RELATED FUNCTIONS ###

async def rank(channel, user):
  dict_list = list(game_user.user_dict.items())
  dict_list.sort(key = lambda item: item[1], reverse=True)

  rank = 1
  list_ranking = []

  for i, j in dict_list:
    display = "**{}.** {}: ${}".format(rank, i, j)

    if rank == 1:
      display = ":first_place: {}: ${} :first_place:".format(i, j)

    elif rank == 2:
      display = ":second_place: {}: ${} :second_place:".format(i, j)

    elif rank == 3:
      display = ":third_place: {}: ${} :third_place:".format(i, j)
    
    if i == waifu_data["owner"]:
      display = display + " :heart:**BOYFRIEND**:heart: :eggplant:"

    rank += 1

    list_ranking.append(display)

  await channel.send("**FORTUNE FAVORS THE BOLD** \n \n" + '\n'.join(list_ranking))
  return

async def roll_daily(channel, user):
  user_str = str(user)

  cur_time = datetime.datetime.now()
  last_time = daily_dict[user_str]
  valid_time = last_time + datetime.timedelta(minutes=1)
  next_time = cur_time + datetime.timedelta(minutes=1)

  if cur_time >= valid_time:
    new_valid_time = next_time - cur_time
    new_time_str = str(new_valid_time).split(':')[1]

    pos_outcomes = [0, 10, 10, 10, 20, 20, 20, 40, 40, 60, 80, 100]

    outcome =  random.choice(pos_outcomes)

    if user_str in game_user.user_dict:
      game_user.user_dict[user_str] += outcome

    else:
      game_user.user_dict[user_str] = outcome

    game_user.save(game_user.user_dict, 'user_data.json')

    daily_dict[user_str] = cur_time

    if outcome == 0:
      return await channel.send("{} Unlucky, you didn't get any money! You can roll your daily again in {} minute(s).".format(user.mention, new_time_str))

    else:
      return await channel.send("{} You found ${} and have a total balance of ${}. You can roll your daily again in {} minute(s).".format(user.mention, outcome, game_user.user_dict[user_str], new_time_str))

  else:
    time_left = valid_time - cur_time
    time_left_str = str(time_left).split(':')[2].split('.')[0]

    return await channel.send("{} You can't roll your daily just yet. You can roll in {} seconds".format(user.mention, time_left_str))

### MISC HELPER FUNCTIONS

async def help(channel, user):
  new_list = []

  for cmd in reg_command_list:
    new_list.append("**{}**: {}".format(cmd.c, cmd.d))

  await channel.send('**__BOT COMMANDS:__** \n' + '\n'.join(new_list))

def is_right_format(txt, spaces):

  num = 0

  for i in range(len(txt)):
    if txt[i] == ' ':
      num += 1

  return num >= spaces

### GF CONTROL FUNCTIONS ###

def list_subjects():
  return ', '.join(db['unique_list_of_replies'])

def list_replies(subject):
  if subject in db:
    replies = ', '.join(db[subject]) + '.'
    return 'The following replies were found for {}: {}'.format(subject, replies)
  
  else:
    return "No replies found for subject: {}.".format(subject)

def get_reply(subject):
  if subject in db:
    return random.choice(db[subject])
  else:
    return

def add_reply(subject, msg):
  if subject in db:
    replies = db[subject]
    replies.append(msg)

    db[subject] = replies

  else:
    db[subject] = [msg]

  if subject not in db['unique_list_of_replies']:
      list_replies = db['unique_list_of_replies']
      list_replies.append(subject)

      db['unique_list_of_replies'] = list_replies

def delete_reply(subject, index):
  if subject in db:
    replies = db[subject]

    if len(replies) > index:
      del replies[index]
    else:
      return 

    db[subject] = replies

    if len(db[subject]) == 0:
      del db[subject]
    else:
      return

  else:
    return

async def asl(channel, user):
  await channel.send("{} Ohayou! My name is Zero Two. I am 18 years old, female, and from Vancouver, BC. Pleased to meet you!".format(user.mention))

async def date(channel, user):

  if waifu_data["owner"] != str(user):
    return await channel.send("{} You seem like a nice guy, but I really love {}. Don't worry, I won't tell him that this happened. We can still be friends!".format(user.mention, waifu_data['owner'].split('#')[0]))
  
  else:
    return await channel.send("{} We're already dating, you silly! \n {}".format(user.mention, random.choice(already_dating_gifs)))

async def get_owner(channel, user):
  await channel.send("{} My significant other is {}, but who knows. That could change ;).".format(user.mention, waifu_data['owner']))

  return

async def hello(channel, user):
  greeting_gifs = ['https://tenor.com/view/zero-two-002-cute-anime-wink-gif-11994868']
  cur_owner = waifu_data['owner']

  if cur_owner == user.name:
    await channel.send("{} \n {}".format(get_reply('hello'), random.choice(greeting_gifs)))

  else:
    await channel.send('{} Hello friend of {}! I am loyal to only {}, so I will not talk to you behind his back.'.format(user.mention, cur_owner, cur_owner))

  return

async def hug(channel, user):

  if waifu_data["owner"] == str(user):
    await channel.send("{} Darling, you look like you could use a hug :heart:. \n".format(user.mention) + random.choice(hug_gifs))

  else:
    await channel.send("{} Eww, no. \n".format(user.mention) + random.choice(no_hug_gifs))

def convert_time(seconds):
  #Converts seconds into minutes and seconds
  minutes = int(seconds // 60)
  seconds_remainder = round(seconds - (minutes * 60))

  return (minutes, seconds_remainder)

async def lottery_help(channel, user):
  global local_entry_cost
  global lottery_pot
  global lottery_start_time
  global lottery_num_participants

  if not lottery_draw:
    return await channel.send("{}\n Number of Entries: **{}**\n Number of Participants: **{}**\n Entry Cost: **${}**\n Current Pot: **${}**\n Time Until Draw: **NOT STARTED**\n \nJoin in on the action right now using '**$lottery join <entries>**'. ".format(user.mention, len(lottery_participants), lottery_num_participants, lottery_entry_cost, lottery_pot))

  else:
    cur_time = time.time()
    time_left = convert_time((lottery_time // 60) - (cur_time - lottery_start_time))
    
    return await channel.send("{}\n Number of Entries: **{}**\n Number of Participants: **{}**\n Entry Cost: **${}**\n Current Pot: **${}**\n Time Until Draw: {} minutes {} seconds\n \nJoin in on the action right now using '**$lottery join <entries>**'. ".format(user.mention, len(lottery_participants), lottery_num_participants, lottery_entry_cost, lottery_pot, time_left[0], time_left[1]))

def lottery_reset():
  #resets lottery game back to default values
  global lottery_participants
  global lottery_num_participants
  global lottery_pot
  global lottery_default_cost
  global lottery_entry_multipliers
  global lottery_entry_cost
  global lottery_draw
  global lottery_channels

  lottery_participants = []
  lottery_num_participants = 0
  lottery_draw = False
  lottery_channels = []

  # Set the entry cost to a random number
  lottery_entry_cost = lottery_default_cost ** random.choice(lottery_entry_multipliers)

  return

async def lottery_resolve(channel, user):

  global lottery_participants
  global lottery_num_participants
  global lottery_pot
  global lottery_draw
  global lottery_channels

  # Add the chance of no one winning to the participants
  # Can't add earlier or it will change number of participants
  lottery_participants = lottery_participants + [None]

  # Choose one from among the participants
  winner = random.choice(lottery_participants)

  # Wait before announcing the winner
  await asyncio.sleep(lottery_time)

  # No one wins so lottery is reset but pot remains intact
  if winner is None:

    for chan in lottery_channels:
        
      await chan.send("Unfortunately the lottery did not yield a winner this time! Don't be discouraged, this just means that there will be a bigger jackpot next time. Unless there is never a winner hehe. You don't want to miss out!\n https://tenor.com/TUDO.gif")

    # Reset the lottery game
    lottery_reset()

    return

  else:
    # User wins the lottery, payout the user

    game_user.user_dict[winner] += lottery_pot
    game_user.save(game_user.user_dict, 'user_data.json')

    for chan in lottery_channels:
      await chan.send("The lottery is over! The winner is **{}**, who wins the jackpot of **${}**. CONGRATULATIONS! May you use your money wisely by gambling it all.".format(winner, lottery_pot))

    # reset the lottery game
    lottery_reset()

    return

async def lottery(msg, channel, user):
  msg_split = msg.split(' ')
  user_str = str(user)
  
  if len(msg_split) == 1:
    return await lottery_help(channel, user)

  else:
    action = msg_split[1]

    if action == "join":
      global lottery_participants
      global lottery_num_participants
      global lottery_entry_cost
      global lottery_min_to_start
      global lottery_pot
      global lottery_time
      global lottery_start_time
      global lottery_draw
      global lottery_channels

      # Default is set to 1 entry when you type $lottery join
      num_entries = 1

      #If the player has 3 arguments, the 3rd one is the number of entries they want
      if len(msg_split) == 3:
        try:
          num_entries = int(msg_split[2])
        except:
          num_entries = 1

      total_cost = lottery_entry_cost * num_entries

      if game_user.suff_money(user_str, total_cost):
        game_user.user_dict[user_str] -= total_cost
        game_user.save(game_user.user_dict, 'user_data.json')
        
        lottery_pot += total_cost
        lottery_participants += [user_str] * num_entries
        lottery_num_participants = len(set(lottery_participants))

        # Build the list of channels that lottery is being done in
        if channel not in lottery_channels:
          lottery_channels.append(channel)
          
        await channel.send("{} You have entered the lottery with **{}** entries, raising the pot to **${}**. There are now **{}** entries. You now have **${}** remaining.".format(user.mention, num_entries, lottery_pot, len(lottery_participants), game_user.user_dict[user_str]))

        if lottery_num_participants >= lottery_min_to_start:
            #If not already drawing, then we must start timer
            if not lottery_draw:
              lottery_start_time = time.time()

              lottery_draw = True

              # All channels that participate will get this announcement
              for chan in lottery_channels:
                await chan.send("Enough players have entered the lottery. The lottery draw will be performed in {} minutes.".format(str(lottery_time // 60)))

              await lottery_resolve(channel, user)

      else:
        return await channel.send("{} You do not have enough money to join the lottery with {} entries.".format(user.mention, num_entries))

    else:
      return await lottery_help(channel, user)

def check_row(row):
    unique_row = set(row)
    is_match = len(unique_row) == 1
    first_icon = list(unique_row)[0]

    return (is_match, first_icon)

def slots_image(row1, row2, row3):
    row1_str = "   ".join(row1) + '\n\n'
    row2_str = "   ".join(row2) + '\n\n'
    row3_str = "   ".join(row3) + '\n\n'

    return row1_str + row2_str + row3_str

async def slots(channel, user):
    user_str = str(user)
    global slot_icons
    global slot_time_to_reward
    global slot_update_time

    # Check that the user has enough money
    if game_user.suff_money(user_str, slot_cost):
        # Take away the user's money
        game_user.user_dict[user_str] -= slot_cost
        game_user.save(game_user.user_dict, 'user_data.json')

        # Generate the first image for slots
        row_1 = random.choices(slot_icons, slot_odds, k=3)
        row_2 = random.choices(slot_icons, slot_odds, k=3)
        row_3 = random.choices(slot_icons, slot_odds, k=3)

        running_msg = "Calculating your reward"

        # Generate the slots image as a discord message
        img_msg = await channel.send("{}\n{}\n{}".format(user.mention, slots_image(row_1, row_2, row_3), running_msg))

        new_img = ""

        count = 0
        # Run the while loop and stop after x secs
        while count < (slot_time_to_reward / slot_update_time):
            # Randomize the icons shown for each row
            row_1 = random.choices(slot_icons, slot_odds, k=3)
            row_2 = random.choices(slot_icons, slot_odds, k=3)
            row_3 = random.choices(slot_icons, slot_odds, k=3)
            count += 1

            new_img = "{}\n{}\n".format(user.mention, slots_image(row_1, row_2, row_3))
            full_txt = new_img + running_msg

            running_msg = running_msg + '.'

            await img_msg.edit(content=full_txt)

            await asyncio.sleep(slot_update_time)

        rows = [row_1, row_2, row_3]

        # Determine if a row matches
        result = (False, "")

        for row in rows:
            result = check_row(row)

            if result[0]:
                break

        if result[0]:
            payout = slot_rewards[result[1]]
            game_user.user_dict[user_str] += payout
            game_user.save(game_user.user_dict, 'user_data.json')

            if result[1] == ":100:":
                jackpot_msg = "{} Jackpot! You won **${}** and now have a total of **${}**. Please spin again soon!".format(user.mention, payout, game_user.user_dict[user_str])

                new_txt = new_img + jackpot_msg
                await img_msg.edit(content=new_txt)

            elif result[1] == ":repeat:":
                free_spin_msg = "{} You haven't lost quite yet because you won a free spin!".format(user.mention)
                outcome_msg = new_img + free_spin_msg
                await img_msg.edit(content=outcome_msg)

                game_user.user_dict[user_str] += slot_cost

                return await slots(channel, user)

            else:
                win_msg = "{} Congratulations! You won **${}** and now have a total of **${}**. Please spin again soon!".format(user.mention, payout, game_user.user_dict[user_str])

                win_txt = new_img + win_msg

                return await img_msg.edit(content=win_txt)

        else:
          lose_msg = "{} Jinkies! This one is a loser. Please spin again soon!".format(user.mention)

          lose_txt = new_img + lose_msg
          
          return await img_msg.edit(content=lose_txt)

    else:
        await channel.send("{} You do not have sufficient money to play slots. The cost is ${}, but you have ${}. Please try again when you ain't broke.".format(user.mention, slot_cost, game_user.user_dict[user_str]))

async def roll_manage(msg, channel, user):
  msg_split = msg.split(' ')
  cmd_name = msg_split[0]
  
  if len(msg_split) == 1:
    return await channel.send("{} The available commands for '{}' are '{} odds' and '{} <amount>'".format(user.mention, cmd_name, cmd_name, cmd_name))

  action = msg_split[1]

  if action in roll_command_dict.keys():
    return await roll_command_dict[action](channel, user)
  
  else:
    try:
      amt = int(action)
    except:
      return await channel.send("{} Invalid amount specified for '$roll'. The amount specified should be a *number* greater than 0.".format(user.mention))

    return await roll(channel, user, amt)

async def give_self_money(channel, user):
  user_str = str(user)

  if user_str == "North#7279":
    game_user.user_dict[user_str] += 10000
    return await channel.send("Giving North $10000.")

  else:
    return

## Gambling Variables ##

roll_command_dict = {'odds': show_odds}

gamble_command_dict = {'$poker': poker.manage, 
  '$p': poker.manage,
  '$blackjack': blackjack.manage,
  '$bj': blackjack.manage,
  '$roll': roll_manage,
  '$r': roll_manage,
  '$g': roll_manage,
  '$gamble': roll_manage,
  '$lot': lottery,
  '$lottery': lottery}

#########################################

#DEFINE WAIFU MANAGEMENT COMMANDS HERE#
waifu_owner_commands = {}
#######################################

async def complex_commands(cmd, channel, user):
  # Our complex commands are:
  # poker, blackjack, gamble, waifu owner commands
  cmd_name = cmd.split(' ')[0]

  if cmd_name in gamble_command_dict.keys():
    return await gamble_command_dict[cmd_name](cmd, channel, user)

  else:
    if cmd in waifu_owner_commands.keys():
      await channel.send("Waifu commands are currently unavailable due to an update in progress. I kindly appreciate your patience during these troubling times.".format(user.mention, cmd))
      return

    else:
      await channel.send("{} No command was found for '{}'. Please consult '$help' for more information.".format(user.mention, cmd))
      return 

### END OF REGULAR FUNCTION DEFINITIONS ###
### EVENT-BASED FUNCTIONS ###

reg_command_dict = {"$asl": asl, "$buygf": buygf, "$date": date, "$money": game_user.fetch_money, "$d": roll_daily, "$daily": roll_daily, "$owner": get_owner, "$top": rank, "$hello": hello, "$help": help, "$hug": hug, "$give": game_user.give_money, "$givemoney": game_user.give_money, "$setmoney": give_self_money, "$slots": slots}

@client.event
async def on_ready():
  activity = discord.Activity(name="how to rig casinos", type=discord.ActivityType.watching)

  await client.change_presence(status=discord.Status.idle, activity=activity)
  print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    author = message.author
    msg = message.content
    channel = message.channel

    if msg.startswith("$"):

      if author == client.user:
        return

      elif msg.startswith("$give") or msg.startswith("$givemoney"):
        try:
          recipient = msg.split(' ')[1]
          amount = int(msg.split(' ')[2])
        except:
          return await channel.send("{} Wrong format for command. Correct usage is '$give <username> <amount>'.".format(author.mention))

        return await give_money(channel, author, recipient, amount)
      
      else:
        if msg in reg_command_dict.keys():
          return await reg_command_dict[msg](channel, author)
        
        else:
          return await complex_commands(msg, channel, author)

      '''
      # If the author of the message uses commands
      if str(author) == waifu_data["owner"]:
        if msg.startswith('$'):
          if msg.startswith('$newreply'):
            txt = msg

            if is_right_format(txt, 2):
              to_add = txt.split(' ', 2)
              subject = to_add[1]
              msg = to_add[2]

              add_reply(subject, msg)
              await message.channel.send('Added greeting, "{}" for {}'.format(msg, subject))
            
            else:
              await message.channel.send("Wrong format for command. Correct usage is '$newreply <subject> <msg>'.")

          elif msg.startswith('$delreply'):
            txt = msg

            if is_right_format(txt, 2):
              to_del = txt.split(' ', 2)
              subject = to_del[1]
              idx = int(to_del[2])

              if not isinstance(idx, int):
                await message.channel.send("Wrong format for command. Correct usage is '$delreply <subject> <index>'.")

              else:
                delete_reply(subject, idx)
                await message.channel.send('Deleted {} reply at index {}.'.format(idx, subject))
            
            else:
              await message.channel.send("Wrong format for command. Correct usage is '$delreply <subject> <index>'.")

          elif msg.startswith('$replies'):
            txt = msg

            if is_right_format(txt, 1):
              subject = txt.split(' ', 1)[1]
              await message.channel.send(list_replies(subject))

            else:
              await message.channel.send("Wrong format for command. Correct usage is '$replies <subject>'.")

          elif msg.startswith('$subjects'):
            await message.channel.send('SUBJECTS: \n' + list_subjects())

          else:
            command = msg.replace('$', '')

            if (command in db['unique_list_of_replies']) and (command not in reg_command_dict.keys()):
              await message.channel.send(get_reply(command))
      '''

    else:
      return

keep_alive()
client.run(os.getenv('TOKEN'))