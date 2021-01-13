####################################
import discord
from collections import defaultdict
import game_user
import cards
####################################
class Command:
  def __init__(self, cmd, definition):
    self.c = cmd
    self.d = definition

win_multiplier = 1.5
#Keeps track of active games that users have
poker_data = defaultdict(bool)

poker_outcomes = {1: "High Card", 2: "One Pair", 3: "Two Pair", 4: "Three of a Kind", 5: "Straight", 6: "Flush", 7: "Full House", 8: "Four of a Kind", 9: "Straight Flush", 10: "Royal Flush", 11: "Five of a Kind"}

command_list = [
  Command('$poker help', 'Lists out all the valid poker commands.'), 

  Command('$poker play <amount>', 'Play the poker game by gambling x amount.'),
                      
  Command('$poker replace <pos1> <pos2> ...', "Replace the cards at specified positions. Can only replace once per game. Positions must be unique and from 1-5."),
  
  Command('$poker reveal', 'Continue game with current hand and proceed with outcome calculation.')]

def generate_help(cmds):
  help_list = []
  for cmd in cmds:
    c = cmd.c
    d = cmd.d

    line = "**{}**: {}".format(c, d)
    help_list.append(line)

  full_help = '\n'.join(help_list)
  return full_help

help_list = generate_help(command_list)

##########################################################

async def help(channel, user):
  return await channel.send("POKER COMMANDS: \n{}".format(help_list))

async def manage(msg, channel, user):
  msg_split = msg.split(' ')
  cmd_name = msg_split[0]
  
  if len(msg_split) == 1:
    return await channel.send("{} The available commands for '{}' can be found in '{} help'".format(user.mention, cmd_name, cmd_name))

  action = msg_split[1]
  #actions: play, reveal, replace

  if action not in command_dict.keys():
    return await channel.send("{} The available commands for '{}' can be found in '{} help'".format(user.mention, cmd_name, cmd_name))

  if action == "play" or action == "p":
    try:
      amt = int(msg_split[2])

    except:
      return await channel.send("{} Invalid amount specified for '{} play'. The amount specified should be a *number* greater than 0.".format(user.mention, cmd_name))

    return await command_dict[action](channel, user, amt)
  
  elif action == "reveal":
    return await resolve(channel, user)

  elif action == "help":
    return await help(channel, user)

  else: #must be replace
    card_pos_list = msg.split(' ')[2:]
    return await replace_cards(channel, user, card_pos_list)

async def start_game(channel, user, amt):
  user_str = str(user)

  #STEPS:
  #0. Check if player already has an active game
  #1. Check if the player has the valid amount of money
  #2. Remove the amount of money they're gambling and save data
  #3. Deal 5 cards to player using random.choice()
  #4. Deal 5 cards to the dealer using random.choice()
  #5. Store these cards in the poker_data dict as a tuple
  #6. Show the cards to the player as an image usnig combine_images()

  #ERROR CODES:
  # -1 = insufficient funds
  # -2 = negative amount
  # -3 = active game
  if poker_data[user_str] == False:

    if game_user.suff_money(user_str, amt):
      if amt > 0:
        game_user.user_dict[user_str] -= amt
        game_user.save(game_user.user_dict, 'user_data.json')

        users_cards = cards.deal(5)
        dealers_cards = cards.deal(5)

        poker_data[user_str] = (users_cards, dealers_cards, amt, False)

        user_img = cards.image(users_cards)

        await channel.send(content="{} Your cards:\n".format(user.mention), file=user_img)
        #await channel.send(file=user_img)

        return
      
      else:
        return await channel.send("{} Please enter a valid amount to gamble.".format(user.mention))
    
    else:
      return await channel.send("{} You have insufficient funds, please change the amount you would like to gamble or rethink your life choices.".format(user.mention))

  else:
    return await channel.send("{} You already have another active game, please finish the current one before starting a new one.".format(user.mention))

