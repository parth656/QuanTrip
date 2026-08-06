import requests


BASE_URL = "http://127.0.0.1:8000/chatbot"

session_id = ""

print("QuanTrip AI Terminal Chatbot")
print("Type 'exit' to stop.")
print("Type 'reset' to start a new trip.\n")

while True:
    try:
        user_message = input("You: ")
    except KeyboardInterrupt:
        print("\nBot:")
        print("Goodbye!")
        break

    if user_message.lower() in [
        "exit",
        "quit",
        "bye"
    ]:
        print("\nBot:")
        print("Goodbye!")
        break

    payload = {
        "session_id": session_id,
        "message": user_message
    }

    try:
        response = requests.post(BASE_URL, json=payload)

        if response.status_code != 200:
            print("\nBot:")
            print("Error:", response.text)
            print()
            continue

        data = response.json()

        session_id = data.get("session_id", session_id)

        print("\nBot:")
        print(data.get("reply"))
        print()

    except Exception as e:
        print("\nBot:")
        print("Something went wrong:", str(e))
        print()