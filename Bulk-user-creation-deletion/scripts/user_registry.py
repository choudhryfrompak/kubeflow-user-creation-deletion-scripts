import json
from datetime import datetime

USER_REGISTRY_FILE = '../users/user_registry.json'

def init_registry():
    with open(USER_REGISTRY_FILE, 'w') as file:
        json.dump({"classes": {}, "users": []}, file)

def add_class(class_name, class_tag, num_users, cpu_limit, memory_limit, gpu_mem, gpu_count, storage_limit):
    with open(USER_REGISTRY_FILE, 'r+') as file:
        registry = json.load(file)
        new_class = {
            'class_name': class_name,
            'class_tag': class_tag,
            'num_users': num_users,
            'cpu_limit': cpu_limit,
            'memory_limit': memory_limit,
            'gpu_mem': gpu_mem,
            'gpu_count': gpu_count,
            'storage_limit': storage_limit,
            'creation_time': datetime.now().isoformat()
        }
        registry['classes'][class_tag] = new_class
        file.seek(0)
        json.dump(registry, file, indent=2)
        file.truncate()

def add_user(username, email, password, class_tag):
    with open(USER_REGISTRY_FILE, 'r+') as file:
        registry = json.load(file)
        new_user = {
            'username': username,
            'email': email,
            'password': password,
            'class_tag': class_tag,
            'creation_time': datetime.now().isoformat(),
            'deletion_time': None
        }
        registry['users'].append(new_user)
        file.seek(0)
        json.dump(registry, file, indent=2)
        file.truncate()

def mark_user_deleted(username):
    with open(USER_REGISTRY_FILE, 'r+') as file:
        registry = json.load(file)
        for user in registry['users']:
            if user['username'] == username:
                user['deletion_time'] = datetime.now().isoformat()
        file.seek(0)
        json.dump(registry, file, indent=2)
        file.truncate()

def get_class_info(class_tag):
    with open(USER_REGISTRY_FILE, 'r') as file:
        registry = json.load(file)
        return registry['classes'].get(class_tag)

# Initialize the registry if it doesn't exist
try:
    with open(USER_REGISTRY_FILE, 'r') as file:
        json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    init_registry()
