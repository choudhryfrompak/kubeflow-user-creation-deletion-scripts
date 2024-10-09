import subprocess
import yaml
import bcrypt
import uuid
from jinja2 import Template
import os
import random
import string
from user_registry import add_class, add_user, get_class_info

def run_command(command):
    print(f"Executing command: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if process.returncode != 0:
        print(f"Error executing command: {command}")
        print(f"Error message: {error.decode('utf-8')}")
        return None
    return output.decode('utf-8')

def get_class_input():
    class_name = input("Enter class name for class registry: ")
    class_tag = input("Enter class tag: ")
    num_users = int(input("Enter number of users to create: "))
    cpu_limit = input("Enter CPU limit for all users (e.g., '5'): ")
    memory_limit = input("Enter memory limit for all users (available options:2-128): ")
    gpu_mem = input("Enter GPU memory limit for all users (available options:1,2): ")
    gpu_count = input("Enter GPU count for all users (available options: 1-2): ")
    storage_limit = input("Enter storage limit for all users (available options: 1Gi-1000Gi): ")
    
    return {
        'class_name': class_name,
        'class_tag': class_tag,
        'num_users': num_users,
        'cpu_limit': cpu_limit,
        'memory_limit': f"{memory_limit}Gi" if not memory_limit.endswith('Gi') else memory_limit,
        'gpu_mem': gpu_mem,
        'gpu_count': gpu_count,
        'storage_limit': storage_limit if storage_limit.endswith('Gi') else f"{storage_limit}Gi"
    }

def generate_password():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

def create_user_yaml(user_data):
    template_path = '../manifests/create-user-template.yaml'
    if not os.path.exists(template_path):
        print(f"Error: {template_path} not found.")
        return False

    with open(template_path, 'r') as file:
        template_content = file.read()
        if not template_content.strip():
            print(f"Error: {template_path} is empty.")
            return False
        template = Template(template_content)
    
    rendered = template.render(user_data)
    
    with open(f'../manifests/create-user-{user_data["username"]}.yaml', 'w') as file:
        file.write(rendered)
    
    print(f"Content written to create-user-{user_data['username']}.yaml")
    
    return True

def apply_user_yaml(username):
    return run_command(f'kubectl apply -f ../manifests/create-user-{username}.yaml')

def get_dex_config():
    result = run_command('kubectl get configmap dex -n auth -o yaml > ../manifests/config.yaml')
    if result is None:
        print("Error: Failed to retrieve Dex configuration.")
        return None
    
    try:
        with open('../manifests/config.yaml', 'r') as file:
            return file.read()
    except FileNotFoundError:
        print("Error: config.yaml file not found after kubectl command.")
        return None
    except IOError as e:
        print(f"Error reading config.yaml: {e}")
        return None

def update_dex_config(dex_config, users_data):
    if dex_config is None:
        print("Error: Dex configuration is None.")
        return None

    try:
        config = yaml.safe_load(dex_config)
    except yaml.YAMLError as e:
        print(f"Error parsing Dex configuration: {e}")
        return None

    if 'data' not in config or 'config.yaml' not in config['data']:
        print("Error: Unexpected Dex configuration structure.")
        return None

    try:
        dex_config_yaml = yaml.safe_load(config['data']['config.yaml'])
    except yaml.YAMLError as e:
        print(f"Error parsing Dex config.yaml: {e}")
        return None

    if 'staticPasswords' not in dex_config_yaml:
        dex_config_yaml['staticPasswords'] = []

    for user_data in users_data:
        hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = {
            'email': user_data['user_email'],
            'hash': hashed_password,
            'username': user_data['username'],
            'userID': str(uuid.uuid4())[:5]  # Using first 5 characters of a UUID
        }
        
        dex_config_yaml['staticPasswords'].append(new_user)
    
    config['data']['config.yaml'] = yaml.dump(dex_config_yaml, default_flow_style=False)
    
    return yaml.dump(config, default_flow_style=False)

def apply_dex_config(config):
    if config is None:
        print("Error: Dex configuration is None. Cannot apply.")
        return None

    with open('../manifests/updated-dex-config.yaml', 'w') as file:
        file.write(config)
    
    return run_command('kubectl apply -f ../manifests/updated-dex-config.yaml')

def restart_dex():
    return run_command('kubectl rollout restart deployment dex -n auth')

def main():
    class_data = get_class_input()
    
    # Add class information to the registry
    add_class(
        class_data['class_name'],
        class_data['class_tag'],
        class_data['num_users'],
        class_data['cpu_limit'],
        class_data['memory_limit'],
        class_data['gpu_mem'],
        class_data['gpu_count'],
        class_data['storage_limit']
    )

    users_data = []

    for i in range(1, class_data['num_users'] + 1):
        username = f"{class_data['class_tag']}-{i}"
        user_email = f"{username}@paf-iast"
        password = generate_password()

        user_data = {
            'profile_name': username,
            'user_email': user_email,
            'username': username,
            'password': password,
            'cpu_limit': class_data['cpu_limit'],
            'memory_limit': class_data['memory_limit'],
            'gpu_mem': class_data['gpu_mem'],
            'gpu_count': class_data['gpu_count'],
            'storage_limit': class_data['storage_limit']
        }

        users_data.append(user_data)

        if not create_user_yaml(user_data):
            print(f"Failed to create YAML for user {username}")
            continue

        result = apply_user_yaml(username)
        if result is None:
            print(f"Failed to apply YAML for user {username}")
            continue

        # Add user to the registry
        add_user(username, user_email, password, class_data['class_tag'])

        print(f"User {username} created successfully with password: {password}")

    dex_config = get_dex_config()
    if dex_config is None:
        return

    updated_config = update_dex_config(dex_config, users_data)
    if updated_config is None:
        return

    result = apply_dex_config(updated_config)
    if result is None:
        return

    result = restart_dex()
    if result is None:
        return

    print(f"Bulk user creation process for class {class_data['class_name']} completed successfully.")

if __name__ == "__main__":
    main()
