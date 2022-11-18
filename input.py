import spacy
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

# before = [{"POS": "ADV"}, {"LOWER": ",", "OP": "?"}, {"POS": "PRON"}, {"POS": "VERB", "OP": "?"}]
# after = [{"POS": "PRON"}, {"POS": "ADV"}, {"POS": "VERB", "OP": "?"}]
# end = [{"POS": "PRON"}, {"POS": "VERB"}, {"POS": "ADV"}]
# matcher.add("before", [before])
# matcher.add("after", [after])
# matcher.add("end", [end])

text = ""
# with open("carry-on.txt") as f:
with open("rebecca.txt") as f:
  text = f.read()
  text = text.replace("\n", " ")

doc = nlp(text)

# for sent in doc.sents:
#   for token in sent:
#     print(token.text, token.pos_, token.dep_)

results = []

# matches = matcher(doc[:5000])
matches = matcher(doc)
for match_id, start, end in matches:
  span = doc[start:end]
  results.append(span.text + "\n")
  # matchIdx = None
  # for i in range(0, len(results)):
  #   if results[i][0] == match_id:
  #     matchIdx = i
  #     break
  # if matchIdx:
  #   if results[matchIdx][2] <= end:
  #     continue
  #   else:
  #     results[matchIdx][2] = end
  #     span = doc[start:end]
  #     print(span.text + "—")
  # else:
  #   span = doc[start:end]
  #   print(span.text + "—")
  #   results.append([match_id, start, end])

with open("output/rebecca.txt", "w") as f:
  f.writelines(results)