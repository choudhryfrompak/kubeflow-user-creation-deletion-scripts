import subprocess
import yaml
import bcrypt
import uuid
from jinja2 import Template
import os
from user_registry import add_user

def run_command(command):
    print(f"Executing command: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if process.returncode != 0:
        print(f"Error executing command: {command}")
        print(f"Error message: {error.decode('utf-8')}")
        return None
    return output.decode('utf-8')

def get_user_input():
    profile_name = input("Enter profile name: ")
    user_email = input("Enter user email: ")
    username = input("Enter username: ")
    password = input("Enter password: ")
    cpu_limit = input("Enter CPU limit (e.g., '5'): ")
    memory_limit = input("Enter memory limit (available options:2-128): ")
    gpu_mem = input("Enter GPU memory limit (available options:1,2): ")
    gpu_count = input("Enter GPU count (available options: 1-2): ")
    storage_limit = input("Enter storage limit (available options: 1Gi-1000Gi): ")
    
    return {
        'profile_name': profile_name,
        'user_email': user_email,
        'username': username,
        'password': password,
        'cpu_limit': cpu_limit,
        'memory_limit': f"{memory_limit}Gi" if not memory_limit.endswith('Gi') else memory_limit,
        'gpu_mem': gpu_mem,
        'gpu_count': gpu_count,
        'storage_limit': storage_limit if storage_limit.endswith('Gi') else f"{storage_limit}Gi"
    }

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
    
    with open('../manifests/create-user.yaml', 'w') as file:
        file.write(rendered)
    
    print("Content written to create-user.yaml:")
    print(rendered)
    
    return True

def apply_user_yaml():
    if not os.path.exists('../manifests/create-user.yaml'):
        print("Error: create-user.yaml not found.")
        return None
    return run_command('kubectl apply -f ../manifests/create-user.yaml')

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

def update_dex_config(dex_config, user_data):
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

    hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = {
        'email': user_data['user_email'],
        'hash': hashed_password,
        'username': user_data['username'],
        'userID': str(uuid.uuid4().int)[:5]  # Using first 5 digits of a UUID
    }
    
    if 'staticPasswords' not in dex_config_yaml:
        dex_config_yaml['staticPasswords'] = []

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
    user_data = get_user_input()
    if not create_user_yaml(user_data):
        return
    
    result = apply_user_yaml()
    if result is None:
        return
    
    dex_config = get_dex_config()
    if dex_config is None:
        return
    
    updated_config = update_dex_config(dex_config, user_data)
    if updated_config is None:
        return

    result = apply_dex_config(updated_config)
    if result is None:
        return
    
    result = restart_dex()
    if result is None:
        return
    
    # Add user to the registry
    add_user(
        user_data['username'],
        user_data['user_email'],
        user_data['cpu_limit'],
        user_data['memory_limit'],
        user_data['gpu_mem'],
        user_data['gpu_count'],
        user_data['storage_limit']
    )
    
    print("User creation process completed successfully.")

if __name__ == "__main__":
    main()
