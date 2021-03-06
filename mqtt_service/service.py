import paho.mqtt.client as mqtt
import pymongo
import time
import threading

broker_address = "192.168.137.1"
subTopic = "hotel/+/relay"
localRooms = []

def on_message(client, userdata, message):
   global localRooms
   _topic = str(message.topic)
   _data = bool(int(str(message.payload.decode("utf-8"))))

   start = "hotel/"
   end = "/relay"
   room = int(_topic[len(start):-len(end)])
   
   for localRoom in localRooms:
      if localRoom['name'] == room:
         localRoom['state'] = _data
   dbRooms.find_one_and_update({'name': room}, {'$set': {'state': _data}})

def on_disconnect (client, userdata, rc):
   print("MQTT Disconnected")

def on_connect (client, obj, flags, rc):
   print("MQTT Connected")
   client.subscribe(subTopic)
   # polling_relay()

def mqtt_client():
   client.on_message=on_message
   client.on_connect=on_connect
   client.on_disconnect=on_disconnect
   client.connect(broker_address)
   print("Connecting MQTT...")
   client.loop_forever()

def polling_relay():
   for room in localRooms:
      client.publish("hotel/" + str(room['name']) + "/admin", "RELAY_STAT")

def initfromdb():
   for room in dbRooms.find({}, projection={'_id': False, 'name': True, 'state': True}):
      localRooms.append(room)

def retfromdb():
   for dbRoom in dbRooms.find({}, projection={'_id': False, 'name': True, 'state': True}):
      for temp in localRooms:
         if temp['name'] == dbRoom['name']:
            if temp['state'] != dbRoom['state']:
               temp['state'] = dbRoom['state']
               if temp['state']:
                  stat = "RELAY_ON"
               else:
                  stat = "RELAY_OFF"
               client.publish("hotel/" + str(temp['name']) + "/admin", stat)

def writebacktodb():
   for room in localRooms:
      dbRooms.find_one_and_update({'name': room['name']}, {'$set': {'state': room['state']}})

def db_read():
   while(1):
      retfromdb()

mongo_client = pymongo.MongoClient(
   "mongodb+srv://minhtaile2712:imissyou@cluster0-wyhfl.mongodb.net/test?retryWrites=true&w=majority")
db = mongo_client.test
dbRooms = db.rooms
initfromdb()

client = mqtt.Client()
mqtt_thread = threading.Thread(target=mqtt_client)
mqtt_thread.start()
db_thread = threading.Thread(target=db_read)
db_thread.start()