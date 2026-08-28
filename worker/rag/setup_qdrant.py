from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "pilgrim_temples"

client = QdrantClient(path="qdrant_data")

existing = [
    collection.name
    for collection in client.get_collections().collections
]

if COLLECTION_NAME not in existing:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1024,
            distance=Distance.COSINE
        )
    )

    print("Collection created.")
else:
    print("Collection already exists.")

info = client.get_collection(
    COLLECTION_NAME
)

print(f"Collection: {COLLECTION_NAME}")
print(f"Vector size: {info.config.params.vectors.size}")
print(f"Distance: {info.config.params.vectors.distance}")