import spacy

nlp = spacy.load("en_core_web_sm")

text = ""
with open("carry-on.txt") as f:
  text = f.read()
  text = text.replace("\n", " ")

doc = nlp(text)

for sent in doc.sents:
# for sent in doc[:100].sents:
  nsubj = None
  for nc in sent.noun_chunks:
    if nc.root.dep_ == "nsubj":
      nsubj = nc
      break

  root = sent.root

  dobj = None
  for nc in sent.noun_chunks:
    if nc.root.dep_ == "dobj":
      dobj = nc
      break

  xcomp = None
  for token in sent:
    if (token.dep_ == "xcomp"):
      xcomp = token
      break

  adj = None
  if (not dobj) and (not xcomp):
    for token in sent:
      if token.pos_ == "ADJ" and token.head == root:
        adj = token
        break

  objdet = None
  obj = None
  if (not dobj) and (not xcomp) and (not adj):
    for token in sent:
      if token.pos_ == "NOUN" and token.head == root:
        obj = token
        break
    if obj:
      for token in sent:
        if token.pos_ == "DET" and token.head == obj:
          objdet = token
          break

  punct = None
  for i in range(len(sent) - 1, -1, -1):
    token = sent[i]
    if (token.text == "." or token.text == "!" or token.text == "?") and token.head == root:
      punct = token
      break

  if nsubj and root:
    if dobj:
      if root.pos_ == "NOUN":
        print(root, nsubj.text, nsubj.root.head.text + punct.text if punct else "")
      elif root.pos_ == "VERB":
        print(nsubj.text, root.text, dobj.text + punct.text if punct else "")
    elif xcomp:
      print(nsubj.text, root.text, xcomp.text + punct.text if punct else "")
    elif adj:
      print(nsubj.text, root.text, adj.text + punct.text if punct else "")
    elif obj:
      if objdet:
        print(nsubj.text, root.text, objdet.text, obj.text + punct.text if punct else "")
      else:
        print(nsubj.text, root.text, obj.text + punct.text if punct else "")
    
    # print("-- TOKENS --")
    # for token in sent:
    #   print(token.text, token.pos_, token.dep_, token.head)
    # print()
  else:
    # print()
    # for token in sent:
    #   print(token.text, token.pos_, token.dep_)
    # print()
    continue