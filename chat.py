import random
import json
import torch
import google.generativeai as palm
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

# Configure the palm API
palm.configure(api_key='AIzaSyD7aMS1rqwIFPp1iG5D3ijxfimujoPv2nI')

# Get the palm model
palm_models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
palm_model = palm_models[0].name

def get_palm_response(prompt):
    prompt += " in India"
    completion = palm.generate_text(
        model=palm_model,
        prompt=prompt,
        temperature=0,
        max_output_tokens=1000,
    )
    return completion.result

def get_response(msg):
    sentence = tokenize(msg)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                return random.choice(intent['responses'])
    
    # If no matching intent was found, use palm to generate a response
    return get_palm_response(msg)
def save_conversation(user_message, bot_response):
    with open('intents.json', 'r+') as file:
        data = json.load(file)
        existing_conversations = [intent for intent in data['intents'] if 'conversation' in intent['tag']]
        if not any(conv for conv in existing_conversations if conv['patterns'][0] == user_message and conv['responses'][0] == bot_response):
            conversation_count = len(existing_conversations)
            new_conversation_tag = f"conversation_{conversation_count + 1}"
            data['intents'].append({
                "tag": new_conversation_tag,
                "patterns": [user_message],
                "responses": [bot_response]
            })
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()

if __name__ == "__main__":
    print("Let's chat! (type 'quit' to exit)")
    while True:
        sentence = input("You: ")
        if sentence == "quit":
            break

        resp = get_response(sentence)
        print("Carbon:",resp)
        
        # Save the conversation
        save_conversation(sentence, resp)