async def replace_cards(channel, user, pos_list):
  user_str = str(user)
  #STEPS:
  #1. Grab the user's cards info
  #1b. Check if the user has replaced his cards before
  #2. Convert pos_list to valid_pos
  #3. Convert positions to indexes
  #4. Replace cards at given index

  #ERROR CODES:
  # -1: No active poker games
  # -2: Replaced cards before

  poker_info = poker_data[user_str]

  if poker_info == False:
    return await channel.send("{} You do not have an active poker game yet. Please use '$poker play <amount>' to start a new game!".format(user.mention))

  else:
    users_cards = poker_info[0]
    dealers_cards = poker_info[1]
    amt = poker_info[2]

    if not poker_data[user_str][3]:
      valid_pos = valid_pos_list(pos_list, 1, 5)
      new_cards = cards.deal(len(valid_pos))

      for pos in valid_pos:
        new_card = new_cards.pop(0)
        actual_pos = pos - 1

        users_cards.pop(actual_pos)
        users_cards.insert(actual_pos, new_card)

      #Place the new cards into the poker data and save it
      poker_data[user_str] = (users_cards, dealers_cards, amt, True)
      user_img = cards.image(users_cards)
      dealer_img = cards.image(dealers_cards)

      await channel.send(content="{} Your new cards:".format(user.mention), file=user_img)

      await channel.send(content="Dealer's hand:", file=dealer_img)

      return await resolve(channel, user)

    else:
      return await channel.send("{} You have already replaced your cards before and can't do it again. Use '$poker reveal' to finish your current game.".format(user.mention))

async def resolve(channel, user):
  user_str = str(user)
  # Steps:
  # 1. Look at the player's hand and determine the ranking of it
  # 2. Do the same with the dealer's hand
  # 3. Compare the two hands to see which one is better
  # 4. ...

  player_info = poker_data[user_str]

  if player_info != False:
    player_cards = player_info[0]
    dealer_cards = player_info[1]
    bet_amount = player_info[2]
    
    player_result = check_hand(player_cards)
    dealer_result = check_hand(dealer_cards)

    player_prim_res = player_result[0]
    dealer_prim_res = dealer_result[0]

    player_sec_res = player_result[1]
    dealer_sec_res = dealer_result[1]


    player_strength = poker_outcomes[player_prim_res]
    dealer_strength = poker_outcomes[dealer_prim_res]

    # If the user hasn't replaced yet, we can show the dealer's cards
    if poker_data[user_str][3] == False:
      dealer_img = cards.image(dealer_cards)

      await channel.send(content="Dealer's hand:", file=dealer_img)

    global win_multiplier

    if player_prim_res > dealer_prim_res:
      new_money = game_user.user_dict[user_str] + int(win_multiplier * bet_amount)

      await channel.send("{} Your **{}** defeated the dealer's **{}**! You now have **${}** to gamble with! Keep gambling!".format(user.mention, player_strength, dealer_strength, new_money))

    elif player_prim_res == dealer_prim_res:

      if player_sec_res > dealer_sec_res:
        new_money = game_user.user_dict[user_str] + int(bet_amount * win_multiplier)

        await channel.send("{} Your **{}** defeated the dealer's **{}**! You now have **${}** to gamble with! Keep gambling!".format(user.mention, player_strength, dealer_strength, new_money))

      elif player_sec_res == dealer_sec_res:
        outcome = 1
        new_money = game_user.user_dict[user_str] + (bet_amount * outcome)

        await channel.send("{} Not bad! You and the dealer tied with a **{}**! You now have **${}** to gamble with! Keep gambling champ!".format(user.mention, player_strength, new_money))
      
      else:
        outcome = 0
        new_money = game_user.user_dict[user_str] + (bet_amount * outcome)

        await channel.send("{} Super unlucky! Your hand of **{}** was unable to defeat the dealer's **{}** in the tiebreaker! You now have **${}** to gamble with! Don't let your dreams fade away, go again!".format(user.mention, player_strength, dealer_strength, new_money))

    else:
      outcome = 0
      new_money = game_user.user_dict[user_str] + int(bet_amount * outcome)

      await channel.send("{} Unfortunately your hand of **{}** was unable to defeat the dealer's **{}**! You now have **${}** to gamble with! Don't let your dreams fade away, go again!".format(user.mention, player_strength, dealer_strength, new_money))

    #End the game by making the user no longer being in active game
    poker_data[user_str] = False

    #Update the player's money
    game_user.user_dict[user_str] = new_money
    game_user.save(game_user.user_dict, 'user_data.json')

    return
  
  else:
    return await channel.send("{} You do not have an active poker game yet. Please use '$poker play <amount>' to start a new game!".format(user.mention))

