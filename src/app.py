from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import pandas as pd
import re
import ast
import torch

app = Flask(__name__)

# Initialize model and tokenizer
model_id = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, load_in_4bit=True, device_map="auto")

def get_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = inputs.to('cuda')
    torch.cuda.empty_cache()
    outputs = model.generate(**inputs, max_new_tokens=128)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

@app.route('/process_article', methods=['POST'])
def process_article():
    data = request.json
    articles = data.get('articles', [])
    source = data.get('source', [])
    destination = data.get('destination', [])
    if not articles:
        return jsonify({"error": "No articles provided"}), 400
    
    results = extract_entities_from_articles(articles, source, destination)
    return jsonify({"entities": results})

def extract_entities_from_articles(articles, source, destination):
    delays = []
    for article in articles:
        prompt = f'''{article}

Instructions: Analyze the provided text to infer flight delay duration, if any, for the flight source and destination mentioned below. Only return a dict with key delay and value as the expected delay in minutes. Return expected delay 0 if nothing is found. Return -1 is expected to cancel.
Source: {source}
Destination: {destination}

Use inference to come up with delay. Use your best guess. If there is severe weather at one of the airports, flight could be cancelled or delayed. If the flight crew is on protest, flight could be cancelled.
Delay Dict:'''
        res = get_response(prompt)
        try:
            start_index = res.find('{')
            end_index = res.find('}')
            delay_map = res[start_index:end_index+1]
            delays.append(int(ast.literal_eval(delay_map)['delay']))
        except SyntaxError:
            pass
        except KeyError:
            pass
        except OutOfMemoryError:
            return delays
    return delays

if __name__ == '__main__':
    app.run(debug=True)
