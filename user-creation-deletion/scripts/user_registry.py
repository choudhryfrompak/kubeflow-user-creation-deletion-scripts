import json
from datetime import datetime

USER_REGISTRY_FILE = '../users/user_registry.json'

def init_registry():
    with open(USER_REGISTRY_FILE, 'w') as file:
        json.dump([], file)

def add_user(username, email, cpu_limit, memory_limit, gpu_mem, gpu_count, storage_limit):
    with open(USER_REGISTRY_FILE, 'r+') as file:
        users = json.load(file)
        new_user = {
            'username': username,
            'email': email,
            'cpu_limit': cpu_limit,
            'memory_limit': memory_limit,
            'gpu_mem': gpu_mem,
            'gpu_count': gpu_count,
            'storage_limit': storage_limit,
            'creation_time': datetime.now().isoformat(),
            'deletion_time': None
        }
        users.append(new_user)
        file.seek(0)
        json.dump(users, file, indent=2)
        file.truncate()

def mark_user_deleted(username):
    with open(USER_REGISTRY_FILE, 'r+') as file:
        users = json.load(file)
        for user in users:
            if user['username'] == username:
                user['deletion_time'] = datetime.now().isoformat()
        file.seek(0)
        json.dump(users, file, indent=2)
        file.truncate()

# Initialize the registry if it doesn't exist
try:
    with open(USER_REGISTRY_FILE, 'r') as file:
        json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    init_registry()
