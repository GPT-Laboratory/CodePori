import json
import requests
import time
# Initialize OpenAI API
openai_api_key = 'Here paste your openAI API key' # change this when using gpt-4
model= "gpt-4" # change this to gpt-4 when using gpt-4


def get_module_descriptions(project_description):
    # Prepare the prompt for the manager bot
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
            'Authorization': 'Bearer ' + openai_api_key,
            'Content-Type': 'application/json',
        }
    conversation_history = []
    manager_prompt = open('manager_bot.txt', 'r').read().replace("PROJECT_DESCRIPTION", project_description)
    conversation_history.append({ "role": "system", "content" : manager_prompt}),
    # Call the OpenAI API with the manager bot prompt
    payload = {
            'model': model,     
            'messages': conversation_history,
        }

    # Extract and return the module descriptions from the response
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()["choices"][0]["message"]["content"]
    module_descriptions = json.loads(response)

    return module_descriptions

def get_pair_programmers_code(module_description, accumulated_code, project_description):
    # Prepare the prompt for the pair programmers
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer ' + openai_api_key,
        'Content-Type': 'application/json',
    }

    # Initialize conversation histories for dev_1 and dev_2
    dev_1_conversation_history = []
    dev_2_conversation_history = []

    # Update and set the initial system message for dev_1
    dev_1_prompt = open('dev_1.txt', 'r').read()
    dev_1_prompt = dev_1_prompt.replace("MODULE_DESCRIPTION", module_description)
    dev_1_prompt = dev_1_prompt.replace("ACCUMULATED_CODE", accumulated_code)
    dev_1_prompt = dev_1_prompt.replace("PROJECT_DESCRIPTION", project_description)
    dev_1_conversation_history.append({"role": "system", "content": dev_1_prompt})

    # Update and set the initial system message for dev_2
    dev_2_prompt = open('dev_2.txt', 'r').read()
    dev_2_prompt = dev_2_prompt.replace("MODULE_DESCRIPTION", module_description)
    dev_2_prompt = dev_2_prompt.replace("ACCUMULATED_CODE", accumulated_code)
    dev_2_prompt = dev_2_prompt.replace("PROJECT_DESCRIPTION", project_description)
    dev_2_conversation_history.append({"role": "system", "content": dev_2_prompt})  # Moved outside the loop

    # Conduct 3 rounds of interaction between dev_1 and dev_2
    for round_num in range(3):
        # Dev_1 to Dev_2 interaction
        payload = {
            'model': model,
            'messages': dev_1_conversation_history,
        }
        for max_tries in range(5):
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()
                break
            except: print("Request timed out, trying again...")
            
        dev_1_response = response["choices"][0]["message"]["content"]
        dev_1_conversation_history.append({"role": "assistant", "content": dev_1_response})
        dev_2_conversation_history.append({"role": "user", "content": dev_1_response})

        # Dev_2 to Dev_1 interaction
        payload = {
            'model': model,
            'messages': dev_2_conversation_history,
        }
        for max_tries in range(5):
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()
                break
            except: print("Request timed out, trying again...")

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()
        dev_2_response = response["choices"][0]["message"]["content"]
        dev_2_conversation_history.append({"role": "assistant", "content": dev_2_response})
        dev_1_conversation_history.append({"role": "user", "content": dev_2_response})

    for dev_2_response, dev_1_response in zip(dev_2_conversation_history[::-1], dev_1_conversation_history[::-1]):
        if "```python" in dev_2_response["content"]:
            final_code = dev_2_response["content"]
            break
        elif "```python" in dev_1_response["content"]:
            final_code = dev_1_response["content"]
            break

    return final_code


