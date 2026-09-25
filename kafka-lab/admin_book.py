from confluent_kafka.admin import AdminClient, NewTopic

#Connect to the Kafka broker and create a new topic named "book-topic" with 1 partition and a replication factor of 1
admin = AdminClient({"bootstrap.servers": "localhost:9092"})
new_topic = NewTopic("book-topic", num_partitions=1, replication_factor=1)

futures = admin.create_topics([new_topic])
for name, future in futures.items():
    try:
        future.result()
        print(f"Topic '{name}' créé")
    except Exception as e:
        print(f"Topic '{name}' non créé : {e}")