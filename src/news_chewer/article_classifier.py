import joblib
import numpy as np
from fastembed import TextEmbedding

MODEL_OUTPUT_PATH = "article_classifier.joblib"
CACHE_DIR = "./fastembed_cache"


class ArticleClassifier:
    def __init__(self, model_path: str = MODEL_OUTPUT_PATH, cache_dir: str = CACHE_DIR):
        self.classifier = joblib.load(model_path)
        self.embedder = TextEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            cache_dir=cache_dir
        )

    def predict(self, title: str, body_text: str) -> tuple[str, float]:
        """Classifies a single article.

        Returns:
            tuple[str, float]: (predicted_category, confidence_score)
        """
        combined = f"{title or ''}\n\n{body_text or ''}".strip()
        embedding = np.array(list(self.embedder.embed([combined])))

        # Get probabilities for all classes
        probabilities = self.classifier.predict_proba(embedding)[0]
        max_idx = np.argmax(probabilities)

        category = str(self.classifier.classes_[max_idx])
        confidence = float(probabilities[max_idx])

        return category, confidence

    def predict_batch(self, articles: list[dict[str, str]]) -> list[tuple[str, float]]:
        """Classifies a list of articles at once.

        Returns:
            list[tuple[str, float]]: List of (predicted_category, confidence_score) tuples
        """
        if not articles:
            return []

        texts = [
            f"{a.get('title', '')}\n\n{a.get('body_text', '')}".strip()
            for a in articles
        ]
        embeddings = np.array(list(self.embedder.embed(texts)))

        probabilities_batch = self.classifier.predict_proba(embeddings)
        max_indices = np.argmax(probabilities_batch, axis=1)

        results = []
        for i, idx in enumerate(max_indices):
            category = str(self.classifier.classes_[idx])
            confidence = float(probabilities_batch[i, idx])
            results.append((category, confidence))

        return results


# Example Usage:
if __name__ == "__main__":
    classifier = ArticleClassifier()

    # Single prediction
    title = "Central Bank Cuts Interest Rates"
    body = "The central bank decided to lower interest rates by 25 basis points to stimulate growth..."
    category, confidence = classifier.predict(title, body)

    print(f"Category: {category} | Confidence: {confidence:.2%}")