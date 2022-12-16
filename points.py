import re
from PIL import Image, ImageFilter
import random
import math
import datetime
import os, os.path
from collections import Counter
import requests

SEED = 0
myRandom = random.Random(SEED)

DOWNSAMPLE_AMT = 10
BLUR_AMT = 4

PALETTE_NUM = 10

words = []
punct = []

SENT_END_PUNCT = ".!?"
CLAUSE_END_PUNCT = SENT_END_PUNCT + ",:"
PUNCT = CLAUSE_END_PUNCT + "—"
PUNCT_PCT = 0.1 # how much punctuation to add between words
to_capitalise = ["i", "i'm", "george", "georges", "georgie", "seurat", "sunday", "sundays", "god",
  "jules", "harriet", "billy", "webster", "charles", "redmond", "texas", "lee", "randolph", "blair", "henry", "marie"]

# MAX_VAL = 255 * 255 * 255
MAX_VAL = 255 * 3
# NUM_PAGES = 5
NUM_PAGES = 1
ASPECT = 0.65 # multiply by width to get height (in landscape orientation)

EXPORT_FORMAT = "%Y%m%d%H%M%S"

now = datetime.datetime.now()
run = now.strftime(EXPORT_FORMAT)
print("Output at", os.path.dirname(f"output/{run}/"))
os.makedirs(os.path.dirname(f"output/{run}/"), exist_ok=True)

def pickPunct(end_of_sent=False):
  if end_of_sent:
    # return SENT_END_PUNCT[math.floor(random.random() * len(SENT_END_PUNCT))]
    return random.choice(SENT_END_PUNCT)
  # return PUNCT[math.floor(random.random() * len(PUNCT))]
  return random.choice(PUNCT)

def tuple_to_word(tup, words):
  pixel = sum(tup)
  # map to an index of the word list
  index = round(pixel / MAX_VAL * len(words))
  word = words[index]
  return word

def generate_palette(img, output_dir):
  pixels = list(img.getdata())
  palette = []
  colors_by_freq = [item for items, c in Counter(pixels).most_common() for item in [items] * c]
  MIN_SAT = 50
  MIN_DIFF = 20
  # go through top colors
  for color in colors_by_freq:
    # check if we have enough colors already
    if len(palette) >= PALETTE_NUM:
      break
    # check if color is already in top colors
    if color in palette:
      continue
    # check if color is far enough away from grey
    if abs(color[0] - color[1]) < MIN_SAT and abs(color[1] - color[0]) < MIN_SAT and abs(color[2] - color[0]) < MIN_SAT:
      continue
    # check if color is different enough from other colors
    if len(palette) > 0:
      diff_enough = True
      for other_color in palette:
        if abs(other_color[0] - color[0]) < MIN_DIFF and abs(other_color[1] - color[1]) < MIN_DIFF and abs(other_color[2] - color[2]) < MIN_DIFF:
          diff_enough = False
      if not diff_enough:
        continue
    # good enough! add it
    palette.append(color)
    # generate image of solid color
    color_img = Image.new("RGB", (100, 100), color=color)
    if not os.path.exists(f"{output_dir}/colors"):
      os.mkdir(f"{output_dir}/colors")
    with open(f"{output_dir}/colors/{str(color)}.png", "wb") as f:
      color_img.save(f)
  return palette

with open("input/sunday.txt") as f:
  lyrics = " ".join(f.read().splitlines())
  trim = re.sub(r"[\[\]()\"/&]|#[0-9]", " ", lyrics) # square brackets, parentheses, double quotes, hyphens and dashes, slashes, ampersands, #1s etc
  trim = re.sub(r" [b-hj-z] |[\-—–]", " ", trim) # single letters that aren't A or I
  ellipsis = re.sub(r"\.\.\.", "…", trim) # replace three dots with ellipsis character

  tokens = re.sub(r"[,.:!?…]", "", ellipsis)
  tokens = re.split(" ", tokens)
  tokens = [x for x in tokens if x]
  nonames = [x for x in tokens if not re.match(r"\b[A-Z]{2,}\b", x)]
  lowercase = [x.lower() for x in nonames]
  nodupes = []
  [nodupes.append(x) for x in lowercase if x not in nodupes]
  # words = list(set(lowercase))
  # words = [x for x in words if x not in PUNCT]
  words = [x for x in nodupes if x not in PUNCT]
  # myRandom.shuffle(words)
  # print(words)

  # img = Image.open("input/seurat-4096.jpg")
  img = Image.open("input/tile-1.jpg")
  for page in range(NUM_PAGES):
    # x = 200
    # y = 150
    # w = 100
    # h = round(w * ASPECT)
    x = 0
    y = 0
    w = 512
    h = 512
    page_id = f"{x}-{y}-{w}-{h}"
    box = (x, y, x + w, y + h)
    crop = img.crop(box)
    # blur = crop.filter(ImageFilter.GaussianBlur(BLUR_AMT))
    # pixels = list(blur.getdata())
    downsampled = img.resize((round(w / DOWNSAMPLE_AMT), round(h / DOWNSAMPLE_AMT)))
    pixels = list(downsampled.getdata())

    text = ""
    for i in range(len(pixels)):
      start_of_para = i == 0 or re.match("\n", text[-1])
      start_of_sent = i == 0 or start_of_para or re.match(r"[.!?]", text[-1])
      after_punct = i > 0 and re.match(r"[,.:!?…\-—–]", text[-1])

      # pick either punctuation or word
      token = ""
      is_punct = False
      if not start_of_para and not start_of_sent and not after_punct and random.random() < PUNCT_PCT:
        is_punct = True
        token = pickPunct()
      else:
        # get value from pixel
        token = tuple_to_word(pixels[i], words)
        if start_of_sent or token in to_capitalise: # capitalise word, if at start of sentence
          token = token[0].upper() + token[1:]

      # skip if repeating word
      if not is_punct and text[-len(token):].lower() == token.lower():
        continue

      # add space before, if word
      if not start_of_para and not re.match(re.compile(f"[{CLAUSE_END_PUNCT}]"), token):
        text += " "
      text += token

      # add newlines, if at end of row
      if i > 0 and i % w == 0:
        # text += "\n\n"
        if not is_punct:
          text += pickPunct(end_of_sent=True)
        text += "\n"

    palette = generate_palette(crop, f"output/{run}")

    log = "date=" + now.strftime("%Y-%m-%d %H:%m:%S")
    log += "\n"
    log += "\n" + "seed=" + str(SEED)
    log += "\n" + "blur=" + str(BLUR_AMT)
    log += "\n"
    log += "\n" + "left=" + str(x)
    log += "\n" + "top=" + str(y)
    log += "\n" + "right=" + str(x + w)
    log += "\n" + "bottom=" + str(y + h)
    log += "\n"
    log += "\n" + "words=" + str(len(re.split(r"\s+", text)))
    log += "\n"
    for color in palette:
      log += "\n" + f"{str(color)} -> {tuple_to_word(color, words)}"

    with open(f"output/{run}/sondrat.txt", "w") as f:
      f.write(text)
    with open(f"output/{run}/seurat.jpg", "w") as f:
      crop.save(f)
    with open(f"output/{run}/seurat-downsampled.jpg", "w") as f:
      downsampled.save(f)
    with open(f"output/{run}/log.txt", "w") as f:
      f.write(log)