def get_verification_review(accumulated_code, project_description, module_code, module_name):
    # Prepare the prompt for the verification bot
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer ' + openai_api_key,
        'Content-Type': 'application/json',
    }
    
    verification_prompt = open('verfication_bot.txt', 'r').read()
    verification_prompt = verification_prompt.replace("ACCUMULATED_CODE", accumulated_code)
    verification_prompt = verification_prompt.replace("PROJECT_DESCRIPTION", project_description)
    verification_prompt = verification_prompt.replace("MODULE_CODE", module_code)
    verification_prompt = verification_prompt.replace("MODULE_NAME", module_name)
    
    conversation_history = [{"role": "system", "content": verification_prompt}]
    
    # Call the OpenAI API with the verification bot prompt
    payload = {
        'model': model,
        'messages': conversation_history,
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=200).json()
    
    # Extract and return the review from the response
    review = response["choices"][0]["message"]["content"]
    
    return review

def finalize_code(project_description, accumalated_code, review):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer ' + openai_api_key,
        'Content-Type': 'application/json',
    }

    dev_1_conversation_history = []
    dev_2_conversation_history = []

    bot_1_prompt = open('finalizer_bot_1.txt', 'r').read()
    bot_1_prompt = bot_1_prompt.replace("ACCUMULATED_CODE", accumalated_code)
    bot_1_prompt = bot_1_prompt.replace("PROJECT_DESCRIPTION", project_description)
    bot_1_prompt = bot_1_prompt.replace("REVIEW", review)
    dev_1_conversation_history.append({"role": "system", "content": bot_1_prompt})

    bot_2_prompt = open('finalizer_bot_2.txt', 'r').read()
    bot_2_prompt = bot_2_prompt.replace("ACCUMULATED_CODE", accumalated_code)
    bot_2_prompt = bot_2_prompt.replace("PROJECT_DESCRIPTION", project_description)
    bot_2_prompt = bot_2_prompt.replace("REVIEW", review)
    dev_2_conversation_history.append({"role": "system", "content": bot_2_prompt})

    for round_num in range(2):
        # Dev_1 to Dev_2 interaction
        payload = {
            'model': model,
            'messages': dev_1_conversation_history,
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()
        dev_1_response = response["choices"][0]["message"]["content"]
        dev_1_conversation_history.append({"role": "assistant", "content": dev_1_response})
        dev_2_conversation_history.append({"role": "user", "content": dev_1_response})

        # Dev_2 to Dev_1 interaction
        payload = {
            'model': model,
            'messages': dev_2_conversation_history,
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=500).json()
        dev_2_response = response["choices"][0]["message"]["content"]
        dev_2_conversation_history.append({"role": "assistant", "content": dev_2_response})
        dev_1_conversation_history.append({"role": "user", "content": dev_2_response})

    # Extract the final code from the last response
    for dev_2_response, dev_1_response in zip(dev_2_conversation_history[::-1], dev_1_conversation_history[::-1]):
        if "```python" in dev_2_response["content"]:
            final_code = dev_2_response["content"]
            break
        elif "```python" in dev_1_response["content"]:
            final_code = dev_1_response["content"]
            break

    return final_code


project_description = open('project_description.txt', 'r').read()

module_descriptions = get_module_descriptions(project_description)
print(module_descriptions)


accumulated_code = ""
for module, module_description in module_descriptions.items():
    i = int(module.split("_")[1])
    print(f"Working on Module {module_description['name']}...")
    
    module_code = get_pair_programmers_code(json.dumps(module_description), accumulated_code, project_description)
    module_code = module_code.split("```")[1].split("```")[0]
    print(f"Module code for {module_description['name']}:\n{module_code}\n")
    # this following code should be un-commented if the code being generated by gpt-3.5 is not good enough
    # review = get_verification_review(accumulated_code, project_description, module_code, module_description["name"])
    # print(f"Review for {module_description['name']}:\n{review}\n")
    # module_code = finalize_code(project_description, accumulated_code, review)
    # print(f"Final code for {module_description['name']}:\n{final_code}\n")
    accumulated_code += f"\n# {module_description['name']} Code:\n" + module_code
    with open(f'{module_description["name"]}.py', 'w') as file:     
        file.write(module_code)
    print(f"Module {i} code saved to file.\n")

print("Project code finalized and saved to file.")
print("Project finished at time: ", time.strftime("%H:%M:%S", time.localtime()) )