import re
from PIL import Image
import random

words = ""
PUNCT_PCT = 0.05 # add a smattering more punctuation to break up the words
with open("input/sunday.txt") as f:
  lyrics = " ".join(f.read().splitlines())
  nopunct = re.sub(r"[\[\]()]|#[0-9]|\"", "", lyrics)
  ellipsis = re.sub(r"\.\.\.", "…", nopunct)
  tokens = re.split(r"(…)|([ ,.:!?\-—–\"])", ellipsis)
  tokens = [x for x in tokens if x]
  nonames = [x for x in tokens if not re.match(r"\b[A-Z]{2,}\b", x)]
  lowercase = [x.lower() for x in nonames]
  words = set(lowercase)
  words = list(words)
  # words = sorted(words)
  punctuation = [x for x in words if re.match(r"[,.:!?]", x)]
  punct_rep = round(len(words) * PUNCT_PCT)
  for i in range(punct_rep):
    for x in punctuation:
      words += x
  random.shuffle(words)

  img = Image.open("input/seurat-1024.jpg")
  width = img.width
  vals = list(img.getdata())
  maxval = 255 * 255 * 255
  text = ""
  for i in range(len(vals)):
    # print(vals[i], end=" ")
    tup = vals[i]

    product = 1
    for num in tup:
      product *= num
    val = round(product / maxval * len(words))
    word = words[val]

    if i > 0 and (i - 1) % width != 0 and not re.match(r"[,.:!?]", word):
      text += " "
    text += words[val]

    if i > 0 and i % width == 0:
      text += "\n\n"

  with open("output/seurat.txt", "w") as f:
    f.write(text)