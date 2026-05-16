from openrouter import OpenRouter
import os
from tools import tools, TOOL_MAPPING
import json

message_list = []
MODEL = "openai/gpt-oss-120b"

def chat():
    while True:
        user_input = input("User:")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break
        message_list.append({"role": "user", "content": user_input})

        with OpenRouter(
            api_key=os.getenv("OPENROUTER_API_KEY")
        ) as client:
            
            response = client.chat.send(
                model=MODEL,
                tools=tools,
                messages=message_list
            )

            while response.choices[0].finish_reason == "tool_calls":
                message_list.append({"role": "assistant",
                                    "content": response.choices[0].message.content,
                                    "tool_calls": response.choices[0].message.tool_calls})
                
                tool_calls = response.choices[0].message.tool_calls
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_response = TOOL_MAPPING[tool_name](**tool_args)
                    message_list.append(
                        {"role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_response)
                        }
                    )
                    response = client.chat.send(
                        model=MODEL,
                        tools=tools,
                        messages=message_list
                    )
               
            print("Assistant:", response.choices[0].message.content)    


    return  "Session ended"





