from sentence_transformers import SentenceTransformer
print("Downloading sentence transformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model downloaded successfully.")