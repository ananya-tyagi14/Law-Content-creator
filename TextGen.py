from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
import torch
from peft import get_peft_model, LoraConfig, TaskType, PeftModel  # If using LoRA
import json
import re
import difflib


class TextGenerator:

    def __init__(self, model_dir = "./GPTtrained/final_model", base_model_dir="./GPT-2"):

        """
        Loads the tokenizer from the fine-tuned model, ensuring it contains a PAD token, then loads the base model
        and resizes its token embeddings to match the tokenizer. Finally, it loads the PEFT adapter onto the base model.

        Parameters:
            model_dir (str): Directory containing the fine-tuned model and adapter.
            base_model_dir (str): Directory containing the base language model (e.g., GPT-2).
        """

        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)

        # Ensure the tokenizer has a PAD token; if not, add it.
        if self.tokenizer.pad_token is None or self.tokenizer.pad_token != "<PAD>":
            self.tokenizer.add_special_tokens({"pad_token": "<PAD>"})
            self.tokenizer.pad_token_id = self.tokenizer.convert_tokens_to_ids("<PAD>")
            
        # Load the base model. This should be the same model you started with.
        self.base_model = AutoModelForCausalLM.from_pretrained(base_model_dir, local_files_only=True)
        self.base_model.resize_token_embeddings(len(self.tokenizer))
        
        # Load the PEFT adapter onto the base model.
        self.model = PeftModel.from_pretrained(self.base_model, model_dir)

        self.legal_data = None


    def load_few_shot_examples(self, example_file):

        """
        Load few-shot examples from a text file.

        Few-shot examples are expected to be separated by two newlines.

        Parameters:
            example_file (str): Path to the text file containing few-shot examples.

        Returns:
            list: A list of few-shot example strings.
        """

        with open(example_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        examples = content.split("\n\n")
        return examples
    

    def find_closest_example(self, user_prompt, examples):

        """
        The method extracts the first sentence of the user prompt and compares it with the question part
        (after "Question:") in each example using a similarity ratio. The example with the highest similarity is returned.

        Parameters:
            user_prompt (str): The prompt provided by the user.
            examples (list): List of few-shot examples.

        Returns:
            str or None: The closest matching example, or None if no match is found.
        """

        
        # Extract the first sentence (everything up to the first period)
        first_sentence = user_prompt.split(".")[0].strip()
        best_example = None
        best_ratio = 0
        for ex in examples:
            # Look for the "Question:" line in each example.
            for line in ex.split("\n"):
                if line.startswith("Question:"):
                    question_line = line[len("Question:"):].strip()
                    # Compare only the first sentence of the user prompt with the example question.
                    ratio = difflib.SequenceMatcher(None, first_sentence.lower(), question_line.lower()).ratio()

                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_example = ex
                    break  # Only consider the first question line in each example
        return best_example
    
    
     
    def few_shot_files(self, category):

        """
        Return the file path for few-shot examples based on the provided category.

        Parameters:
            category (str): The category of the prompt (e.g., "introduction" or "definition").

        Returns:
            str or None: File path for the corresponding few-shot examples, or None if the category is unrecognized.
        """

        if category:
            if category.lower() == "introduction":
                return "./prompt resources/Intro-prompts.txt"
            elif category.lower() == "definition":
                return"./prompt resources/definition-prompts.txt"       
            else:
                return

                
    def generate_text(self, prompt, max_length=600, num_beams=5, length_penalty=2.0, no_repeat_ngram_size=3):

        """
        Generate text from the model based on the provided prompt using beam search.

        Parameters:
            prompt (str): The input prompt for text generation.
            max_length (int): Maximum length of the generated text.
            num_beams (int): Number of beams for beam search.
            length_penalty (float): Penalty to encourage longer outputs.
            no_repeat_ngram_size (int): Prevents repetition of n-grams of this size.

        Returns:
            str: The generated text.
        """

        #Tokenize the input prompt and convert it to tensors.
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
        input_ids = inputs.input_ids
        attention_mask = inputs.attention_mask
                                 
        output_ids = self.model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_length = max_length,
            num_beams=num_beams,
            length_penalty=length_penalty,     # Encourages longer outputs
            no_repeat_ngram_size=no_repeat_ngram_size,
            early_stopping=True,  
            do_sample = False,
            pad_token_id = self.tokenizer.pad_token_id
        )
        
        #Decode the generated tokens to a human-readable string.
        generate_txt = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return generate_txt

    
if __name__ == "__main__":

    generator = TextGenerator(model_dir="./GPTtrained/final_model") #create class instance

    #base prompt
    prompt = ("Draft a well structured introduction about employment discrimination. "
              "Ensure all facts are strictly based on UK law."
              "Do not include any external citations or source references in your answer. "
              "Do not include any generic contact or advisory information. "
              "Avoid phrases like 'In this article' or 'in this paper'.")

    #find the category that the prompt falls under
    lower_prompt = prompt.lower()
    if "introduction" in lower_prompt:
        category =  "Introduction"
    elif "definition" in lower_prompt:
        category =  "Definition"
    else:
        category = None

    #Retrieve the file path for the appropriate few-shot examples.
    examples_file = generator.few_shot_files(category)
    
    #Load few-shot examples from the specified file.
    examples = generator.load_few_shot_examples(examples_file)

    matching_example = generator.find_closest_example(prompt, examples)
    
    #Construct the few-shot prompt by appending the user's question to the matching example.
    if matching_example:
        few_shot_prompt = matching_example + "\n\nUser Question: " + prompt + "\nAnswer:"
    else:
        few_shot_prompt = "User Question: " + prompt + "\nAnswer:"

    generated_text = generator.generate_text(few_shot_prompt, max_length=400)
    print(generated_text)
    print("\n")
 
