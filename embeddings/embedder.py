from chunking.chunker import chunk_text
import time
from sentence_transformers import SentenceTransformer
model=SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
text="Virat Kohli (born 5 November 1988) is an Indian international cricketer and the former all-format captain of the Indian national cricket team. He is a right-handed batter and occasional right-arm medium pace bowler. Considered one of the greatest all-format batsmen in the history of cricket, he has been nicknamed the King, the Chase Master, and the Run Machine for his skills, records and ability to lead his team to victory. Kohli has the most centuries in ODIs and thesecond-most centuries in international cricket with 85 tons across all formats. He is also the leading run-scorer in the Indian Premier League. Kohli is the most successful Test captain of India with most wins and 3 consecutive Test mace retainments. He is the only batter to earn 900+ rating points across all 3 formats. Kohli was the captain of the 2008 U19 World Cup winning team and was a crucial member of the teams that won 2011 ODI World Cup, 2013 Champions Trophy, 2024 T20 World Cup, and 2025 Champions Trophy. He plays for Royal Challengers Bengaluru in the Indian Premier League and for Delhi in domestic cricket. In 2013, Kohli was ranked number one in the ODI batting rankings. In 2015, he achieved the same in T20I. In 2018, he was ranked number one in Test, making him the only Indian to hold the number one spot in all three formats. He is the first player to score 20,000 runs in a decade. He was the Cricketer of the Decade for 2011 to 2020. Kohli has won ten ICC Awards, making him the most awarded player in international cricket history. He won the ODI Player of the Year award four times in 2012, 2017, 2018, and 2023. He won the Cricketer of the Year award, on two occasions, in 2017 and 2018. In 2018, he became the first player to win all three major awards including Cricketer of the Year, ODI Player of the Year and Test Player of the Year in the same year. He was honored with the Spirit of Cricket Award in 2019 and given the Cricketer of the Decade and ODI Cricketer of the Decade in 2020. Kohli was named the Wisden Leading Cricketer in the World for three consecutive years."
chunks,stats=chunk_text(text, document_id="doc_1")
texts=[chunk["text"] for chunk in chunks]
start_time = time.time()
vectors = model.encode(texts, normalize_embeddings=True)
end_time = time.time()

embedding_time = end_time - start_time

print("Embedding time (seconds):", round(embedding_time, 3))
print(len(vectors[0]))
print("Vector dimension:", vectors.shape[1])
print("Total vectors:", vectors.shape[0])
vector_store = []

for vector, chunk in zip(vectors, chunks):
    vector_store.append(
        {
        "vector": vector,
        "metadata": chunk["metadata"],
        "text": chunk["text"]
        }
    )
print("Stored vectors:", len(vector_store))
print("One vector shape:", vector_store[0]["vector"].shape)
print("One metadata example:", vector_store[0]["metadata"])
