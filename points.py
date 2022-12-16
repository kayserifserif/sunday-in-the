import re
from PIL import Image, ImageFilter
import random
import math
import datetime
import os, os.path

SEED = 0
myRandom = random.Random(SEED)

words = []
punct = []

SENT_END_PUNCT = ".!?"
CLAUSE_END_PUNCT = SENT_END_PUNCT + ",:"
PUNCT = CLAUSE_END_PUNCT + "—"
PUNCT_PCT = 0.1 # how much punctuation to add between words
to_capitalise = ["i", "i'm", "george", "georges", "georgie", "seurat", "sunday", "sundays", "god",
  "jules", "harriet", "billy", "webster", "charles", "redmond", "texas", "lee", "randolph", "blair", "henry", "marie"]

MAX_VAL = 255 * 255 * 255
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
    x = 200
    y = 150
    w = 100
    h = round(w * ASPECT)
    page_id = f"{x}-{y}-{w}-{h}"
    box = (x, y, x + w, y + h)
    crop = img.crop(box)
    blur = crop.filter(ImageFilter.GaussianBlur(4))
    # pixels = list(crop.getdata())
    pixels = list(blur.getdata())
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
        tup = pixels[i]
        product = 1
        for num in tup:
          product *= num
        # map that to an index of the word list
        index = round(product / MAX_VAL * len(words))
        token = words[index]
        if start_of_sent or token == "i" or token == "i'm": # capitalise word, if at start of sentence
          token = token[0].upper() + token[1:]

      # skip if repeating word
      if not is_punct and text[-len(token):].lower() == token:
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

    metadata = "date=" + now.strftime("%Y-%m-%d %H:%m:%S")
    metadata += "\n" + "seed=" + str(SEED)
    metadata += "\n" + "left=" + str(x)
    metadata += "\n" + "top=" + str(y)
    metadata += "\n" + "right=" + str(x + w)
    metadata += "\n" + "bottom=" + str(y + h)

    with open(f"output/{run}/{page_id}.txt", "w") as f:
      f.write(text)
    with open(f"output/{run}/{page_id}.jpg", "w") as f:
      crop.save(f)
    with open(f"output/{run}/metadata.txt", "w") as f:
      f.write(metadata)