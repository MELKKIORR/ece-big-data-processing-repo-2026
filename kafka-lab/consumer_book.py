import re
from collections import Counter
from confluent_kafka import Consumer

TOPIC = "book-topic"
OUTPUT = "cleaned_book.txt"

#Commons words to ignore when counting word frequency
STOPWORDS = {
    "the", "and", "a", "an", "of", "to", "in", "is", "it", "that", "i", "was",
    "he", "she", "his", "her", "you", "my", "me", "with", "for", "on", "as",
    "had", "be", "at", "by", "not", "but", "this", "which", "from", "or",
    "have", "so", "all", "were", "we", "they", "them", "their", "are", "been",
}

#Identifier of the consumer group and the topic to subscribe to
consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "book-group",
    "auto.offset.reset": "earliest",
})
consumer.subscribe([TOPIC])


def clean(line):
    #Lowercase the line, remove punctuation, digits, and underscores, then split into words and filter out stopwords and single-character words
    line = line.lower()
    line = re.sub(r"[^\w\s]|\d|_", " ", line)       # ponctuation, chiffres
    return [w for w in line.split() if w not in STOPWORDS and len(w) > 1]

word_counts = Counter()
in_body = False
empty_polls = 0

with open(OUTPUT, "w", encoding="utf-8") as out:
    #Stop after 10 consecutive empty polls to avoid infinite waiting if the topic is empty
    try:
        while empty_polls < 10:                    
            msg = consumer.poll(1.0)
            if msg is None:
                empty_polls += 1
                continue
            if msg.error():
                print(f"Erreur : {msg.error()}")
                continue
            empty_polls = 0
            text = msg.value().decode("utf-8")

            if "*** START OF" in text:             # début du livre
                in_body = True
                continue
            if "*** END OF" in text:               # fin du livre
                in_body = False
                continue
            if not in_body:
                continue

            words = clean(text)
            if words:
                out.write(" ".join(words) + "\n")
                word_counts.update(words)
                print(f"Rcvd & cleaned: {' '.join(words)}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


#Write the top 20 most common words to a file
with open("word_counts.txt", "w", encoding="utf-8") as wc:
    for word, n in word_counts.most_common(20):
        wc.write(f"{word}: {n}\n")

print(f"\nTexte nettoyé écrit dans {OUTPUT}")
print("Top 10 :", word_counts.most_common(10))