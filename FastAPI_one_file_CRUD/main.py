from fastapi import FastAPI
from pydantic import BaseModel
import os


data_structure = {}

def setup():
	if not os.path.exists("data.txt"):
		return

	with open("data.txt","r") as file:
		while True:
			line = file.readline()
			if not line:
				break
			line = line.strip().split(",")
			data_structure[line[0]] = line[1]

class KeyValue(BaseModel):
	key: str
	value: str

app = FastAPI()
setup()

@app.get("/")
def read_root():
	return "Hello, CRUD application. Data Structure loaded. "

@app.post("/create")
def create_item(data: KeyValue):
	key = data.key
	value = data.value
	file = open("data.txt","a")
	file.write(f"{key},{value}\n")
	file.close()
	data_structure[key] = value
	return {"message":"Data added to file."}

@app.get("/retrieve")
def get_all_items():
	return data_structure

@app.put("/update")
def update_item(data: KeyValue):
	target_key = data.key
	new_value = data.value	
	
	with open("data.txt","r") as file:
		lines = file.readlines()

	with open("tmp.txt","w") as file:
		for line in lines:
			line = line.strip()
			key,value = line.split(",")
		
			if key == target_key:
				value = new_value
				data_structure[target_key] = new_value
			file.write(f"{key},{value}\n")
	
	with open("tmp.txt","r") as src, open ("data.txt","w") as dest:
		dest.write(src.read())	
		
	return "Updated"

@app.delete("/delete")
def delete_item(data: KeyValue):
	target_key = data.key
	
	with open("data.txt","r") as file:
		lines = file.readlines()

	with open("tmp.txt","w") as file:
		for line in lines:
			line = line.strip()
			key,value = line.split(",")
		
			if key == target_key:
				del data_structure[target_key]
				continue
			file.write(f"{key},{value}\n")
	
	with open("tmp.txt","r") as src, open ("data.txt","w") as dest:
		dest.write(src.read())	
		
	return "Deleted"

