import numpy as np
from app.ingestion.pipeline.processor import embed

# ---------------------------------------
# Keyword routing rules
# ---------------------------------------
domain_keywords = {
    "general_printer": [
        "printer", "print", "toner", "drum", "paper jam", "streak",
        "scan", "mfc", "hl", "dcp"
    ],
    "general_server": [
        "server", "active directory", "domain controller", "dfs",
        "replication", "gpo", "group policy"
    ],
    "general_network": [
        "router", "switch", "firewall", "wifi", "dhcp", "dns", "vlan"
    ],
    "general_m365": [
        "office", "outlook", "exchange", "sharepoint", "onedrive",
        "microsoft 365", "m365"
    ],
    "general_security": [
        "antivirus", "malware", "phishing", "ransomware", "threat"
    ],
    "general_windows": [
        "windows", "blue screen", "bsod", "boot", "login", "profile"
    ]
}

# ---------------------------------------
# Cosine similarity
# ---------------------------------------
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# ---------------------------------------
# Compute centroids for semantic routing
# ---------------------------------------
def compute_centroids(collections):
    centroids = {}

    for name, col in collections.items():
        try:
            results = col.get(include=["embeddings"])
        except Exception as e:
            print(f"Skipping centroid for {name}: no embeddings or index not found ({e})")
            continue

        embeddings = results.get("embeddings", [])
        if embeddings is None or len(embeddings) == 0:
            print(f"Skipping centroid for empty collection: {name}")
            continue

        centroid = np.mean(embeddings, axis=0)
        centroids[name] = centroid

    return centroids


# ---------------------------------------
# Route a question to the correct collection
# ---------------------------------------
def route_collection(question, collections, centroids):
    q = question.lower()

    # 1. Keyword routing
    for domain, keywords in domain_keywords.items():
        if any(k in q for k in keywords):
            # If the domain exists as a collection, use it
            if domain in collections:
                return collections[domain]

            # No hard-coded general_it anymore — just fall back
            return next(iter(collections.values()))

    # 2. Semantic routing
    q_emb = np.array(embed([question])[0])
    best_collection = None
    best_score = -1

    for name, centroid in centroids.items():
        score = cosine_similarity(q_emb, centroid)
        if score > best_score:
            best_score = score
            best_collection = name

    # Final fallback
    if best_collection in collections:
        return collections[best_collection]

    return next(iter(collections.values()))

