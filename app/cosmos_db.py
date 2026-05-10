from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os

client = None
db = None
users_container = None
photos_container = None
comments_container = None
ratings_container = None


def init_cosmos():
    global client, db, users_container, photos_container, comments_container, ratings_container

    COSMOS_URL = os.getenv("COSMOS_URL")
    COSMOS_KEY = os.getenv("COSMOS_KEY")

    client = CosmosClient(COSMOS_URL, COSMOS_KEY)

    db = client.create_database_if_not_exists(id="snapshare")

    users_container = db.create_container_if_not_exists(
        id="users",
        partition_key=PartitionKey(path="/id"),
        offer_throughput=400
    )

    photos_container = db.create_container_if_not_exists(
        id="photos",
        partition_key=PartitionKey(path="/id"),
        offer_throughput=400
    )

    comments_container = db.create_container_if_not_exists(
        id="comments",
        partition_key=PartitionKey(path="/photo_id"),
        offer_throughput=400
    )

    ratings_container = db.create_container_if_not_exists(
        id="ratings",
        partition_key=PartitionKey(path="/photo_id"),
        offer_throughput=400
    )
