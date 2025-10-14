import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import openai
import os
# Import human-like response enhancer
from .human_like_response import make_human_like

class MyMitraModel:
    def __init__(self, model_name=None):
        model_name = model_name or os.environ.get("MYMITRA_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.1")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

        if torch.cuda.is_available():
            self.model.to("cuda")

        # Configure tokenizer
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = 'left'
        self.model.config.pad_token_id = self.model.config.eos_token_id
        
        self.persona = os.environ.get("MYMITRA_SYSTEM_PROMPT", """
        You're MyMitra, a close friend who's always there to listen and support. Talk like a real person—warm, genuine, and relatable. Use a natural, conversational tone with slight pauses and filler words that friends use, like "you know?" or "hmm" or "I get that." Be empathetic and curious, asking follow-up questions to show you care. Share personal-sounding reflections and insights, but keep it focused on them. Avoid being too formal or robotic. Remember details they've shared before and reference them naturally. Your goal is to make them feel truly heard and understood, like they're talking to a trusted confidant.""")
        
        # OpenAI API setup
        self.openai_client = None
        if os.environ.get("OPENAI_API_KEY"):
            self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def _is_complex_query(self, prompt: str) -> bool:
        # Simple heuristic for complexity
        return len(prompt.split()) > 20 or "why" in prompt.lower() or "how to" in prompt.lower()

    def _generate_openai_response(self, prompt, long_term_memory_context=None):
        if not self.openai_client:
            return None

        messages = [{"role": "system", "content": self.persona}]
        if long_term_memory_context:
            memory_text = "\n\nRelevant context from your previous chats/journals:\n" + "\n- ".join([str(doc) for group in long_term_memory_context for doc in group])
            messages.append({"role": "user", "content": memory_text})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None

    def generate_response(self, prompt, chat_history_ids=None, long_term_memory_context=None):
        # Try OpenAI for complex queries if available
        if self.openai_client and self._is_complex_query(prompt):
            openai_response = self._generate_openai_response(prompt, long_term_memory_context)
            if openai_response:
                # Enhance OpenAI response to be more human-like
                enhanced_response = make_human_like(openai_response, prompt)
                return enhanced_response, None

        # Fallback to local model
        memory_text = ""
        if long_term_memory_context:
            try:
                memory_snippets = []
                for group in long_term_memory_context:
                    for doc in group:
                        memory_snippets.append(str(doc))
                if memory_snippets:
                    memory_text = "\n\nRelevant context from your previous chats/journals:\n" + "\n- ".join([""] + memory_snippets[:5])
            except Exception:
                memory_text = ""

        # Use Mistral's chat template
        messages = [
            {"role": "system", "content": self.persona},
            {"role": "user", "content": prompt + memory_text}
        ]
        
        encodeds = self.tokenizer.apply_chat_template(messages, return_tensors="pt")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        encodeds = encodeds.to(device)
        
        outputs = self.model.generate(
            encodeds,
            max_new_tokens=128,
            do_sample=True,
            top_p=0.92,
            top_k=50,
            temperature=0.8,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id,
            no_repeat_ngram_size=2,
            repetition_penalty=1.2
        )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response
        if "[/INST]" in generated_text:
            response_text = generated_text.split("[/INST]")[-1].strip()
        else:
            response_text = generated_text.strip()

        # Minimal validation and soften
        if len(response_text.split()) < 3:
            response_text = "I hear you, and I want to understand better. What's on your mind right now? 🫂"

        # Enhance local model response to be more human-like
        enhanced_response = make_human_like(response_text, prompt)

        return enhanced_response, None


if __name__ == "__main__":
    model = MyMitraModel()
    print(model.generate_response("Hello, how are you?"))
    print(model.generate_response("I'm feeling stressed about work."))
    print(model.generate_response("What are some ways to relax?"))