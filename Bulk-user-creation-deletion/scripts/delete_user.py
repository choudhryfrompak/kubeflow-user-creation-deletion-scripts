import subprocess
import sys
import json
import time
from user_registry import mark_user_deleted, USER_REGISTRY_FILE

def run_command(command, timeout=30):
    print(f"Executing command: {command}")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate(timeout=timeout)
        if process.returncode != 0:
            print(f"Error executing command: {command}")
            print(f"Error message: {error.decode('utf-8')}")
            return False
        print(output.decode('utf-8'))
        return True
    except subprocess.TimeoutExpired:
        process.kill()
        print(f"Command timed out: {command}")
        return False

def force_delete_profile(username):
    # Remove finalizers from the profile
    run_command(f"kubectl patch profiles.kubeflow.org {username} -p '{{\"metadata\":{{\"finalizers\":null}}}}' --type=merge")
    # Force delete the profile
    return run_command(f"kubectl delete profiles.kubeflow.org {username} --force --grace-period=0")

def force_delete_namespace(username):
    # Remove finalizers from the namespace
    run_command(f"kubectl patch namespace {username} -p '{{\"metadata\":{{\"finalizers\":null}}}}' --type=merge")
    # Force delete the namespace
    return run_command(f"kubectl delete namespace {username} --force --grace-period=0")

def delete_user(username):
    # Step 1: Delete the Kubeflow profile
    if not run_command(f"kubectl delete profiles.kubeflow.org {username}"):
        print(f"Failed to delete Kubeflow profile for user {username}, attempting force delete")
        if not force_delete_profile(username):
            print(f"Force delete of Kubeflow profile for user {username} failed")
            return False

    # Step 2: Delete the namespace
    if not run_command(f"kubectl delete ns {username}"):
        print(f"Failed to delete namespace for user {username}, attempting force delete")
        if not force_delete_namespace(username):
            print(f"Force delete of namespace for user {username} failed")
            return False

    # Mark user as deleted in the registry
    mark_user_deleted(username)
    print(f"Successfully deleted user {username} and associated resources")
    return True

def get_users_by_class(class_name):
    try:
        with open(USER_REGISTRY_FILE, 'r') as file:
            registry = json.load(file)
            return [user['username'] for user in registry['users'] if user['class_tag'] == class_name and user['deletion_time'] is None]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading user registry: {e}")
        return []

def delete_class_users(class_name):
    users = get_users_by_class(class_name)
    if not users:
        print(f"No active users found for class {class_name}")
        return

    print(f"The following users will be deleted from class {class_name}:")
    for user in users:
        print(user)
    
    confirm = input("Are you sure you want to delete these users? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Deletion cancelled.")
        return

    for username in users:
        if delete_user(username):
            print(f"User {username} deleted successfully")
        else:
            print(f"Failed to delete user {username}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python delete_user.py <username1> [username2] [username3] ...")
        print("   or: python delete_user.py --class <class_name>")
        sys.exit(1)

    if sys.argv[1] == '--class':
        if len(sys.argv) != 3:
            print("Usage for class deletion: python delete_user.py --class <class_name>")
            sys.exit(1)
        delete_class_users(sys.argv[2])
    else:
        usernames = sys.argv[1:]
        for username in usernames:
            if delete_user(username):
                print(f"User {username} deleted successfully")
            else:
                print(f"Failed to delete user {username}")

if __name__ == "__main__":
    main()
