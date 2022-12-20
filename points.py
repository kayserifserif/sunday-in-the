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

EXPORT_FORMAT = "%Y%m%d%H%M%S"

now = datetime.datetime.now()
run = now.strftime(EXPORT_FORMAT)
print("Output at", os.path.dirname(f"output/{run}/"))
os.makedirs(os.path.dirname(f"output/{run}/"), exist_ok=True)

def pickPunct(end_of_sent: bool = False):
  if end_of_sent:
    # return SENT_END_PUNCT[math.floor(random.random() * len(SENT_END_PUNCT))]
    return random.choice(SENT_END_PUNCT)
  # return PUNCT[math.floor(random.random() * len(PUNCT))]
  return random.choice(PUNCT)

def tuple_to_word(tup: tuple, words: list) -> str:
  pixel = sum(tup)
  # map to an index of the word list
  index = round(pixel / MAX_VAL * len(words))
  word = words[index]
  return word

def get_words(in_file: str) -> list:
  with open(in_file) as f:
    lyrics = " ".join(f.read().splitlines())

    # clean up lyrics and get a list of all unique words
    words = re.sub(r"[\[\]()\"/&]|#[0-9]", " ", lyrics) # square brackets, parentheses, double quotes, hyphens and dashes, slashes, ampersands, #1s etc
    words = re.sub(r" [b-hj-z] |[\-—–]", " ", words) # single letters that aren't A or I
    words = re.sub(r"\.\.\.", "…", words) # replace three dots with ellipsis character
    words = re.sub(r"[,.:!?…]", "", words) # remove punctuation
    words = [x for x in re.split(" ", words) if x] # remove empty tokens
    words = [x for x in words if not re.match(r"\b[A-Z]{2,}\b", x)] # remove character headings
    words = [x.lower() for x in words] # make everything lowercase
    nodupes = [] # remove duplicates
    [nodupes.append(x) for x in words if x not in nodupes]
    words = [x for x in nodupes if x not in PUNCT]
    
    return words

def generate_text(words: list, pixels: list, box: tuple) -> str:
  # calculate dimensions
  (left, top, right, bottom) = box
  w = right - left

  # start putting together the text
  text = ""
  for i in range(len(pixels)):
    # check if start of paragraph: if it's the first pixel, or if the last character was a line break
    start_of_para = i == 0 or re.match("\n", text[-1])
    # check if start of sentence: if it's the first pixel, or if the last character was a sentence-ending punctuation mark
    start_of_sent = i == 0 or start_of_para or re.match(re.compile(f"[{SENT_END_PUNCT}]"), text[-1])
    # check if after punctuation: if it's after the first pixels and the last character was a punctuation mark
    after_punct = i > 0 and re.match(re.compile(f"[{PUNCT}]"), text[-1])

    # pick either punctuation or word
    token = ""
    is_punct = False
    if not start_of_para and not start_of_sent and not after_punct and random.random() < PUNCT_PCT:
      is_punct = True
      token = pickPunct()
    else:
      # get a word from pixel value
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
      if not is_punct:
        text += pickPunct(end_of_sent=True) # add sentence-ending punctuation, if word
      text += "\n"
  
  return text

def get_colors(img: Image) -> list:
  pixels = list(img.getdata())
  colors_by_freq = [item for items, c in Counter(pixels).most_common() for item in [items] * c]
  return colors_by_freq

def generate_palette(colors: list, output_dir: str) -> list:
  MIN_SAT = 50
  MIN_DIFF = 20
  palette = []
  # go through top colors
  for color in colors:
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

def main():
  words = get_words("input/sunday.txt")

  # read the image
  # img = Image.open("input/seurat-4096.jpg")
  img = Image.open("input/tile-1.jpg")
  # make a box to crop the image to
  x = 0
  y = 0
  w = 512
  h = 512
  box = (x, y, x + w, y + h)
  crop = img.crop(box)

  # downsample the cropped image to get a more manageable list of pixels
  down_w = round(w / DOWNSAMPLE_AMT)
  down_h = round(h / DOWNSAMPLE_AMT)
  downsampled = img.resize((down_w, down_h))
  pixels = list(downsampled.getdata())

  # start putting together the text
  text = generate_text(words, pixels, box)

  # generate palette (top unique-enough colors) from image
  colors = get_colors(crop)
  palette = generate_palette(colors, f"output/{run}")

  # log some info
  log_info = {
    "run": {
      "datetime": now.strftime("%Y-%m-%d %H:%m:%S"),
      "seed": str(SEED)
    },
    "image": {
      "coords": str((x, y, x + w, y + h)),
      "downsize": str((down_w, down_h)),
      "pixels": str(down_w * down_h)
    },
    "text": {
      "wordlist": str(len(words)),
      "length": str(len(re.split(r"\s+", text)))
    },
    "palette": {
      "colors": str(len(colors))
    }
  }
  for i in range(len(palette)):
    color_word = tuple_to_word(palette[i], words)
    log_info["palette"][color_word] = str(palette[i])
  log = ""
  for category in log_info:
    if len(log) > 0:
      log += "\n"
    log += category.upper() + "\n"
    for key in log_info[category]:
      log += key + "=" + log_info[category][key] + "\n"

  # write files
  with open(f"output/{run}/sondrat.txt", "w") as f:
    f.write(text)
  with open(f"output/{run}/seurat.jpg", "w") as f:
    crop.save(f)
  with open(f"output/{run}/seurat-downsampled.jpg", "w") as f:
    downsampled.save(f)
  with open(f"output/{run}/log.txt", "w") as f:
    f.write(log)

if __name__ == "__main__":
  main()