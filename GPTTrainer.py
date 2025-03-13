import os
os.environ["HF_DATASETS_NO_PROGRESS_BAR"] = "1"

import json
from datasets import load_dataset, concatenate_datasets
from transformers import (AutoTokenizer, AutoModelForCausalLM, DataCollatorForLanguageModeling, TrainingArguments, Trainer,)
from peft import get_peft_model, LoraConfig, TaskType



class DataPreparer:

    def __init__(self, json_dir, test_size=0.05, seed=42, max_length=512, use_lora=True):

        """
        Initialize the DataPreparer with dataset parameters and model tokenization settings.

        Parameters:
            json_dir (str): Directory path containing JSON files.
            test_size (float): Proportion of data to reserve for testing.
            seed (int): Seed for random operations.
            max_length (int): Maximum sequence length for tokenization.
            use_lora (bool): Whether to enable LoRA fine-tuning.
        """

        self.json_dir = json_dir
        self.test_size = test_size
        self.seed = seed
        self.max_length = max_length
        self.use_lora = use_lora
        
        self.train_dataset = None
        self.test_dataset = None
        self.train_dataset_tokenized = None
        self.test_dataset_tokenized = None
        
        # Load the GPT-2 tokenizer and add special tokens for padding and separation.
        self.tokenizer = AutoTokenizer.from_pretrained("./GPT-2", local_files_only=True)

        special_tokens = ["<PAD>", "<SEP>"]
        self.tokenizer.add_tokens(special_tokens)

        self.tokenizer.pad_token = "<PAD>"

     
        
    def load_json_files(self):

        """
        Iterates over JSON files in self.json_dir, loads each file as a dataset, extracts the document name,
        and groups data by 'Section'. Each section is split into training and test sets based on test_size.
        
        Returns:
            dict: A dictionary with keys 'train' and 'test' containing the corresponding datasets.
        """

        train_list = []
        test_list = []

        for file in os.listdir(self.json_dir):
            if file.lower().endswith(".json"):
                file_path = os.path.join(self.json_dir, file)
                print(f"loading {file_path}...")

                ds = load_dataset("json", data_files=file_path)["train"] # Load the JSON file as a dataset.

                file_name_full = os.path.basename(file_path)               # e.g., "Pracitcal Advice Note - Domestic Abuse.json"
                file_name_no_ext = file_name_full.replace(".json", "")       # "Pracitcal Advice Note - Domestic Abuse"
                if "-" in file_name_no_ext:
                    document_name = file_name_no_ext.split("-")[-1].strip()  # "Domestic Abuse"
                else:
                    document_name = file_name_no_ext

                ds = ds.map(lambda x: {"Document": document_name}) # Add the document name to each record.

                if "Section" not in ds.column_names:
                    raise ValueError(f"'Section' key not found in {file_path}")

                # Group data by Section
                unique_sections = set(ds["Section"])
                file_train_groups = []
                file_test_groups = []


                for section in unique_sections:
                    ds_section = ds.filter(lambda x: x["Section"] == section)
                    if len(ds_section) < 2:
                        file_train_groups.append(ds_section)

                    else:
                        split_ds = ds_section.train_test_split(test_size=self.test_size, seed=self.seed)
                        file_train_groups.append(split_ds["train"])
                        file_test_groups.append(split_ds["test"])

                file_train = concatenate_datasets(file_train_groups)
                file_test = concatenate_datasets(file_test_groups)
                train_list.append(file_train)
                test_list.append(file_test)
                

        if not train_list:
            raise ValueError("No JSON file found in the specified directory")

        self.train_dataset = concatenate_datasets(train_list)
        self.test_dataset = concatenate_datasets(test_list)

        #Optional: Save the datasets for review.
        #self.train_dataset.to_json("train_dataset_review.json", orient="records", lines=True)
        #self.test_dataset.to_json("test_dataset_review.json", orient="records", lines=True)

        return {"train": self.train_dataset, "test": self.test_dataset}


    def tokenize_data(self):

        """
        Tokenize the training and test datasets.

        Combines the 'Document', 'Section', 'Subsection', and 'Content' fields into a single string for each example,
        then tokenizes the text with truncation to self.max_length.

        Returns:
            dict: A dictionary with tokenized 'train' and 'test' datasets formatted as PyTorch tensors.
        """

        def tokenize_function(example):
            combined_text = []
            # Combine fields for each example.
            for sec, subsec, content, doc in zip(example["Section"], example["Subsection"], example["Content"], example["Document"]):

                sec = sec if sec is not None else ""
                subsec = subsec if subsec is not None else ""
                content = content if content is not None else ""
                doc = doc if doc is not None else ""
                combined_text.append(doc + " " + sec + " " + subsec + " " + content)
                
            return self.tokenizer(combined_text, truncation=True, max_length= self.max_length)

        #Apply tokenization on training and testing datasets using multiprocessing.
        self.train_dataset_tokenized = self.train_dataset.map(tokenize_function, batched=True, num_proc=4)
        self.test_dataset_tokenized = self.test_dataset.map(tokenize_function, batched=True, num_proc=4)

        # Format the datasets to return PyTorch tensors.
        self.train_dataset_tokenized.set_format(type="torch", columns=["input_ids", "attention_mask"])
        self.test_dataset_tokenized.set_format(type="torch", columns=["input_ids", "attention_mask"])

        return {"train": self.train_dataset_tokenized, "test": self.test_dataset_tokenized}
    

    def load_model(self):

        """
        Load the GPT-2 base model and apply a LoRA adapter if enabled.

        The method loads the base model from a local directory, adjusts the token embeddings to match the tokenizer,
        and, if self.use_lora is True, configures and applies a LoRA adapter for parameter-efficient fine-tuning.

        Returns:
            model: The loaded and optionally adapted language model.
        """

        self.model = AutoModelForCausalLM.from_pretrained("./GPT-2", local_files_only=True)
        self.model.resize_token_embeddings(len(self.tokenizer))
        print("model loaded successfully")


        if self.use_lora:
            # Configure LoRA settings.
            lora_config = LoraConfig(
                task_type= TaskType.CAUSAL_LM,
                inference_mode=False,
                r=8,
                lora_alpha=32,
                lora_dropout=0.1
            )
            # Apply LoRA adapter to the model.
            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()
        else:
            print("loRA not used")
                       
        return self.model
    

    def train_model(self, output_dir="./GPTtrained", num_train_epochs=3, batch_size = 4):

        """
        Configures training arguments and data collator for language modeling, initializes a Trainer, and trains the model.
        After training, the model and tokenizer are saved to the specified output directory.

        Parameters:
            output_dir (str): Directory to save the trained model and tokenizer.
            num_train_epochs (int): Number of training epochs.
            batch_size (int): Training batch size.
        """


        data_collator = DataCollatorForLanguageModeling(tokenizer=self.tokenizer, mlm=False)

        training_args = TrainingArguments(
            output_dir=output_dir,
            evaluation_strategy="epoch",
            save_strategy="steps", 
            learning_rate=5e-5,
            weight_decay=0.01,
            per_device_train_batch_size = batch_size,
            per_device_eval_batch_size = batch_size,
            num_train_epochs=num_train_epochs,
            gradient_accumulation_steps=8,
            logging_steps=50,
            save_steps=100,
            save_total_limit=3,
            fp16=True,
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset_tokenized,
            eval_dataset=self.test_dataset_tokenized,
            data_collator=data_collator,
        )

        print("Starting training...")
        trainer.train()
        print("Training complete.")
            
        trainer.save_model(f"{output_dir}/final_model")
        self.tokenizer.save_pretrained(f"{output_dir}/final_model")
        print("Model and tokenizer saved successfully.")

        
if __name__ == "__main__":

    json_directory = r"C:\Users\User\OneDrive\Documents\UNI work\SCC\year 4\placement\legal resources\json_files"
    loader = DataPreparer(json_dir=json_directory, test_size=0.03, seed=42)
    
    splits = loader.load_json_files()
    tokenized_splits = loader.tokenize_data()

    loader.load_model()
    loader.train_model(output_dir="./GPTtrained", num_train_epochs=3, batch_size=4) 
