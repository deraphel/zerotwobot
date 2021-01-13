####################################
import discord
import random
import uuid

import io
import cv2
####################################
class Card:
  def __init__(self, value, suit, img):
    self.value = value #int[0-13], J=11, Q=12, K=13
    self.suit = suit #int[0-3], 0=dia, 1=club, 2=heart, 3=spades
    self.img = img #str, img file name

####################################

def generate():
  card_names = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
  card_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
  suit_abbrevs = ['D', 'C', 'H', 'S']
  suit_vals = [0, 1, 2, 3]

  card_list = []

  for i1, value in enumerate(card_values):

    for i2, suit in enumerate(suit_abbrevs):
      img = cv2.imread("poker/{}{}.png".format(card_names[i1], suit), cv2.IMREAD_REDUCED_COLOR_4)
      new_card = Card(value, suit_vals[i2], img)

      card_list.append(new_card)

  return card_list      

def combine_image(im_list):
    file_name = str(uuid.uuid4()) + ".jpg"

    h_min = min(im.shape[0] for im in im_list)
    im_list_resize = [cv2.resize(im, (int(im.shape[1] * h_min / im.shape[0]), h_min), interpolation=cv2.INTER_CUBIC)
                      for im in im_list]

    im = cv2.hconcat(im_list_resize)

    #Convert ndarray to img using CV2
    is_success, buffer = cv2.imencode(".JPEG", im, [3, 1])

    arr = io.BytesIO(buffer)
    file = discord.File(fp=arr, filename=file_name)

    return file

def deal(num):
  return random.choices(all_cards, k=num)

# Creates an image of all the cards side-by-side as a JPG file
def image(users_cards):
  imgs = [x.img for x in users_cards]
  return combine_image(imgs)


#########################################################
# Global Variables
#########################################################

all_cards = generate()