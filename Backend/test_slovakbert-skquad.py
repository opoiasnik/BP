from sentence_transformers import SentenceTransformer, util


model = SentenceTransformer("TUKE-DeutscheTelekom/slovakbert-skquad-mnlr")


sentences = [
    "Prvý most cez Zlatý roh nechal vybudovať cisár Justinián I. V roku 1502 vypísal sultán Bajezid II. súťaž na nový most.",
    "V ktorom roku vznikol druhý drevený most cez záliv Zlatý roh?",
    "Aká je priemerná dĺžka života v Eritrei?"
]

embeddings = model.encode(sentences)
print("Shape of embeddings:", embeddings.shape)


similarities = util.cos_sim(embeddings, embeddings)
print("Similarity matrix:\n", similarities)
