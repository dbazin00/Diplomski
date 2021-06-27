import json
import nltk
# nltk.download("punkt")
import numpy as np
import fesbbook_app.Croatian_stemmer as cro_stem

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

import random

def tokenize(student_question):
    return nltk.word_tokenize(student_question)

def stem(word):
    return cro_stem.korjenuj(word.lower())

def bag_of_words(student_question, all_questions):
    student_question = [stem(word) for word in student_question]

    bag = np.zeros(len(all_questions), dtype=np.float32)

    for index, word in enumerate(all_questions):
        if word in student_question:
            bag[index] = 1

    return bag

class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(NeuralNet, self).__init__()

        self.l1 = nn.Linear(input_size, hidden_size)
        self.l2 = nn.Linear(hidden_size, hidden_size)
        self.l3 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        out = self.relu(out)
        out = self.l3(out)

        return out

def train():
    with open("fesbbook_app/chatbot_data.json", "r", encoding="utf8") as chatbot_data:
        chatbot_data = json.load(chatbot_data)

    tokenized_questions = []
    categories = []
    xy = []

    for intent in chatbot_data["chatbot"]:
        categories.append(intent["category"])
        for question in intent["questions"]:
            question_words = tokenize(question)
            tokenized_questions.extend(question_words)
            xy.append((question_words, intent["category"]))

    ignore_wods = ["?", "!", ".", ",", "'", "-", "/", ":", ";", "'", "..."]

    tokenized_questions = [stem(word) for word in tokenized_questions if word not in ignore_wods]
    tokenized_questions = sorted(set(tokenized_questions))

    categories = sorted(set(categories))

    x_train = []
    y_train = []
    # print(xy)

    for (question, category) in xy:
        bag = bag_of_words(question, tokenized_questions)
        x_train.append(bag)
        y_train.append(categories.index(category))


    x_train = np.array(x_train)
    y_train = np.array(y_train)
    # print(bag_of_words(["hello", "how", "are", "you"], ["hi", "hello", "i", "you", "bye", "thank", "cool"]))

    class ChatbotDataset(Dataset):
        def __init__(self):
            self.n_samples = len(x_train)
            self.x_data = x_train
            self.y_data = y_train

        def __getitem__(self, index):
            return self.x_data[index], self.y_data[index]

        def __len__(self):
            return self.n_samples

    batch_size = 8
    hidden_size = 8
    output_size = len(categories)
    input_size = len(x_train[0])
    learning_rate = 0.001
    num_epochs = 1000

    dataset = ChatbotDataset()
    train_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    # NeuralNet

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = NeuralNet(input_size, hidden_size, output_size).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    for epoch in range(num_epochs):
        for (words, labels) in train_loader:
            words = words.to(device)
            labels = labels.long().to(device)

            #forward
            outputs = model(words)
            loss = criterion(outputs, labels)

            #backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        if (epoch + 1) % 100 == 0:
            print(f"epoch {epoch+1}/{num_epochs}, loss={loss.item():.4f}")
            print(f"final loss, loss={loss.item():.4f}")

    data = {
        "model_state": model.state_dict(),
        "input_size": input_size,
        "hidden_size": hidden_size,
        "output_size": output_size,
        "all_words": tokenized_questions,
        "categories": categories
    }

    FILE = "fesbbook_app/data.pth"
    torch.save(data, FILE)

    print(f"training complete. file saved to {FILE}")

def chatbot(student_question):
    # train()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    with open("fesbbook_app/chatbot_data.json", "r", encoding="utf8") as chatbot_data:
        chatbot_data = json.load(chatbot_data)

    FILE = "fesbbook_app/data.pth"
    data = torch.load(FILE)

    input_size = data["input_size"]
    output_size = data["output_size"]
    hidden_size = data["hidden_size"]

    all_words = data["all_words"]
    categories = data["categories"]
    model_state = data["model_state"]


    model = NeuralNet(input_size, hidden_size, output_size).to(device)
    model.load_state_dict(model_state)
    model.eval()
   

    student_question = tokenize(student_question)
    x = bag_of_words(student_question, all_words)
    x = x.reshape(1, x.shape[0])
    x = torch.from_numpy(x)

    output = model(x)

    _, predicted = torch.max(output, dim=1)
    category = categories[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]

    if prob.item() > 0.75:
        for intent in chatbot_data["chatbot"]:
            if category == intent["category"]:
                return random.choice(intent['responses'])

    else: 
        return f"Ne razumijem pitanje"


# if __name__=='__main__':
#     train()
#     print("Let's chat! type 'quit' to exit")
#     while True:
#         student_question = input("You: ")
#         if student_question == "quit":
#             break
#         print(chatbot(student_question))
