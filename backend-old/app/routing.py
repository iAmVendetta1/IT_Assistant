import numpy as np
from backend.app.ingestion import embed

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
        results = col.get(include=["embeddings"])
        embs = np.array(results["embeddings"])
        if len(embs) == 0:
            continue
        centroids[name] = embs.mean(axis=0)
    return centroids

# ---------------------------------------
# Route a question to the correct collection
# ---------------------------------------
def route_collection(question, collections, centroids):
    q = question.lower()

    # 1. Client detection
    client_collections = [
        name for name in collections.keys()
        if not name.startswith("general_")
    ]
    for client_name in client_collections:
        if client_name.lower() in q:
            return collections[client_name]

    # 2. Keyword routing
    for domain, keywords in domain_keywords.items():
        if any(k in q for k in keywords):
            return collections[domain]

    # 3. Semantic fallback
    q_emb = np.array(embed([question])[0])
    best_collection = None
    best_score = -1

    for name, centroid in centroids.items():
        score = cosine_similarity(q_emb, centroid)
        if score > best_score:
            best_score = score
            best_collection = name

    return collections[best_collection]

