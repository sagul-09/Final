from flask import Flask, render_template, request, jsonify
from chat import get_response
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import json

app = Flask(__name__)

# Establish a connection to the MongoDB database
client = MongoClient('mongodb+srv://sagul:im2fast4U@test.ab0sxwg.mongodb.net/')
db = client['chatbot_database']  # Use your database name here
conversations = db['conversations']  # Use your collection name here

try:
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
    print("MongoDB connection successful")
except ConnectionFailure:
    print("MongoDB connection failed")

def save_conversation(user_message, bot_response):
    # Check if the conversation already exists in MongoDB
    existing_conversation = conversations.find_one({
        "patterns": {"$elemMatch": {"$eq": user_message}},
        "responses": {"$elemMatch": {"$eq": bot_response}},
        "tag": "conversation"
    })

    # If the conversation does not exist, save it to MongoDB
    if existing_conversation is None:
        conversation = {
            "tag": "conversation",
            "patterns": [user_message],
            "responses": [bot_response]
        }
        conversations.insert_one(conversation)

    # Save to intents.json
    with open('intents.json', 'r+') as file:
        data = json.load(file)
        existing_conversations = [intent for intent in data['intents'] if intent['tag'] == 'conversation']
        if not any(conv for conv in existing_conversations if conv['patterns'][0] == user_message and conv['responses'][0] == bot_response):
            data['intents'].append({
                "tag": "conversation",
                "patterns": [user_message],
                "responses": [bot_response]
            })
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

@app.route('/')
def index_get():
    return render_template("base.html") 

@app.route("/predict", methods=['POST'])
def predict():
    text = request.get_json().get("message")  # text validity
    response = get_response(text)
    save_conversation(text, response)  # Save the conversation
    message = {"answer": response}
    return jsonify(message)

if __name__=="__main__":
    app.run(debug=True)