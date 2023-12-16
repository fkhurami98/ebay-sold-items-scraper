# producer.py
import pika
from settings import search_keywords
import os

"""
Send ebay search terms to RabbitMQ queue from settings.py
"""

def send_to_rabbitmq(keyword, queue_name="ebay_keyword_queue"):
    # Use the below connection object if running locally without docker
    # connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))

    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_user = "user"  # Username as set in docker-compose
    rabbitmq_password = "password"  # Password as set in docker-compose

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitmq_host, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_publish(exchange="", routing_key=queue_name, body=keyword)
    print(f"Sent keyword '{keyword}' to {queue_name}")
    connection.close()


def main():
    for keyword in search_keywords:
        send_to_rabbitmq(keyword)


if __name__ == "__main__":
    main()
