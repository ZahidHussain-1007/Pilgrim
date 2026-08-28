from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "pilgrim_temples"

client = QdrantClient(path="qdrant_data")

existing = [c.name for c in client.get_collections().collections]
if COLLECTION_NAME in existing:
    client.delete_collection(COLLECTION_NAME)
    print("Old collection deleted.")

client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=1024,
        distance=Distance.COSINE,
    ),
)

info = client.get_collection(COLLECTION_NAME)
print("New empty collection.")
print("Points:", info.points_count)
client.close()