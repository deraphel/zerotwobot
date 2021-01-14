####################################
import discord
from collections import defaultdict
import game_user
import cards
import random
####################################
class Command:
  def __init__(self, cmd, definition):
    self.c = cmd
    self.d = definition

blackjack_data = defaultdict(bool)

command_list = [
  Command("$bj play <amount>", "Bets x amount of money to start a classic blackjack game."),
  Command("$bj hit", "Draws an additional card during an active blackjack game."),
  Command("$bj stay", "Stop drawing additional cards and move to the resolve phase."),
  Command("$bj double", "Double down on your current bet by betting x amount again and only draw one more card before moving to resolve phase.")]

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

bust_gifs = ['https://tenor.com/0Blz.gif', 'https://tenor.com/vNkh.gif']

natural_payout_multiplier = 3
normal_payout_multiplier = 2
#######################################
async def manage(msg, channel, user):
  msg_split = msg.split(' ')
  cmd_name = msg_split[0]
  
  if len(msg_split) == 1:
    if (cmd_name == "$bj"):
      return await channel.send("{} You pathetic, disgusting pervert, I'm not doing that! Just kidding teehee. The available commands for '{}' can be found in '{} help'".format(user.mention, cmd_name, cmd_name))

    else:
      return await channel.send("{} The available commands for '{}' can be found in '{} help'".format(user.mention, cmd_name, cmd_name))

  action = msg_split[1]
  #actions: play, hit, stay, double

  if action not in command_dict.keys():
    return await channel.send("{} The available commands for '{}' can be found in '{} help'".format(user.mention, cmd_name, cmd_name))

  if action == "play" or action == "p":
    try:
      amt = int(msg_split[2])

    except:
      return await channel.send("{} Invalid amount specified for '{} play'. The amount specified should be a *number* greater than 0.".format(user.mention, cmd_name))

    return await command_dict[action](channel, user, amt)
  
  else:
    return await command_dict[action](channel, user)

async def help(channel, user):
  return await channel.send("{} BLACKJACK COMMANDS: \n{}".format(user.mention, help_list))

async def hit(channel, user):
  user_str = str(user)
  user_info = blackjack_data[user_str]

  if user_info == False:
    return await channel.send("{} You do not have an active blackjack game yet. Please use '$bj play <amount>' to start a new game!".format(user.mention))
  
  else:
    cur_deck = user_info[0]
    dealer = user_info[1]
    amt = user_info[2]

    new_card = cards.deal(1)
    new_deck = cur_deck + new_card
    card_values = bj_convert_to_values(new_deck)

    result = bj_check_user_value(card_values)
    player_total = result[0]

    dealer_result = bj_check_user_value(bj_convert_to_values(dealer))
    dealer_total = dealer_result[0]
    
    combined_img = cards.user_dealer_image(new_deck, dealer)

    await embed(combined_img, player_total, dealer_total, channel, user)

    if result[1] == 0: # user busts
      blackjack_data[user_str] = False

      await channel.send("{} Yikes! You busted with **{}**. Better luck next time! You now have **${}** left to gamble again!".format(user.mention, result[0], game_user.user_dict[user_str]))
      await channel.send(random.choice(bust_gifs))

      return

    elif result[1] == 1: # user doesn't bust
      blackjack_data[user_str] = (new_deck, dealer, amt, True)
      
      await channel.send("{} You can choose to hit with '$bj hit' or stay with '$bj stay'.".format(user.mention))

      return

    else: # user gets blackjack and auto-resolve
      blackjack_data[user_str] = (new_deck, dealer, amt, True)
      
      return await resolve(channel, user)

