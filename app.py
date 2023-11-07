from flask import Flask, render_template, request, jsonify
from chat import get_response
from pymongo import MongoClient

app = Flask(__name__)

# Establish a connection to the MongoDB database
client = MongoClient('mongodb+srv://sagul:im2fast4U@test.ab0sxwg.mongodb.net/')
db = client['chatbot_database']  # Use your database name here
conversations = db['conversations']  # Use your collection name here

def save_conversation(user_message, bot_response):
    # Create a new conversation document
    conversation = {
        "user_message": user_message,
        "bot_response": bot_response
    }

    # Insert the conversation into the MongoDB collection
    conversations.insert_one(conversation)

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


