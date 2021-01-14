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

def vconcat_resize_min(im_list, interpolation=cv2.INTER_CUBIC):

    w_min = min(im.shape[1] for im in im_list)
    im_list_resize = [cv2.resize(im, (w_min, int(im.shape[0] * w_min / im.shape[1])), interpolation=interpolation)
                      for im in im_list]
    
    return cv2.vconcat(im_list_resize)

def hconcat_resize_min(im_list):

    h_min = min(im.shape[0] for im in im_list)
    im_list_resize = [cv2.resize(im, (int(im.shape[1] * h_min / im.shape[0]), h_min), interpolation=cv2.INTER_CUBIC)
                      for im in im_list]

    return cv2.hconcat(im_list_resize)

def img_to_bytes(img):
  file_name = "cards.jpg"

  #Convert ndarray to JPGimg using CV2
  is_success, buffer = cv2.imencode(".JPEG", img, [3, 1])

  arr = io.BytesIO(buffer)
  file = discord.File(fp=arr, filename=file_name)

  return file

def deal(num):
  return random.choices(all_cards, k=num)

# Creates an image of all the cards side-by-side as a JPG file
def image(users_cards):
  imgs = [x.img for x in users_cards]
  return img_to_bytes(hconcat_resize_min(imgs))

def user_dealer_image(ucards, dcards):
  u_cards = [x.img for x in ucards]
  d_cards = [x.img for x in dcards]

  ucards_aligned = hconcat_resize_min(u_cards)
  dcards_aligned = hconcat_resize_min(d_cards)

  return img_to_bytes(vconcat_resize_min([ucards_aligned, dcards_aligned]))

#########################################################
# Global Variables
#########################################################

all_cards = generate()