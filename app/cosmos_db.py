from azure.cosmos import CosmosClient, PartitionKey, exceptions
from dotenv import load_dotenv
import os

load_dotenv()

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "snapshare"

client = CosmosClient(COSMOS_URL, COSMOS_KEY)

db = client.create_database_if_not_exists(id=DATABASE_NAME)

users_container = db.create_container_if_not_exists(
    id="users", partition_key=PartitionKey(path="/id")
)
photos_container = db.create_container_if_not_exists(
    id="photos", partition_key=PartitionKey(path="/id")
)
comments_container = db.create_container_if_not_exists(
    id="comments", partition_key=PartitionKey(path="/photo_id")
)
ratings_container = db.create_container_if_not_exists(
    id="ratings", partition_key=PartitionKey(path="/photo_id")
)
# ─── USER OPERATIONS ──────────────────────────────────────────────────────────

def get_user_by_email(email: str):
    query = "SELECT * FROM c WHERE c.email = @email"
    params = [{"name": "@email", "value": email}]
    items = list(users_container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    return items[0] if items else None


def get_user_by_id(user_id: str):
    try:
        return users_container.read_item(item=user_id, partition_key=user_id)
    except exceptions.CosmosResourceNotFoundError:
        return None

def create_user(user_data: dict):
    return users_container.create_item(body=user_data)

# ─── PHOTO OPERATIONS ─────────────────────────────────────────────────────────

def create_photo(photo_data: dict):
    return photos_container.create_item(body=photo_data)

def get_all_photos(search: str = None, owner_id: str = None):
    if owner_id:
        query = "SELECT * FROM c WHERE c.owner_id = @owner_id ORDER BY c.created_at DESC"
        params = [{"name": "@owner_id", "value": owner_id}]
    elif search:
        term = search.lower()
        query = """SELECT * FROM c WHERE 
                    CONTAINS(LOWER(c.title), @term) OR 
                    CONTAINS(LOWER(c.caption), @term) OR 
                    CONTAINS(LOWER(c.location), @term) OR
                    CONTAINS(LOWER(c.people), @term)
                    ORDER BY c.created_at DESC"""
        params = [{"name": "@term", "value": term}]
    else:
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        params = []
    return list(photos_container.query_items(query=query, parameters=params, enable_cross_partition_query=True))

def get_photo_by_id(photo_id: str):
    try:
        return photos_container.read_item(item=photo_id, partition_key=photo_id)
    except exceptions.CosmosResourceNotFoundError:
        return None

def delete_photo(photo_id: str):
    photos_container.delete_item(item=photo_id, partition_key=photo_id)

# ─── COMMENT OPERATIONS ───────────────────────────────────────────────────────

def create_comment(comment_data: dict):
    return comments_container.create_item(body=comment_data)

def get_comments_for_photo(photo_id: str):
    query = "SELECT * FROM c WHERE c.photo_id = @photo_id ORDER BY c.created_at ASC"
    params = [{"name": "@photo_id", "value": photo_id}]
    return list(comments_container.query_items(query=query, parameters=params, enable_cross_partition_query=True))

# ─── RATING OPERATIONS ────────────────────────────────────────────────────────

def create_or_update_rating(rating_data: dict):
    query = "SELECT * FROM c WHERE c.photo_id = @photo_id AND c.user_id = @user_id"
    params = [{"name": "@photo_id", "value": rating_data['photo_id']},
              {"name": "@user_id", "value": rating_data['user_id']}]
    existing = list(ratings_container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    if existing:
        existing[0]['score'] = rating_data['score']
        return ratings_container.replace_item(item=existing[0]['id'], body=existing[0])
    return ratings_container.create_item(body=rating_data)

def get_ratings_for_photo(photo_id: str):
    query = "SELECT * FROM c WHERE c.photo_id = @photo_id"
    params = [{"name": "@photo_id", "value": photo_id}]
    return list(ratings_container.query_items(query=query, parameters=params, enable_cross_partition_query=True))

def get_user_rating_for_photo(photo_id: str, user_id: str):
    query = "SELECT * FROM c WHERE c.photo_id = @photo_id AND c.user_id = @user_id"
    params = [{"name": "@photo_id", "value": photo_id},
              {"name": "@user_id", "value": user_id}]
    items = list(ratings_container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    return items[0] if items else None
