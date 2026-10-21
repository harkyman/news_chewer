import os
import joblib
import numpy as np
import pandas as pd
from fastembed import TextEmbedding
from sklearn.linear_model import LogisticRegression

CSV_FILEPATH = "classifier training material.csv"
MODEL_OUTPUT_PATH = "article_classifier.joblib"
# Local directory where FastEmbed will cache model snapshots
CACHE_DIR = "./fastembed_cache" 

def train():
    df = pd.read_csv(CSV_FILEPATH)
    df["title"] = df["title"].fillna("")
    df["body_text"] = df["body_text"].fillna("")
    df = df.dropna(subset=["category"])
    df["combined_text"] = (df["title"] + "\n\n" + df["body_text"]).str.strip()
    
    texts = df["combined_text"].tolist()
    labels = df["category"].tolist()

    print("Loading FastEmbed model...")
    # FastEmbed downloads files on run #1, then reuses them locally on all future runs
    embedder = TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        cache_dir=CACHE_DIR
    )

    X = np.array(list(embedder.embed(texts)))
    y = np.array(labels)

    classifier = LogisticRegression(C=1.0, max_iter=1000)
    classifier.fit(X, y)

    joblib.dump(classifier, MODEL_OUTPUT_PATH)
    print(f"Successfully saved model to '{MODEL_OUTPUT_PATH}'")

if __name__ == "__main__":
    train()