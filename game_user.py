# Manages the users money

import json

user_dict = {}

# Initialize by loading the users' data
with open('user_data.json') as file:
  user_dict = json.load(file)

################################
def suff_money(user, amt):
  if str(user) in user_dict.keys():
    return user_dict[str(user)] >= amt
  
  else:
    user_dict[str(user)] = 0
    return user_dict[str(user)]

def save(data, file_name):
  with open(file_name, 'w') as outfile:
    json.dump(data, outfile)

async def fetch_money(channel, user):
  user_str = str(user)

  if user_str in user_dict.keys():
    return await channel.send("{} You currently have **${}**.".format(user.mention, user_dict[user_str]))

  else:
    user_dict[user_str] = 0
    save(user_dict, 'user_data.json')
    return await channel.send("{} You currently have **${}**.".format(user.mention, user_dict[user_str]))

async def give_money(channel, user, recipient, amt):
  user_str = str(user)
  #Check:
  #recipient = user?
  #recipient exists?
  #amount > 0
  #suff_amount?

  if str(user) == recipient:
    return await channel.send("{} You can't send money to yourself baka!".format(user.mention))
  
  else:
    if recipient in user_dict.keys():
      if amt > 0:

        if suff_money(user_str, amt):
          user_dict[user_str] -= amt
          user_dict[recipient] += amt
          save(user_dict, 'user_data.json')

          return await channel.send("{} You have successfully transfered **${}** to **{}**. You now have **${}** remaining in your wallet. You're such a nice guy :)".format(user.mention, str(amt), recipient, user_dict[user_str]))

        else: 
          return await channel.send("{} Imagine trying to give others money when you don't have enough yourself haha.".format(user.mention))
        
      else:
        return await channel.send("{} Please enter a valid amount to give.".format(user.mention))

    else:
      return await channel.send("{} The user **{}** couldn't be found. Please ensure that you copy their **full username** including the discord tag (e.g. North#7279).".format(user.mention, recipient))