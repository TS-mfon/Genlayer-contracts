# { "Depends": "py-genlayer:test" }

from genlayer import *

class FriendlyGuestbook(gl.Contract):
    # GenLayer requires defining storage types at the class level.
    # We use simple strings here to avoid complex Array syntax errors.
    latest_message: str
    latest_sender: str

    def __init__(self):
        # Initialize with safe default values
        # We DO NOT use gl.msg.sender here to avoid deployment crashes
        self.latest_message = "Welcome to GenLayer!"
        self.latest_sender = "System"
        print("Friendly Guestbook Deployed!")

    @gl.public.write
    def sign_guestbook(self, message: str):
        """
        Signs the guestbook with a message if it passes the AI check.
        """
        
        # 1. Define the AI Task
        # This function runs inside the non-deterministic engine
        def check_vibes() -> str:
            task_prompt = f"""
            You are a content moderation AI. Analyze the following user message.

            User Message: "{message}"

            Instructions:
            - If the message is offensive, rude, or spam, reply strictly with "YES".
            - If the message is acceptable/polite, reply strictly with "NO".
            - Output ONLY the word "YES" or "NO". No punctuation.
            """
            # Execute the prompt using the GenLayer non-deterministic API
            result = gl.nondet.exec_prompt(task_prompt)
            return result.strip().upper()

        # 2. Enforce Consensus
        # All validators must run check_vibes and agree on the result
        consensus_result = gl.eq_principle.strict_eq(check_vibes)
        print(f"AI Consensus Result: {consensus_result}")

        # 3. The Gate Logic
        if consensus_result == "YES":
            raise Exception("Vibe Check Failed: Your message was rejected.")

        # 4. State Update
        # We convert the sender address to a string for safe storage
        self.latest_message = message
        self.latest_sender = str(gl.message.sender_address)

        # NOTE: No return statement here! Write functions must be void.

    @gl.public.view
    def get_latest_entry(self) -> dict[str, str]:
        return {
            "sender": self.latest_sender,
            "message": self.latest_message
        }
