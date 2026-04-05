from publish_blog import load_published, get_embedding, save_embedding
import time

published = load_published()
print(f"Ukupno naslova: {len(published)}")

for i, entry in enumerate(published):
    title = entry["title"] if isinstance(entry, dict) else entry
    print(f"[{i+1}/{len(published)}] {title}")
    vec = get_embedding(title)
    save_embedding(title, vec)
    time.sleep(0.3)

print("Done! Sada commituj published_embeddings.json")