## Helper Functions ##

def valid_pos_list(pos_list, min, max):
  #Converts a pos_list to a valid one without duplicates or out of range positions

  new_list = []
  a = pos_list

  while len(a) > 0: 
    pos = int(a.pop(0))

    #Check if valid int
    if isinstance(pos, int):
      #Check if duplicate
      if pos not in pos_list:
        #Check if within range
        if (pos >= min) and (pos <= max):
          new_list.append(pos)

  return new_list

def check_mountain(values):
  return values == [1, 10, 11, 12, 13]

def check_consecutive(values):
  prev = values[0] - 1

  for value in values:
    if value != (prev + 1):
      return False

    prev = value

  return True

def check_five_kind(vdict):
  return len(vdict) == 1

def check_four_kind(vdict):
  if (4 in vdict.values()):
    for i, j in vdict.items():
      if j == 4:
        if i == 1:
          return (True, 14)

        else:
          return (True, i)
  
  else:
    return (False, -1)

def check_full_house(vdict):
  three_and_two = (3 in vdict.values()) and (2 in vdict.values())

  if three_and_two:
    for i, j in vdict.items():
      if j == 3:
        if (i == 1):
          return (True, 14)
        
        else:
          return (True, i)

  else:
    return (False, -1)

def check_three_kind(vdict):
  for i, j in vdict.items():
    if j == 3:

      if (i == 1):
        return (True, 14)

      else:
        return (True, i)
  
  return (False, -1)

def check_two_pairs(vdict):
  pairs = 0
  big_card = 0

  for i, j in vdict.items():
    if j == 2:
      pairs += 1
      
      if (i > big_card) or (i == 1):
        big_card = i

  if big_card == 1:
    return (pairs == 2, 14)
  
  else:
    return (pairs == 2, big_card)

def check_pair(values, vdict):
  for val in values:
    if vdict[val] == 2:
      if val == 1:
        return (True, 14)
      
      else:
        return (True, val)

  return (False, -1)

def highest_value(values):
  
  if 1 in values:
    return 14
  
  else:
    return values[-1]

def check_hand(cards):
  vcount = defaultdict(int)
  scount = defaultdict(int)
  values = []
  suits = []

  for x in cards:
    v = x.value
    s = x.suit

    vcount[v] += 1
    scount[s] += 1
    values.append(v)
    suits.append(s)

  values.sort()
  suits.sort() 

  flush = len(scount) == 1
  hsuit = suits[0]
  
  #Five of a Kind: vcount only 1?
  if check_five_kind(vcount):
    return (11, values[-1]) #score + value

  #Royal Flush: mountain and flush?
  rf = check_mountain(values) and flush
  if rf:
    return (10, hsuit) #score + suit of rf

  #Straight Flush: straight and flush?
  if check_consecutive(values) and flush:
    return (9, hsuit)
  #Four of a Kind

  fkind = check_four_kind(vcount)
  if fkind[0]:
    return (8, fkind[1])

  #Full House
  fhouse = check_full_house(vcount)
  if fhouse[0]: 
    return (7, fhouse[1])

  #Flush
  elif flush:
    return (6, hsuit)

  #Straight
  elif check_mountain(values):
    return (5, 14)

  elif check_consecutive(values):
    return (5, values[-1])

  #Three of a Kind
  tkind = check_three_kind(vcount)
  if tkind[0]:
    return (4, tkind[1])

  #Two Pairs
  tpair = check_two_pairs(vcount)
  if tpair[0]:
    return (3, tpair[1])

  #One Pair
  opair = check_pair(values, vcount)
  if opair[0]:
    return (2, opair[1])

  #High Card
  else:
    hvalue = highest_value(values)
    return (1, hvalue)

##########################################################
command_dict = {'help': help, 'p': start_game, 'play': start_game, 'r': replace_cards, 'replace': replace_cards, 'reveal': resolve}