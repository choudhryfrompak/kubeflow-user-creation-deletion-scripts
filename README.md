# Kubeflow User Management Scripts

## Description

This project provides a set of Python scripts for managing user profiles in a Kubeflow environment. It automates the process of creating and deleting user profiles, updating Dex authentication configurations, and maintaining a local registry of users.

### Key Features:

- Automated user profile creation in Kubeflow
- User deletion with proper cleanup
- Dex configuration management for user authentication
- Local JSON-based user registry for tracking user details and actions
- Customizable resource quotas for each user

## System Components

1. `create-user.py`: Main script for user creation
2. `delete_user.py`: Script for user deletion
3. `user_registry.py`: Module for managing the local user registry
4. `create-user-template.yaml`: Template for Kubeflow profile creation

## Prerequisites

- Python 3.6+
- Access to a Kubeflow ready Kubernetes cluster with administrative privileges
- `kubectl` configured with appropriate permissions
- Required Python packages: `pyyaml`, `bcrypt`, `jinja2`

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/choudhryfrompak/kubeflow-user-creation-deletion-scripts.git
   cd kubeflow-user-creation-deletion-scripts
   ```

2. Install required Python packages:
   ```
   cd scripts
   pip install -r requirements.txt
   ```

## Usage

### Creating a New User

1. Run the user creation script:
   ```
   python3 create-user.py
   ```

2. Follow the prompts to enter user details:
   - Profile name
   - User email
   - Username
   - Password
   - CPU limit
   - Memory limit
   - GPU memory limit
   - GPU count
   - Storage limit

You can add more fields as permissibile by kubeflow ResourceQuota values.

3. The script will:
   - Create a Kubeflow profile for the user
   - Update the Dex configuration
   - Add the user to the local registry located at `users/user-registry.json`

### Deleting a User

1. Run the user deletion script:
   ```
   python3 delete_user.py <username>
   ```
   Replace `<username>` with the username of the user you want to delete.

2. The script will:
   - Delete the Kubeflow profile
   - Remove the associated namespace
   - Mark the user as deleted in the local registry.

## User Registry

The user registry is maintained in a JSON file (`user_registry.json`) in the `/users/user-registry.json`. It stores the following information for each user:

- Username
- Email
- CPU limit
- Memory limit
- GPU memory limit
- GPU count
- Storage limit
- Creation time
- Deletion time (after deletion)

## Customization

- Modify `create-user-template.yaml` to change the default profile configuration.
- Adjust resource quotas in `create-user.py` to set different limits for users.

## Troubleshooting

- Ensure you have the necessary permissions to create and delete Kubeflow profiles and namespaces.
- Check Kubeflow and Dex logs if users face authentication issues after creation.
- Verify that the `kubectl` context is set to the correct cluster.

## Security Considerations

- Store the scripts and user registry in a secure location with restricted access.
- Regularly review and audit the user registry.
- Consider implementing additional access controls and monitoring for the Kubeflow environment.

## Contributing

Contributions to improve the scripts or add new features are welcome. Please submit a pull request or open an issue to discuss proposed changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
