import uuid
import json
from app.config import settings

# ─── AZURE BLOB STORAGE ──────────────────────────────────────────────────────

def upload_to_azure_blob(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Upload image bytes to Azure Blob Storage.
    Returns the public URL of the uploaded blob.
    Falls back to a placeholder if Azure is not configured.
    """
    if not settings.AZURE_STORAGE_CONNECTION_STRING:
        # Local dev fallback - return placeholder URL
        return f"https://via.placeholder.com/600x400?text={filename}"

    try:
        from azure.storage.blob import BlobServiceClient, ContentSettings
        blob_service = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        container = blob_service.get_container_client(settings.AZURE_STORAGE_CONTAINER)

        # Create container if it doesn't exist
        try:
            container.create_container(public_access="blob")
        except Exception:
            pass  # Already exists

        blob_name = f"{uuid.uuid4()}-{filename}"
        blob_client = container.get_blob_client(blob_name)
        blob_client.upload_blob(
            file_bytes,
            content_settings=ContentSettings(content_type=content_type),
            overwrite=True
        )
        return blob_client.url

    except Exception as e:
        print(f"Azure Blob upload error: {e}")
        return f"https://via.placeholder.com/600x400?text=Upload+Failed"


# ─── AZURE COMPUTER VISION ───────────────────────────────────────────────────

def analyze_image_tags(image_url: str) -> list[str]:
    """
    Use Azure Computer Vision to auto-tag an image.
    Returns a list of tag strings.
    Falls back to empty list if Azure is not configured.
    """
    if not settings.AZURE_VISION_KEY or not settings.AZURE_VISION_ENDPOINT:
        return []

    try:
        from azure.cognitiveservices.vision.computervision import ComputerVisionClient
        from msrest.authentication import CognitiveServicesCredentials

        client = ComputerVisionClient(
            settings.AZURE_VISION_ENDPOINT,
            CognitiveServicesCredentials(settings.AZURE_VISION_KEY)
        )
        result = client.tag_image(image_url)
        # Return tags with confidence > 0.7
        return [tag.name for tag in result.tags if tag.confidence > 0.7]

    except Exception as e:
        print(f"Azure Vision error: {e}")
        return []


# ─── AZURE TEXT ANALYTICS (SENTIMENT) ───────────────────────────────────────

def analyze_sentiment(texts: list[str]) -> list[str]:
    """
    Use Azure Text Analytics to analyse sentiment of comments.
    Returns list of sentiment labels: 'positive', 'negative', 'neutral'.
    Falls back to 'neutral' for all if Azure is not configured.
    """
    if not texts:
        return []

    if not settings.AZURE_TEXT_KEY or not settings.AZURE_TEXT_ENDPOINT:
        return ["neutral"] * len(texts)

    try:
        from azure.ai.textanalytics import TextAnalyticsClient
        from azure.core.credentials import AzureKeyCredential

        client = TextAnalyticsClient(
            endpoint=settings.AZURE_TEXT_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_TEXT_KEY)
        )
        # API limit: 10 docs per call
        results = []
        for i in range(0, len(texts), 10):
            batch = texts[i:i+10]
            response = client.analyze_sentiment(documents=batch)
            for doc in response:
                if not doc.is_error:
                    results.append(doc.sentiment)
                else:
                    results.append("neutral")
        return results

    except Exception as e:
        print(f"Azure Text Analytics error: {e}")
        return ["neutral"] * len(texts)


def get_overall_sentiment(sentiments: list[str]) -> str:
    """Given a list of sentiments, return the dominant one."""
    if not sentiments:
        return "neutral"
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for s in sentiments:
        counts[s] = counts.get(s, 0) + 1
    return max(counts, key=counts.get)
