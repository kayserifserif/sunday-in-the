import re
from PIL import Image
import random
import math

SEED = 0
myRandom = random.Random(SEED)

words = []
punct = []
PUNCT_PCT = 0.1 # how much punctuation to add between words
with open("input/sunday.txt") as f:
  lyrics = " ".join(f.read().splitlines())
  trim = re.sub(r"[\[\]()\"\-—–/&]|#[0-9]", " ", lyrics) # square brackets, parentheses, double quotes, hyphens and dashes, slashes, ampersands, #1s etc
  trim = re.sub(r" [b-hj-z] ", " ", trim) # single letters that aren't A or I
  ellipsis = re.sub(r"\.\.\.", "…", trim) # replace three dots with ellipsis character

  punct = re.findall(r"[,.:!?…]", ellipsis) # get punctuation characters
  punct = list(set(punct))

  tokens = re.sub(r"[,.:!?…]", "", ellipsis)
  tokens = re.split(" ", tokens)
  tokens = [x for x in tokens if x]
  nonames = [x for x in tokens if not re.match(r"\b[A-Z]{2,}\b", x)]
  lowercase = [x.lower() for x in nonames]
  words = list(set(lowercase))
  words = [x for x in words if x not in punct]
  myRandom.shuffle(words)
  print(words)

  img = Image.open("input/seurat-1024.jpg")
  width = img.width
  vals = list(img.getdata())
  maxval = 255 * 255 * 255
  text = ""
  for i in range(len(vals)):
    start_of_para = i == 0 or re.match("\n\n", text[-2:]) != None
    start_of_sent = i == 0 or start_of_para or re.match(r"[.!?]", text[-1])
    after_punct = i > 0 and re.match(r"[,.:!?…]", text[-1])

    # pick either punctuation or word
    token = ""
    is_punct = False
    if not start_of_para and not start_of_sent and not after_punct and random.random() < PUNCT_PCT:
      is_punct = True
      token = punct[math.floor(random.random() * len(punct))]
    else:
      # get value from pixel
      tup = vals[i]
      product = 1
      for num in tup:
        product *= num
      # map that to an index of the word list
      index = round(product / maxval * len(words))
      token = words[index]
      if start_of_sent: # capitalise word, if at start of sentence
        token = token[0].upper() + token[1:]

    # add space before word, if word
    if not start_of_para and not is_punct:
      text += " "
    text += token

    # add newlines, if at end of row
    if i > 0 and i % width == 0:
      text += "\n\n"

  with open("output/seurat.txt", "w") as f:
    f.write(text)