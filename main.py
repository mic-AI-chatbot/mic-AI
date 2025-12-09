import sys
import os
from mic.core import process_input
from mic.database import init_db # Import init_db
from mic.auth import register_user, verify_user, get_user_tier, update_user_tier # Import auth functions

# Set the HF_HOME environment variable before any transformers imports
os.environ["HF_HOME"] = "E:\\mic\\LLM"

# Create the directory if it doesn't exist
os.makedirs(os.environ["HF_HOME"], exist_ok=True)

# Initialize the database
init_db()

def main():
    history = []
    current_user = None # Track logged-in user

    print("Welcome to mic - your Multi-modal Intelligent Companion!")
    print("Type 'register <username> <password>' to create an account.")
    print("Type 'login <username> <password>' to log in.")
    print("Type 'upgrade <tier>' to change your subscription.")
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            
            # Handle registration
            if user_input.lower().startswith("register "):
                parts = user_input.split(" ")
                if len(parts) == 3:
                    username = parts[1]
                    password = parts[2]
                    if register_user(username, password):
                        print(f"mic: User '{username}' registered successfully.")
                    else:
                        print(f"mic: Registration failed. Username '{username}' might already exist.")
                else:
                    print("mic: Usage: register <username> <password>")
                continue # Skip to next input

            # Handle login
            if user_input.lower().startswith("login "):
                parts = user_input.split(" ")
                if len(parts) == 3:
                    username = parts[1]
                    password = parts[2]
                    if verify_user(username, password):
                        current_user = username
                        print(f"mic: User '{username}' logged in successfully. Your current tier is {get_user_tier(username)}.")
                    else:
                        print("mic: Login failed. Invalid username or password.")
                else:
                    print("mic: Usage: login <username> <password>")
                continue # Skip to next input

            # Handle upgrade
            if user_input.lower().startswith("upgrade "):
                if not current_user:
                    print("mic: Please log in to upgrade your subscription.")
                    continue
                parts = user_input.split(" ")
                if len(parts) == 2:
                    new_tier = parts[1]
                    # Simulate payment
                    payment_successful = True # Always successful for simulation
                    if payment_successful:
                        if update_user_tier(current_user, new_tier):
                            print(f"mic: Successfully upgraded to {new_tier} tier!")
                        else:
                            print("mic: Failed to upgrade tier.")
                    else:
                        print("mic: Simulated payment failed.")
                else:
                    print("mic: Usage: upgrade <tier> (e.g., upgrade Premium)")
                continue # Skip to next input

            if not current_user:
                print("mic: Please register or log in to use mic's features.")
                continue # Skip to next input

            history.append({"role": "user", "content": user_input})
            response = process_input(history, current_user=current_user) # Pass current_user
            history.append({"role": "assistant", "content": response})
            print(f"mic: {response}")
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nExiting mic.")
            break

if __name__ == "__main__":
    main()