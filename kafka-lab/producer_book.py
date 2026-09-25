from confluent_kafka import Producer

TOPIC = "book-topic"
BOOK = "book.txt"

#Create the producer
producer = Producer({"bootstrap.servers": "localhost:9092"})

count = 0

#Send each line of the book to the Kafka topic, skipping empty lines
with open(BOOK, encoding="utf-8-sig") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line.strip():          # on saute les lignes vides
            continue
        producer.produce(TOPIC, value=line.encode("utf-8"))
        producer.poll(0)
        count += 1

producer.flush()
print(f"{count} lignes envoyées dans '{TOPIC}'")