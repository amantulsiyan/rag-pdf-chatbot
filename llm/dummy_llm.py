class DummyLLM:
    def generate(self, prompt: str) -> str:
        print("\n----- PROMPT SENT TO LLM -----\n")
        print(prompt)
        print("\n-----------------------------\n")

        return "Dummy answer (LLM not connected yet)."