async def double(channel, user):
  user_str = str(user)
  user_info = blackjack_data[user_str]

  if user_info == False:
    return await channel.send("{} You do not have an active blackjack game yet. Please use '$bj play <amount>' to start a new game!".format(user.mention))
  
  else:
    if user_info[3]:
      return await channel.send("{} You have already hit once, so you are unable to double down. Please either use '$bj hit' or '$bj stay' to continue your game.".format(user.mention))
    
    else:
      if game_user.suff_money(user_str, user_info[2]):
        game_user.user_dict[user_str] -= user_info[2]
        game_user.save(game_user.user_dict, 'user_data.json')

        new_deck = user_info[0] + cards.deal(1)

        blackjack_data[user_str] = (new_deck, user_info[1], user_info[2] * 2)

        return await resolve(channel, user)

      else:
        return await channel.send("{} You do not have enough money to double down, sorry!".format(user.mention))

  return await channel.send("{} Not working right now, so don't use me for now :)".format(user.mention))

async def play(channel, user, amt):
    '''
    1. Check if user has an active game already
    2. Check if the user has sufficient money
    3. Take user's MONEY
    4. Deal the player's cards
    5. Check if user has blackjack already. If so, skip player and go to dealer
    6. If no bj, ask the player if they want to hit/stand/double down

    7a. If the user chooses to hit, give them one card and check if bust
    '''
    user_str = str(user)

    if blackjack_data[user_str] == False:
        if amt > 0:
            if game_user.suff_money(user_str, amt):

                game_user.user_dict[user_str] -= amt
                game_user.save(game_user.user_dict, 'user_data.json')

                player_cards = cards.deal(2)
                dealer_cards = cards.deal(2)

                combined_img = cards.user_dealer_image(player_cards, dealer_cards)

                player_total = bj_check_user_value(bj_convert_to_values(player_cards))[0]

                dealer_total = bj_check_user_value(bj_convert_to_values(dealer_cards))[0]
                
                blackjack_data[user_str] = (player_cards, dealer_cards, amt, False)

                await embed(combined_img, player_total, dealer_total, channel, user)

                if check_blackjack(player_cards):
                  if check_blackjack(dealer_cards):
                    # User ties with the dealer. Give him back his money with a little extra compensation.
                    # Restart dictionary entry for user to False
                    game_user.user_dict[user_str] += round(amt * 1.5)
                    game_user.save(game_user.user_dict, 'user_data.json')
                    blackjack_data[user_str] = False

                    await channel.send("{} So close! You tied with the dealer with a blackjack. We'll give you a little bit of compensation for disappointing you. You now have **${}** to gamble away!".format(user.mention, game_user.user_dict[user_str]))

                    return
                  
                  else:
                    # User wins with a natural at beginning. Give him big payout
                    # Restart the dictionary entry for user to False
                    game_user.user_dict[user_str] += (amt * natural_payout_multiplier)
                    game_user.save(game_user.user_dict, 'user_data.json')
                    blackjack_data[user_str] = False

                    await channel.send("{} Damn you're a god! You won immediately with a blackjack and received 2x payout! You now have **${}** to gamble away! Don't let your luck fade away, go again! https://tenor.com/view/my-hero-acadmia-anime-power-gif-15405892".format(user.mention, game_user.user_dict[user_str]))

                else:
                  await channel.send("{} You can choose to hit with '$bj hit', stay with '$bj stay', or double down with '$bj double'.".format(user.mention))

            else:
                return await channel.send("{} You have insufficient funds, please change the amount you would like to gamble or rethink your life choices.".format(user.mention))

        else:
            return await channel.send("{} Please enter a valid amount to gamble.".format(user.mention))

    else:
        return await channel.send("{} You already have another active game, please finish the current one before starting a new one.".format(user.mention))

