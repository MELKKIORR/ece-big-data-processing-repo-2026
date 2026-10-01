# %% Dependencies
import socket
import json
import time
from confluent_kafka import Producer
from pywikibot.comms.eventstreams import EventStreams
from datetime import datetime, timedelta

# %% Helper Functions
# Serializer function to change message from python dict to json
value_serializer = lambda val: json.dumps(val).encode('utf-8')

# %% Producder Instantiation
# Set the producer configuration
conf = {'bootstrap.servers': 'localhost:9092',
        'client.id': socket.gethostname(),
        'compression.type': 'lz4'
}

# Instantiate the producer
producer = Producer(conf)

# %% Create wikistreams query
stream = EventStreams(
  streams=['recentchange', 'revision-create'], since='20260209'
)
stream.register_filter(server_name='fr.wikipedia.org', type='edit')

# %% Query EventStream
# Run a single query and inspect raw and example formatted output
change = next(stream)
print('Raw Message: ' + str(change))
print(
  '\n' # Add line breakd between outputs
  'Formatted Message: {type} on page "{title}" by "{user}" at {meta[dt]}.'
  .format(**change)
)

# %% Streaming Query
duration = 10 # Streaming window in minutes
start_time = datetime.now() # Current clock time
stop_time = start_time + timedelta(minutes=duration) #start+duration=stop

# Query stream for <duration> minutes
# Uncomment print change to examine output in interactive env
topic='wikistreams'
while datetime.now() < stop_time:
  change = next(stream)
  producer.produce(
    topic=topic,
    value=value_serializer(change)
  )
  print(' ')
  print(change)

# Close producer after run duration
print('\n wait 1 minute for last messages and then close producer')
time.sleep(60)
print('\n closing producer')
producer.close()
print('')
