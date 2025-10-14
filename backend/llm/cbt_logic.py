class CBTLogic:
    def __init__(self, model):
        self.model = model
        self.stages = ["awareness", "reflection", "reframing", "action"]
        self.current_stage_index = 0

    def get_current_stage(self):
        return self.stages[self.current_stage_index]

    def advance_stage(self):
        if self.current_stage_index < len(self.stages) - 1:
            self.current_stage_index += 1
        else:
            self.current_stage_index = 0 # Loop back to awareness or handle completion

    def process_cbt(self, user_input, conversation_history):
        current_stage = self.get_current_stage()

        if current_stage == "awareness":
            response = self._handle_awareness(user_input, conversation_history)
        elif current_stage == "reflection":
            response = self._handle_reflection(user_input, conversation_history)
        elif current_stage == "reframing":
            response = self._handle_reframing(user_input, conversation_history)
        elif current_stage == "action":
            response = self._handle_action(user_input, conversation_history)
        else:
            response = "I'm not sure how to process that within the CBT framework right now."

        self.advance_stage()
        return response

    def _handle_awareness(self, user_input, conversation_history):
        prompt = f"The user shared: '{user_input}'. As a warm and supportive friend, gently help them explore their feelings with a kind and understanding question. Avoid clinical terms and use comforting emojis when appropriate. Focus on making them feel truly heard and valued."
        response, _ = self.model.generate_response(prompt)
        return response

    def _handle_reflection(self, user_input, conversation_history):
        prompt = f"The user shared: '{user_input}'. Like a caring and empathetic friend, help them gently dig a little deeper into what's going on. Keep it casual, supportive, and soothing, maybe use a gentle emoji to show you're there for them. Ask a thoughtful question that helps them understand their feelings better."
        response, _ = self.model.generate_response(prompt)
        return response

    def _handle_reframing(self, user_input, conversation_history):
        prompt = f"The user shared: '{user_input}'. As their kind and supportive friend, gently suggest another way to look at things. Keep it real, relatable, and encouraging, maybe add a hopeful emoji. Help them see a different perspective without dismissing or minimizing their feelings."
        response, _ = self.model.generate_response(prompt)
        return response

    def _handle_action(self, user_input, conversation_history):
        prompt = f"The user shared: '{user_input}'. Like a helpful and caring friend, suggest one small, doable step they could try. Keep it super simple, encouraging, and reassuring, maybe with a supportive emoji. Focus on what feels manageable and comforting right now."
        response, _ = self.model.generate_response(prompt)
        return response

if __name__ == "__main__":
    cbt = CBTLogic()
    history = []

    print("MyMitra CBT Session (Type 'quit' to exit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break

        response = cbt.process_cbt(user_input, history)
        history.append(f"You: {user_input}")
        history.append(f"MyMitra: {response}")
        print(f"MyMitra ({cbt.get_current_stage()}): {response}")