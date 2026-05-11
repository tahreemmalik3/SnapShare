import uuid
import os

def upload_to_azure_blob(file_bytes: bytes, filename: str, content_type: str) -> str:
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "photos")

    if not connection_string:
        print("No Azure storage configured - saving locally")
        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        unique_name = f"{uuid.uuid4()}-{filename}"
        file_path = f"{upload_dir}/{unique_name}"
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return f"/static/uploads/{unique_name}"

    try:
        from azure.storage.blob import BlobServiceClient, ContentSettings
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container = blob_service.get_container_client(container_name)
        try:
            container.create_container(public_access="blob")
        except Exception:
            pass
        blob_name = f"{uuid.uuid4()}-{filename}"
        blob_client = container.get_blob_client(blob_name)
        blob_client.upload_blob(
            file_bytes,
            content_settings=ContentSettings(content_type=content_type),
            overwrite=True
        )
        url = blob_client.url
        print(f"Uploaded to Azure Blob: {url}")
        return url
    except Exception as e:
        print(f"Azure Blob upload error: {e}")
        return f"https://picsum.photos/seed/{uuid.uuid4()}/600/400"


def analyze_image_tags(image_url: str) -> list:
    try:
        vision_key = os.getenv("AZURE_VISION_KEY", "")
        vision_endpoint = os.getenv("AZURE_VISION_ENDPOINT", "")
        if not vision_key or not vision_endpoint:
            return []
        from azure.cognitiveservices.vision.computervision import ComputerVisionClient
        from msrest.authentication import CognitiveServicesCredentials
        client = ComputerVisionClient(vision_endpoint, CognitiveServicesCredentials(vision_key))
        result = client.tag_image(image_url)
        return [tag.name for tag in result.tags if tag.confidence > 0.7]
    except Exception as e:
        print(f"Azure Vision error: {e}")
        return []


def analyze_sentiment(texts: list) -> list:
    if not texts:
        return []
    try:
        text_key = os.getenv("AZURE_TEXT_KEY", "")
        text_endpoint = os.getenv("AZURE_TEXT_ENDPOINT", "")
        if not text_key or not text_endpoint:
            return ["neutral"] * len(texts)
        from azure.ai.textanalytics import TextAnalyticsClient
        from azure.core.credentials import AzureKeyCredential
        client = TextAnalyticsClient(endpoint=text_endpoint, credential=AzureKeyCredential(text_key))
        results = []
        for i in range(0, len(texts), 10):
            response = client.analyze_sentiment(documents=texts[i:i+10])
            for doc in response:
                results.append(doc.sentiment if not doc.is_error else "neutral")
        return results
    except Exception as e:
        print(f"Azure Sentiment error: {e}")
        return ["neutral"] * len(texts)


def get_overall_sentiment(sentiments: list) -> str:
    if not sentiments:
        return "neutral"
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for s in sentiments:
        counts[s] = counts.get(s, 0) + 1
    return max(counts, key=counts.get)
