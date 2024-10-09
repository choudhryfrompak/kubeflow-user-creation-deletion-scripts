import subprocess
import sys
from user_registry import mark_user_deleted

def run_command(command):
    print(f"Executing command: {command}")
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if process.returncode != 0:
        print(f"Error executing command: {command}")
        print(f"Error message: {error.decode('utf-8')}")
        return False
    print(output.decode('utf-8'))
    return True

def delete_user(username):
    # Step 1: Delete the Kubeflow profile
    if not run_command(f"kubectl delete profiles.kubeflow.org {username}"):
        print(f"Failed to delete Kubeflow profile for user {username}")
        return False

    # Step 2: Delete the namespace
    if not run_command(f"kubectl delete ns {username}"):
        print(f"Failed to delete namespace for user {username}")
        return False

    # Mark user as deleted in the registry
    mark_user_deleted(username)

    print(f"Successfully deleted user {username} and associated resources")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python delete_user.py <username1> [username2] [username3] ...")
        sys.exit(1)

    usernames = sys.argv[1:]
    for username in usernames:
        if delete_user(username):
            print(f"User {username} deleted successfully")
        else:
            print(f"Failed to delete user {username}")

if __name__ == "__main__":
    main()
