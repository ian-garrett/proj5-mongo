"""
Configuration of 'memos' Flask app. 
Edit to fit development or deployment environment.

"""
import random 

### My local development environment
#PORT=5000
#DEBUG = True
#MONGO_URL = "mongodb://memo:iremember@localhost:27333/memos"  # on Gnat

### On ix.cs.uoregon.edu (Ian Garrett's instance of MongoDB)
PORT=6066
DEBUG = False # Because it's unsafe to run outside localhost
MONGO_URL =  "mongodb://guest:blackberry7@localhost:4846/memos"  # on ix
