from sentence_transformers import SentenceTransformer, util

# Загрузка модели из Hugging Face
model = SentenceTransformer("TUKE-DeutscheTelekom/slovakbert-skquad-mnlr")  # Замените на ID нужной модели

# Пример предложений на словацком языке
sentences = [
    "Prvý most cez Zlatý roh nechal vybudovať cisár Justinián I. V roku 1502 vypísal sultán Bajezid II. súťaž na nový most.",
    "V ktorom roku vznikol druhý drevený most cez záliv Zlatý roh?",
    "Aká je priemerná dĺžka života v Eritrei?"
]

# Получение эмбеддингов для каждого предложения
embeddings = model.encode(sentences)
print("Shape of embeddings:", embeddings.shape)  # Вывод формы эмбеддингов, например (3, 768)

# Вычисление сходства между предложениями
similarities = util.cos_sim(embeddings, embeddings)
print("Similarity matrix:\n", similarities)