async def resolve(channel, user):
    user_str = str(user)
    # Load the user and dealer's cards
    # Start updating the dealer's cards
    # Stop updating dealer once bust or goes >= 17
    data = blackjack_data[user_str]

    if data == False:
      # No active game
      return await channel.send("{} You do not have an active blackjack game yet. Please use '$bj play <amount>' to start a new game!".format(user.mention))

    else:
      player_cards = data[0]
      dealer_cards = data[1]

      player_check = bj_check_user_value(bj_convert_to_values(player_cards))
      player_total = player_check[0]
      player_outcome = player_check[1]

      dealer_check = bj_check_user_value(bj_convert_to_values(dealer_cards))
      dealer_total = dealer_check[0]
      dealer_outcome = dealer_check[1]

      combined_img = cards.user_dealer_image(player_cards, dealer_cards)

      if player_outcome == 0:

        blackjack_data[user_str] = False

        await embed(combined_img, player_total, dealer_total, channel, user)

        await channel.send("{} Yikes! You busted with **{}**. Better luck next time! You now have **${}** left to gamble again!".format(user.mention, player_total, game_user.user_dict[user_str]))
        await channel.send(random.choice(bust_gifs))

        return

      while dealer_total < 17: # keep dealing cards until the dealer reaches >= 17
        new_dealer_cards = dealer_cards + cards.deal(1)
        dealer_check = bj_check_user_value(bj_convert_to_values(new_dealer_cards))
        dealer_total = dealer_check[0]
        dealer_outcome = dealer_check[1]

        dealer_cards = new_dealer_cards

      combined_img = cards.user_dealer_image(player_cards, dealer_cards)

      await embed(combined_img, player_total, dealer_total, channel, user)

      if player_total == dealer_total:  # a tie, give money back
          game_user.user_dict[user_str] += data[2]
          game_user.save(game_user.user_dict, 'user_data.json')

          blackjack_data[user_str] = False

          return await channel.send("{} You were so close to winning, but the dealer tied with you! Gamble again with your **${}**!".format(user.mention, game_user.user_dict[user_str]))
        
      # If dealer is bust or player has greater value then they win
      elif (dealer_outcome == 0) or (player_total > dealer_total): # player wins, gets 2x money spent
          game_user.user_dict[user_str] += (data[2] * normal_payout_multiplier)
          game_user.save(game_user.user_dict, 'user_data.json')

          blackjack_data[user_str] = False

          await channel.send("{} You've won, defeating the dealer's **{}** with your **{}**! You now have **${}** to gamble away! Don't let your good luck fade away!".format(user.mention, dealer_total, player_total, game_user.user_dict[user_str]))

          return

      else: # player loses and gets nothing
          blackjack_data[user_str] = False

          await channel.send("{} Unfortunately the dealer is just superior to you, beating your **{}** with a **{}**. Better luck next time. Gamble again with your **${}** left!".format(user.mention, player_total, dealer_total, game_user.user_dict[user_str]))

          return

async def embed(img, ustrength, dstrength, channel, user):
  # Creates an embed that combines the user's cards with the dealer's cards and makes it look fancier

  embed = discord.Embed(title="Blackjack", description="Your cards (top) and Dealer's cards (bottom)",
  color = 1146986)
  embed.set_image(url="attachment://cards.jpg")
  embed.set_author(name=user.display_name, icon_url=user.avatar_url)

  embed.set_footer(text="Your Hand: *{}* | Dealer's Hand: *{}*".format(ustrength, dstrength))

  return await channel.send(file=img, embed=embed)

## Helper Functions ##
def check_blackjack(class_deck):
  return bj_check_user_value(bj_convert_to_values(class_deck))[1] == 2

def bj_check_user_value(deck):

  sum = 0
  count = defaultdict(int)

  for card in deck:
    count[card] += 1
    
    if card > 10:
      sum += 10

    # Aces count as 11 unless bust
    elif card == 1:
      sum += 11

    # Every other card
    else:
      sum += card

  if sum > 21:
    # If there was an A in the deck and sum > 21, then we should pretend A is 1 instead to see if they still bust
    new_sum = sum

    for i in range(count[1]):
      new_sum -= 10

      if new_sum == 21:
        return (new_sum, 2)
      
      elif new_sum < 21:
        return (new_sum, 1)

    #Either aces weren't found or all the aces didn't reduce to <= 21
    return (new_sum, 0)

  else:
    if sum == 21:
      return (sum, 2)

    else:
      return (sum, 1)

def bj_convert_to_values(class_cards):
  return [x.value for x in class_cards]

##########################################################
command_dict = {'help': help, 'hit': hit, 'h': hit, 'stay': resolve, 's': resolve, 'stand': resolve, 'play': play, 'p': play, 'd': double, 'double': double}