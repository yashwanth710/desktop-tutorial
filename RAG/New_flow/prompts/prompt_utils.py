import yaml

def load_prompt(prompt_name:str) -> str:
    try:
        file_path = "prompts/prompts.yaml"
        with open(file_path, "r") as file:
            prompts = yaml.safe_load(file)

        prompt = prompts.get(prompt_name)
        if prompt is None:
            raise KeyError(f"Prompt '{prompt_name}' not found.")
        return prompt
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file {file_path} not found.")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML file: {e}")

def format_prompt(prompt_name: str, **kwargs) -> str:
    """
    Load a prompt template by name and format it with provided keyword arguments.
    """
    prompt_template = load_prompt(prompt_name)
    try:
        return prompt_template.format(**kwargs)
    except KeyError as e:
        missing_key = e.args[0]
        raise KeyError(f"Missing placeholder '{missing_key}' in formatting arguments for prompt '{prompt_name}'.")
    