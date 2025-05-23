TITLE: Authenticate OpenRouter API with OpenAI SDK (Python)
DESCRIPTION: This Python snippet demonstrates how to use the OpenAI Python library to make requests to the OpenRouter API. It requires setting the `openai.api_base` to the OpenRouter endpoint and assigning your API key to `openai.api_key`. Optional headers can be passed directly to the `ChatCompletion.create` method.
SOURCE: https://openrouter.ai/docs/api-reference/authentication.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import openai

openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = "<OPENROUTER_API_KEY>"

response = openai.ChatCompletion.create(
  model="openai/gpt-4o",
  messages=[...],
  headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
)

reply = response.choices[0].message
```

----------------------------------------

TITLE: Initializing and Running LangChain ChatOpenAI with OpenRouter (Python)
DESCRIPTION: Shows a complete Python example using LangChain to interact with OpenRouter. It demonstrates loading environment variables, setting up a prompt template, initializing `ChatOpenAI` with OpenRouter base URL and headers, creating an `LLMChain`, and running a query.
SOURCE: https://openrouter.ai/docs/community/frameworks.mdx#_snippet_3

LANGUAGE: Python
CODE:
```
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from os import getenv
from dotenv import load_dotenv

load_dotenv()

template = """Question: {question}
Answer: Let's think step by step."""

prompt = PromptTemplate(template=template, input_variables=["question"])

llm = ChatOpenAI(
  openai_api_key=getenv("OPENROUTER_API_KEY"),
  openai_api_base=getenv("OPENROUTER_BASE_URL"),
  model_name="<model_name>",
  model_kwargs={
    "headers": {
      "HTTP-Referer": getenv("YOUR_SITE_URL"),
      "X-Title": getenv("YOUR_SITE_NAME"),
    }
  },
)

llm_chain = LLMChain(prompt=prompt, llm=llm)

question = "What NFL team won the Super Bowl in the year Justin Beiber was born?"

print(llm_chain.run(question))
```

----------------------------------------

TITLE: Streaming Text and Using Tools with Vercel AI SDK and OpenRouter (TypeScript)
DESCRIPTION: Shows how to use the `@openrouter/ai-sdk-provider` with the Vercel AI SDK `streamText` function. It includes examples for streaming a recipe and using a tool (`getCurrentWeather`) with schema validation (`zod`) to handle function calls.
SOURCE: https://openrouter.ai/docs/community/frameworks.mdx#_snippet_7

LANGUAGE: typescript
CODE:
```
import { createOpenRouter } from '@openrouter/ai-sdk-provider';
import { streamText } from 'ai';
import { z } from 'zod';

export const getLasagnaRecipe = async (modelName: string) => {
  const openrouter = createOpenRouter({
    apiKey: '${API_KEY_REF}',
  });

  const response = streamText({
    model: openrouter(modelName),
    prompt: 'Write a vegetarian lasagna recipe for 4 people.',
  });

  await response.consumeStream();
  return response.text;
};

export const getWeather = async (modelName: string) => {
  const openrouter = createOpenRouter({
    apiKey: '${API_KEY_REF}',
  });

  const response = streamText({
    model: openrouter(modelName),
    prompt: 'What is the weather in San Francisco, CA in Fahrenheit?',
    tools: {
      getCurrentWeather: {
        description: 'Get the current weather in a given location',
        parameters: z.object({
          location: z
            .string()
            .describe('The city and state, e.g. San Francisco, CA'),
          unit: z.enum(['celsius', 'fahrenheit']).optional(),
        }),
        execute: async ({ location, unit = 'celsius' }) => {
          // Mock response for the weather
          const weatherData = {
            'Boston, MA': {
              celsius: '15°C',
              fahrenheit: '59°F',
            },
            'San Francisco, CA': {
              celsius: '18°C',
              fahrenheit: '64°F',
            },
          };

          const weather = weatherData[location];
          if (!weather) {
            return `Weather data for ${location} is not available.`;
          }

          return `The current weather in ${location} is ${weather[unit]}.`;
        },
      },
    },
  });

  await response.consumeStream();
  return response.text;
};
```

----------------------------------------

TITLE: Sending Chat Completion Request with Python Requests
DESCRIPTION: Shows how to make a POST request to the OpenRouter chat completions API using the Python `requests` library, setting the necessary headers and sending the request payload as JSON.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/chat/completions"

payload = { "model": "openai/gpt-3.5-turbo" }
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Sending Chat Completion Request with JavaScript Fetch
DESCRIPTION: Illustrates how to use the JavaScript `fetch` API to send a POST request to the OpenRouter chat completions endpoint, configuring headers and the JSON request body, and handling the response asynchronously.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/chat/completions';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"model":"openai/gpt-3.5-turbo"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Calling OpenRouter API directly
DESCRIPTION: Demonstrates how to interact with the OpenRouter API by making direct HTTP requests to the chat completions endpoint. It shows how to include the API key in the Authorization header and add optional headers for site ranking. Examples are provided using Python (requests), TypeScript (fetch), and Shell (curl).
SOURCE: https://openrouter.ai/docs/quickstart.mdx#_snippet_1

LANGUAGE: python
CODE:
```
import requests
import json

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer <OPENROUTER_API_KEY>",
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  data=json.dumps({
    "model": "openai/gpt-4o", # Optional
    "messages": [
      {
        "role": "user",
        "content": "What is the meaning of life?"
      }
    ]
  })
)
```

LANGUAGE: typescript
CODE:
```
fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer <OPENROUTER_API_KEY>',
    'HTTP-Referer': '<YOUR_SITE_URL>', // Optional. Site URL for rankings on openrouter.ai.
    'X-Title': '<YOUR_SITE_NAME>', // Optional. Site title for rankings on openrouter.ai.
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'openai/gpt-4o',
    messages: [
      {
        role: 'user',
        content: 'What is the meaning of life?',
      },
    ],
  }),
});
```

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d '{
  "model": "openai/gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
}'
```

----------------------------------------

TITLE: Calling OpenRouter API using OpenAI SDK
DESCRIPTION: Demonstrates how to integrate with the OpenRouter API using the official OpenAI SDKs. It covers setting the base URL, providing the API key, and including optional headers for site ranking. Examples are provided for Python and TypeScript, showing how to make a chat completion request. Requires the respective OpenAI SDK library.
SOURCE: https://openrouter.ai/docs/quickstart.mdx#_snippet_0

LANGUAGE: python
CODE:
```
from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="<OPENROUTER_API_KEY>",
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  model="openai/gpt-4o",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)

print(completion.choices[0].message.content)
```

LANGUAGE: typescript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: '<OPENROUTER_API_KEY>',
  defaultHeaders: {
    'HTTP-Referer': '<YOUR_SITE_URL>', // Optional. Site URL for rankings on openrouter.ai.
    'X-Title': '<YOUR_SITE_NAME>', // Optional. Site title for rankings on openrouter.ai.
  },
});

async function main() {
  const completion = await openai.chat.completions.create({
    model: 'openai/gpt-4o',
    messages: [
      {
        role: 'user',
        content: 'What is the meaning of life?',
      },
    ],
  });

  console.log(completion.choices[0].message);
}

main();
```

----------------------------------------

TITLE: Making a Chat Completion Request with Headers (TypeScript)
DESCRIPTION: This snippet demonstrates how to make a basic chat completion request to the OpenRouter API using fetch in TypeScript. It shows how to include the required Authorization header and optional HTTP-Referer and X-Title headers for identifying your application on openrouter.ai. The request body specifies the model and the initial user message.
SOURCE: https://openrouter.ai/docs/api-reference/overview.mdx#_snippet_1

LANGUAGE: typescript
CODE:
```
fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer <OPENROUTER_API_KEY>',
    'HTTP-Referer': '<YOUR_SITE_URL>', // Optional. Site URL for rankings on openrouter.ai.
    'X-Title': '<YOUR_SITE_NAME>', // Optional. Site title for rankings on openrouter.ai.
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'openai/gpt-4o',
    messages: [
      {
        role: 'user',
        content: 'What is the meaning of life?'
      }
    ]
  })
});
```

----------------------------------------

TITLE: Implementing Agentic Loop with OpenRouter Python
DESCRIPTION: This Python snippet defines functions to call an LLM via the OpenRouter API, process tool calls returned by the LLM, and execute the corresponding local tool function. It then uses a `while` loop to repeatedly call the LLM and process tool responses until the LLM provides a final non-tool response.
SOURCE: https://openrouter.ai/docs/features/tool-calling.mdx#_snippet_6

LANGUAGE: python
CODE:
```
def call_llm(msgs):
    resp = openai_client.chat.completions.create(
        model={{MODEL}},
        tools=tools,
        messages=msgs
    )
    msgs.append(resp.choices[0].message.dict())
    return resp

def get_tool_response(response):
    tool_call = response.choices[0].message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    # Look up the correct tool locally, and call it with the provided arguments
    # Other tools can be added without changing the agentic loop
    tool_result = TOOL_MAPPING[tool_name](**tool_args)

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": tool_name,
        "content": tool_result,
    }

while True:
    resp = call_llm(_messages)

    if resp.choices[0].message.tool_calls is not None:
        messages.append(get_tool_response(resp))
    else:
        break

print(messages[-1]['content'])
```

----------------------------------------

TITLE: Initializing OpenAI SDK with OpenRouter (Python)
DESCRIPTION: Shows how to initialize the OpenAI SDK in Python to connect to OpenRouter, setting the base URL and API key from environment variables. It includes examples of using `extra_headers` for site information and `extra_body` for OpenRouter-specific arguments (commented out).
SOURCE: https://openrouter.ai/docs/community/frameworks.mdx#_snippet_1

LANGUAGE: Python
CODE:
```
from openai import OpenAI
from os import getenv

# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=getenv("OPENROUTER_API_KEY"),
)

completion = client.chat.completions.create(
  model="${Model.GPT_4_Omni}",
  extra_headers={
    "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  # pass extra_body to access OpenRouter-only arguments.
  # extra_body={
    # "models": [
    #   "${Model.GPT_4_Omni}",
    #   "${Model.Mixtral_8x_22B_Instruct}"
    # ]
  # },
  messages=[
    {
      "role": "user",
      "content": "Say this is a test",
    },
  ],
)
print(completion.choices[0].message.content)
```

----------------------------------------

TITLE: Implementing Agentic Loop with OpenRouter TypeScript
DESCRIPTION: This TypeScript snippet defines asynchronous functions to call an LLM via the OpenRouter API using `fetch`, process tool calls from the LLM's response, and execute the corresponding local tool function. It uses an `async while` loop to manage the conversation flow, calling the LLM and processing tool results until a non-tool response is received.
SOURCE: https://openrouter.ai/docs/features/tool-calling.mdx#_snippet_7

LANGUAGE: typescript
CODE:
```
async function callLLM(messages: Message[]): Promise<Message> {
  const response = await fetch(
    'https://openrouter.ai/api/v1/chat/completions',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer {{API_KEY_REF}}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: '{{MODEL}}',
        tools,
        messages,
      }),
    },
  );

  const data = await response.json();
  messages.push(data.choices[0].message);
  return data;
}

async function getToolResponse(response: Message): Promise<Message> {
  const toolCall = response.toolCalls[0];
  const toolName = toolCall.function.name;
  const toolArgs = JSON.parse(toolCall.function.arguments);

  // Look up the correct tool locally, and call it with the provided arguments
  // Other tools can be added without changing the agentic loop
  const toolResult = await TOOL_MAPPING[toolName](toolArgs);

  return {
    role: 'tool',
    toolCallId: toolCall.id,
    name: toolName,
    content: toolResult,
  };
}

while (true) {
  const response = await callLLM(messages);

  if (response.toolCalls) {
    messages.push(await getToolResponse(response));
  } else {
    break;
  }
}

console.log(messages[messages.length - 1].content);
```

----------------------------------------

TITLE: Streaming Chat Completion with Reasoning Tokens using OpenRouter API in TypeScript
DESCRIPTION: Illustrates how to perform a streaming chat completion request to the OpenRouter API using the TypeScript `openai` library. The example configures a specific token limit for reasoning and iterates through the streamed response to log reasoning and content parts.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_9

LANGUAGE: TypeScript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey,
});

async function chatCompletionWithReasoning(messages) {
  const response = await openai.chat.completions.create({
    model: '{{MODEL}}',
    messages,
    maxTokens: 10000,
    reasoning: {
      maxTokens: 8000, // Directly specify reasoning token budget
    },
    stream: true,
  });

  return response;
}

(async () => {
  for await (const chunk of chatCompletionWithReasoning([
    { role: 'user', content: "What's bigger, 9.9 or 9.11?" },
  ])) {
    if (chunk.choices[0].delta.reasoning) {
      console.log(`REASONING: ${chunk.choices[0].delta.reasoning}`);
    } else if (chunk.choices[0].delta.content) {
      console.log(`CONTENT: ${chunk.choices[0].delta.content}`);
    }
  }
})();
```

----------------------------------------

TITLE: Initializing OpenAI SDK with OpenRouter (TypeScript)
DESCRIPTION: Demonstrates how to initialize the OpenAI SDK in TypeScript to use OpenRouter as the base URL, including setting the API key and default headers. It then shows how to create a chat completion.
SOURCE: https://openrouter.ai/docs/community/frameworks.mdx#_snippet_0

LANGUAGE: TypeScript
CODE:
```
import OpenAI from "openai"

const openai = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: "${API_KEY_REF}",
  defaultHeaders: {
    ${getHeaderLines().join('\n        ')}
  },
})

async function main() {
  const completion = await openai.chat.completions.create({
    model: "${Model.GPT_4_Omni}",
    messages: [
      { role: "user", content: "Say this is a test" }
    ],
  })

  console.log(completion.choices[0].message)
}
main();
```

----------------------------------------

TITLE: Sending Completions Request with JavaScript Fetch
DESCRIPTION: Example using the JavaScript Fetch API to send an asynchronous POST request to the OpenRouter completions endpoint, including headers and a stringified JSON body.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/completions';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"model":"model","prompt":"prompt"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Making Initial Chat Completion Call with TypeScript
DESCRIPTION: This TypeScript snippet shows how to make the initial API call to OpenRouter's chat completions endpoint using the fetch API. It sets the required headers, including authorization with the API key and content type, and includes the model and initial messages in the request body.
SOURCE: https://openrouter.ai/docs/features/tool-calling.mdx#_snippet_1

LANGUAGE: typescript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: `Bearer {{API_KEY_REF}}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: '{{MODEL}}',
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      {
        role: 'user',
        content: 'What are the titles of some James Joyce books?',
      },
    ],
  }),
});
```

----------------------------------------

TITLE: Implement Chain-of-Thought Reasoning with OpenRouter API (Python)
DESCRIPTION: This Python snippet demonstrates a chain-of-thought workflow using the OpenRouter API. It first queries a capable model (`deepseek/deepseek-r1`) to generate reasoning for a question, then injects this reasoning into a subsequent query to another model (`openai/gpt-4o-mini`) to improve its final answer. It requires the `requests` and `json` libraries.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_6

LANGUAGE: Python
CODE:
```
import requests
import json

question = "Which is bigger: 9.11 or 9.9?"

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {{API_KEY_REF}}",
    "Content-Type": "application/json"
}

def do_req(model, content, reasoning_config=None):
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": content}
        ],
        "stop": "</think>"
    }

    return requests.post(url, headers=headers, data=json.dumps(payload))

# Get reasoning from a capable model
content = f"{question} Please think this through, but don't output an answer"
reasoning_response = do_req("deepseek/deepseek-r1", content)
reasoning = reasoning_response.json()['choices'][0]['message']['reasoning']

# Let's test! Here's the naive response:
simple_response = do_req("openai/gpt-4o-mini", question)
print(simple_response.json()['choices'][0]['message']['content'])

# Here's the response with the reasoning token injected:
content = f"{question}. Here is some context to help you: {reasoning}"
smart_response = do_req("openai/gpt-4o-mini", content)
print(smart_response.json()['choices'][0]['message']['content'])
```

----------------------------------------

TITLE: Authenticate OpenRouter API with OpenAI SDK (TypeScript)
DESCRIPTION: This example shows how to configure and use the OpenAI TypeScript SDK to interact with the OpenRouter API. It involves setting the `baseURL` to the OpenRouter endpoint and providing the API key during client initialization. Optional default headers can also be configured.
SOURCE: https://openrouter.ai/docs/api-reference/authentication.mdx#_snippet_1

LANGUAGE: typescript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: '<OPENROUTER_API_KEY>',
  defaultHeaders: {
    'HTTP-Referer': '<YOUR_SITE_URL>', // Optional. Site URL for rankings on openrouter.ai.
    'X-Title': '<YOUR_SITE_NAME>', // Optional. Site title for rankings on openrouter.ai.
  },
});

async function main() {
  const completion = await openai.chat.completions.create({
    model: 'openai/gpt-4o',
    messages: [{ role: 'user', content: 'Say this is a test' }],
  });

  console.log(completion.choices[0].message);
}

main();
```

----------------------------------------

TITLE: Sending Completions Request with Python Requests
DESCRIPTION: Example using the Python requests library to send a POST request to the OpenRouter completions endpoint with the necessary headers and JSON payload.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/completions"

payload = {
    "model": "model",
    "prompt": "prompt"
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Implement Chain-of-Thought Reasoning with OpenRouter API (TypeScript)
DESCRIPTION: This TypeScript snippet shows how to perform a chain-of-thought reasoning workflow using the OpenRouter API via the `openai` library. It fetches reasoning from one model (`deepseek/deepseek-r1`) and uses it as context for a query to another model (`openai/gpt-4o-mini`) to enhance the response quality. It requires the `openai` library configured with the OpenRouter base URL.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_7

LANGUAGE: TypeScript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey,
});

async function doReq(model, content, reasoningConfig) {
  const payload = {
    model,
    messages: [{ role: 'user', content }],
    stop: '</think>',
    ...reasoningConfig,
  };

  return openai.chat.completions.create(payload);
}

async function getResponseWithReasoning() {
  const question = 'Which is bigger: 9.11 or 9.9?';
  const reasoningResponse = await doReq(
    'deepseek/deepseek-r1',
    `${question} Please think this through, but don't output an answer`,
  );
  const reasoning = reasoningResponse.choices[0].message.reasoning;

  // Let's test! Here's the naive response:
  const simpleResponse = await doReq('openai/gpt-4o-mini', question);
  console.log(simpleResponse.choices[0].message.content);

  // Here's the response with the reasoning token injected:
  const content = `${question}. Here is some context to help you: ${reasoning}`;
  const smartResponse = await doReq('openai/gpt-4o-mini', content);
  console.log(smartResponse.choices[0].message.content);
}

getResponseWithReasoning();
```

----------------------------------------

TITLE: Requesting Structured Output with JSON Schema (TypeScript)
DESCRIPTION: This code snippet demonstrates how to include the 'response_format' parameter in an OpenRouter API request to enforce a specific JSON schema for the model's response. It shows the structure for defining the schema, including properties, types, descriptions, required fields, and strict mode.
SOURCE: https://openrouter.ai/docs/features/structured-outputs.mdx#_snippet_0

LANGUAGE: json
CODE:
```
{
  "messages": [
    { "role": "user", "content": "What's the weather like in London?" }
  ],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "weather",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City or location name"
          },
          "temperature": {
            "type": "number",
            "description": "Temperature in Celsius"
          },
          "conditions": {
            "type": "string",
            "description": "Weather conditions description"
          }
        },
        "required": ["location", "temperature", "conditions"],
        "additionalProperties": false
      }
    }
  }
}
```

----------------------------------------

TITLE: Initializing OpenRouter Client with Python
DESCRIPTION: This snippet demonstrates the basic setup for using OpenRouter with Python. It imports necessary libraries, sets the API key and model, initializes the OpenAI client pointing to OpenRouter's base URL, and defines the initial system and user messages for a chat conversation.
SOURCE: https://openrouter.ai/docs/features/tool-calling.mdx#_snippet_0

LANGUAGE: python
CODE:
```
import json, requests
from openai import OpenAI

OPENROUTER_API_KEY = f"{{API_KEY_REF}}"

# You can use any model that supports tool calling
MODEL = "{{MODEL}}"

openai_client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

task = "What are the titles of some James Joyce books?"

messages = [
  {
    "role": "system",
    "content": "You are a helpful assistant."
  },
  {
    "role": "user",
    "content": task,
  }
]
```

----------------------------------------

TITLE: Authenticate OpenRouter API with Bearer Token (TypeScript)
DESCRIPTION: This snippet demonstrates how to make a direct HTTP POST request to the OpenRouter chat completions endpoint using the `fetch` API in TypeScript. It requires setting the `Authorization` header with a Bearer token containing your OpenRouter API key. Optional headers like `HTTP-Referer` and `X-Title` can be included for site ranking.
SOURCE: https://openrouter.ai/docs/api-reference/authentication.mdx#_snippet_0

LANGUAGE: typescript
CODE:
```
fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer <OPENROUTER_API_KEY>',
    'HTTP-Referer': '<YOUR_SITE_URL>', // Optional. Site URL for rankings on openrouter.ai.
    'X-Title': '<YOUR_SITE_NAME>', // Optional. Site title for rankings on openrouter.ai.
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'openai/gpt-4o',
    messages: [
      {
        role: 'user',
        content: 'What is the meaning of life?',
      },
    ],
  }),
});
```

----------------------------------------

TITLE: OpenRouter Chat Completions API Response Format (JSON)
DESCRIPTION: This JSON snippet illustrates the standard structure returned by the OpenRouter chat completions API. It includes details such as the unique response ID, provider, model used, object type, creation timestamp, the generated message content from the assistant, and token usage statistics for the request.
SOURCE: https://openrouter.ai/docs/features/images-and-pdfs.mdx#_snippet_6

LANGUAGE: JSON
CODE:
```
{
  "id": "gen-1234567890",
  "provider": "DeepInfra",
  "model": "google/gemma-3-27b-it",
  "object": "chat.completion",
  "created": 1234567890,
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "The document discusses..."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 1000,
    "completion_tokens": 100,
    "total_tokens": 1100
  }
}
```

----------------------------------------

TITLE: Make POST Request with requests in Python
DESCRIPTION: This Python snippet uses the popular 'requests' library to make a POST request. It defines the URL, the JSON payload as a dictionary, and the headers. The `requests.post` function handles sending the request and automatically serializes the `json` payload.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_11

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/auth/keys"

payload = { "code": "string" }
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Making Initial OpenRouter API Call with Tools (Python/TypeScript)
DESCRIPTION: This snippet demonstrates how to make the first API call to the OpenRouter chat completions endpoint. It sends the initial messages and the list of available tools to the specified model. The response is expected to contain tool call requests from the LLM.
SOURCE: https://openrouter.ai/docs/features/tool-calling.mdx#_snippet_3

LANGUAGE: python
CODE:
```
request_1 = {
    "model": {{MODEL}},
    "tools": tools,
    "messages": messages
}

response_1 = openai_client.chat.completions.create(**request_1).message
```

LANGUAGE: typescript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: `Bearer {{API_KEY_REF}}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: '{{MODEL}}',
    tools,
    messages,
  }),
});
```

----------------------------------------

TITLE: Use API Key for Request (TypeScript)
DESCRIPTION: TypeScript code snippet demonstrating how to use the obtained user-controlled API key to make a chat completions request to the OpenRouter API. Include the API key in the `Authorization` header as a Bearer token.
SOURCE: https://openrouter.ai/docs/use-cases/oauth-pkce.mdx#_snippet_6

LANGUAGE: typescript
CODE:
```
fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer <API_KEY>',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'openai/gpt-4o',
    messages: [
      {
        role: 'user',
        content: 'Hello!',
      },
    ],
  }),
});
```

----------------------------------------

TITLE: Authenticate OpenRouter API with cURL (Shell)
DESCRIPTION: This shell command uses `curl` to make a direct HTTP POST request to the OpenRouter chat completions endpoint. It sets the `Content-Type` header to `application/json` and the `Authorization` header with a Bearer token containing the API key, typically read from an environment variable.
SOURCE: https://openrouter.ai/docs/api-reference/authentication.mdx#_snippet_3

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d '{
  "model": "openai/gpt-4o",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ]
}'
```

----------------------------------------

TITLE: Processing LLM Tool Calls and Appending Results (Python/TypeScript)
DESCRIPTION: This code processes the tool calls received in the LLM's response. It iterates through the requested tool calls, executes the corresponding local function using a mapping, and appends the tool's output back to the messages array with the 'tool' role. This prepares the conversation history for the next API call.
SOURCE: https://openrouter.ai/docs/features/tool-calling.mdx#_snippet_4

LANGUAGE: python
CODE:
```
# Append the response to the messages array so the LLM has the full context
# It's easy to forget this step!
messages.append(response_1)

# Now we process the requested tool calls, and use our book lookup tool
for tool_call in response_1.tool_calls:
    '''
    In this case we only provided one tool, so we know what function to call.
    When providing multiple tools, you can inspect `tool_call.function.name`
    to figure out what function you need to call locally.
    '''
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)
    tool_response = TOOL_MAPPING[tool_name](**tool_args)
    messages.append({
      "role": "tool",
      "tool_call_id": tool_call.id,
      "name": tool_name,
      "content": json.dumps(tool_response),
    })
```

LANGUAGE: typescript
CODE:
```
// Append the response to the messages array so the LLM has the full context
// It's easy to forget this step!
messages.push(response);

// Now we process the requested tool calls, and use our book lookup tool
for (const toolCall of response.toolCalls) {
  const toolName = toolCall.function.name;
  const toolArgs = JSON.parse(toolCall.function.arguments);
  const toolResponse = await TOOL_MAPPING[toolName](toolArgs);
  messages.push({
    role: 'tool',
    toolCallId: toolCall.id,
    name: toolName,
    content: JSON.stringify(toolResponse),
  });
}
```

----------------------------------------

TITLE: Implement and Specify Project Gutenberg Search Tool
DESCRIPTION: Implements a function to search the Gutendex API for books based on search terms and defines the corresponding JSON specification for LLM function calling. The function takes an array of search terms and returns a simplified list of book results (id, title, authors). The specification details the tool's name, description, and the structure of its `search_terms` parameter.
SOURCE: https://openrouter.ai/docs/features/tool-calling.mdx#_snippet_2

LANGUAGE: python
CODE:
```
def search_gutenberg_books(search_terms):
    search_query = " ".join(search_terms)
    url = "https://gutendex.com/books"
    response = requests.get(url, params={"search": search_query})

    simplified_results = []
    for book in response.json().get("results", []):
        simplified_results.append({
            "id": book.get("id"),
            "title": book.get("title"),
            "authors": book.get("authors")
        })

    return simplified_results

tools = [
  {
    "type": "function",
    "function": {
      "name": "search_gutenberg_books",
      "description": "Search for books in the Project Gutenberg library based on specified search terms",
      "parameters": {
        "type": "object",
        "properties": {
          "search_terms": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of search terms to find books in the Gutenberg library (e.g. ['dickens', 'great'] to search for books by Dickens with 'great' in the title)"
          }
        },
        "required": ["search_terms"]
      }
    }
  }
]

TOOL_MAPPING = {
    "search_gutenberg_books": search_gutenberg_books
}
```

LANGUAGE: typescript
CODE:
```
async function searchGutenbergBooks(searchTerms: string[]): Promise<Book[]> {
  const searchQuery = searchTerms.join(' ');
  const url = 'https://gutendex.com/books';
  const response = await fetch(`${url}?search=${searchQuery}`);
  const data = await response.json();

  return data.results.map((book: any) => ({
    id: book.id,
    title: book.title,
    authors: book.authors,
  }));
}

const tools = [
  {
    type: 'function',
    function: {
      name: 'search_gutenberg_books',
      description:
        'Search for books in the Project Gutenberg library based on specified search terms',
      parameters: {
        type: 'object',
        properties: {
          search_terms: {
            type: 'array',
            items: {
              type: 'string',
            },
            description:
              "List of search terms to find books in the Gutenberg library (e.g. ['dickens', 'great'] to search for books by Dickens with 'great' in the title)",
          },
        },
        required: ['search_terms'],
      },
    },
  },
];

const TOOL_MAPPING = {
  searchGutenbergBooks,
};
```

----------------------------------------

TITLE: Streaming Chat Completion with Reasoning Tokens using OpenRouter API in Python
DESCRIPTION: Demonstrates how to make a streaming chat completion request to the OpenRouter API using the Python `openai` library. It shows how to specify a token budget for reasoning and process the streamed response, printing both reasoning and content chunks as they arrive.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_8

LANGUAGE: Python
CODE:
```
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="{{API_KEY_REF}}",
)

def chat_completion_with_reasoning(messages):
    response = client.chat.completions.create(
        model="{{MODEL}}",
        messages=messages,
        max_tokens=10000,
        reasoning={
            "max_tokens": 8000  # Directly specify reasoning token budget
        },
        stream=True
    )
    return response

for chunk in chat_completion_with_reasoning([
    {"role": "user", "content": "What's bigger, 9.9 or 9.11?"}
]):
    if hasattr(chunk.choices[0].delta, 'reasoning') and chunk.choices[0].delta.reasoning:
        print(f"REASONING: {chunk.choices[0].delta.reasoning}")
    elif chunk.choices[0].delta.content:
        print(f"CONTENT: {chunk.choices[0].delta.content}")
```

----------------------------------------

TITLE: Making a Structured Output Request with Fetch API
DESCRIPTION: Demonstrates how to make a POST request to the OpenRouter chat completions endpoint using the Fetch API in TypeScript, including setting headers, providing the model and messages, and defining a JSON Schema for the response format.
SOURCE: https://openrouter.ai/docs/features/structured-outputs.mdx#_snippet_2

LANGUAGE: typescript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer {{API_KEY_REF}}',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: '{{MODEL}}',
    messages: [
      { role: 'user', content: 'What is the weather like in London?' },
    ],
    response_format: {
      type: 'json_schema',
      json_schema: {
        name: 'weather',
        strict: true,
        schema: {
          type: 'object',
          properties: {
            location: {
              type: 'string',
              description: 'City or location name',
            },
            temperature: {
              type: 'number',
              description: 'Temperature in Celsius',
            },
            conditions: {
              type: 'string',
              description: 'Weather conditions description',
            },
          },
          required: ['location', 'temperature', 'conditions'],
          additionalProperties: false,
        },
      },
    },
  }),
});

const data = await response.json();
const weatherInfo = data.choices[0].message.content;
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with Python Requests
DESCRIPTION: This Python snippet utilizes the `requests` library to make a GET request to the OpenRouter API key endpoint. It sets the Authorization header with the bearer token and prints the JSON response.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/key"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Making a Structured Output Request with Python Requests
DESCRIPTION: Shows how to make a POST request to the OpenRouter chat completions endpoint using the `requests` library in Python, including setting headers, providing the model and messages, and defining a JSON Schema for the response format.
SOURCE: https://openrouter.ai/docs/features/structured-outputs.mdx#_snippet_3

LANGUAGE: python
CODE:
```
import requests
import json

response = requests.post(
  "https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": f"Bearer {{API_KEY_REF}}",
    "Content-Type": "application/json",
  },

  json={
    "model": "{{MODEL}}",
    "messages": [
      {"role": "user", "content": "What is the weather like in London?"},
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "weather",
        "strict": True,
        "schema": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City or location name",
            },
            "temperature": {
              "type": "number",
              "description": "Temperature in Celsius",
            },
            "conditions": {
              "type": "string",
              "description": "Weather conditions description",
            },
          },
          "required": ["location", "temperature", "conditions"],
          "additionalProperties": False,
        },
      },
    },
  },
)

data = response.json()
weather_info = data["choices"][0]["message"]["content"]
```

----------------------------------------

TITLE: Example Structured Output Response (JSON)
DESCRIPTION: This snippet shows an example of a model response that conforms to the JSON schema defined in the request. It illustrates the expected output format when structured outputs are successfully applied.
SOURCE: https://openrouter.ai/docs/features/structured-outputs.mdx#_snippet_1

LANGUAGE: json
CODE:
```
{
  "location": "London",
  "temperature": 18,
  "conditions": "Partly cloudy with light drizzle"
}
```

----------------------------------------

TITLE: Completions Request Schema (TypeScript)
DESCRIPTION: This TypeScript type definition represents the expected body structure for the POST request to the `/api/v1/chat/completions` endpoint. It outlines the required and optional parameters for initiating a chat completion request, including message formats, model selection, streaming, and various LLM control parameters.
SOURCE: https://openrouter.ai/docs/api-reference/overview.mdx#_snippet_0

LANGUAGE: TypeScript
CODE:
```
// Definitions of subtypes are below
type Request = {
  // Either "messages" or "prompt" is required
  messages?: Message[];
  prompt?: string;

  // If "model" is unspecified, uses the user's default
  model?: string; // See "Supported Models" section

  // Allows to force the model to produce specific output format.
  // See models page and note on this docs page for which models support it.
  response_format?: { type: 'json_object' };

  stop?: string | string[];
  stream?: boolean; // Enable streaming

  // See LLM Parameters (openrouter.ai/docs/api-reference/parameters)
  max_tokens?: number; // Range: [1, context_length)
  temperature?: number; // Range: [0, 2]

  // Tool calling
  // Will be passed down as-is for providers implementing OpenAI's interface.
  // For providers with custom interfaces, we transform and map the properties.
  // Otherwise, we transform the tools into a YAML template. The model responds with an assistant message.
  // See models supporting tool calling: openrouter.ai/models?supported_parameters=tools
  tools?: Tool[];
  tool_choice?: ToolChoice;

  // Advanced optional parameters
  seed?: number; // Integer only
  top_p?: number; // Range: (0, 1]
  top_k?: number; // Range: [1, Infinity) Not available for OpenAI models
  frequency_penalty?: number; // Range: [-2, 2]
  presence_penalty?: number; // Range: [-2, 2]
  repetition_penalty?: number; // Range: (0, 2]
  logit_bias?: { [key: number]: number };
  top_logprobs: number; // Integer only
  min_p?: number; // Range: [0, 1]
  top_a?: number; // Range: [0, 1]

  // Reduce latency by providing the model with a predicted output
  // https://platform.openai.com/docs/guides/latency-optimization#use-predicted-outputs
  prediction?: { type: 'content'; content: string };

  // OpenRouter-only parameters
  // See "Prompt Transforms" section: openrouter.ai/docs/transforms
  transforms?: string[];
  // See "Model Routing" section: openrouter.ai/docs/model-routing
  models?: string[];
  route?: 'fallback';
  // See "Provider Routing" section: openrouter.ai/docs/provider-routing
  provider?: ProviderPreferences;
};

// Subtypes:

type TextContent = {
  type: 'text';
  text: string;
};

type ImageContentPart = {
  type: 'image_url';
  image_url: {
    url: string; // URL or base64 encoded image data
    detail?: string; // Optional, defaults to "auto"
  };
};

type ContentPart = TextContent | ImageContentPart;

type Message =
  | {
      role: 'user' | 'assistant' | 'system';
      // ContentParts are only for the "user" role:
      content: string | ContentPart[];
      // If "name" is included, it will be prepended like this
      // for non-OpenAI models: `{name}: {content}`
      name?: string;
    }
  | {
      role: 'tool';
      content: string;
      tool_call_id: string;
      name?: string;
    };

type FunctionDescription = {
  description?: string;
  name: string;
  parameters: object; // JSON Schema object
};

type Tool = {
  type: 'function';
  function: FunctionDescription;
};

type ToolChoice =
  | 'none'
  | 'auto'
  | {
      type: 'function';
      function: {
        name: string;
      };
    };
```

----------------------------------------

TITLE: Create OpenRouter API Key using cURL
DESCRIPTION: Example using cURL to send a POST request to the OpenRouter API to create a new API key. It includes setting the Authorization and Content-Type headers and providing the request body with the key name.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl -X POST https://openrouter.ai/api/v1/keys \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
  "name": "name"
}'
```

----------------------------------------

TITLE: Streaming Chat Completion with Usage - OpenRouter API
DESCRIPTION: This code snippet shows how to initiate a streaming chat completion request to the OpenRouter API using the OpenAI SDK. It configures the request to include usage information and iterates through the streamed chunks, printing either the content delta or the usage statistics when available.
SOURCE: https://openrouter.ai/docs/use-cases/usage-accounting.mdx#_snippet_4

LANGUAGE: Python
CODE:
```
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="{{API_KEY_REF}}",
)

def chat_completion_with_usage(messages):
    response = client.chat.completions.create(
        model="{{MODEL}}",
        messages=messages,
        usage={
          "include": True
        },
        stream=True
    )
    return response

for chunk in chat_completion_with_usage([
    {"role": "user", "content": "Write a haiku about Paris."}
]):
    if hasattr(chunk, 'usage'):
        print(f"\nUsage Statistics:")
        print(f"Total Tokens: {chunk.usage.total_tokens}")
        print(f"Prompt Tokens: {chunk.usage.prompt_tokens}")
        print(f"Completion Tokens: {chunk.usage.completion_tokens}")
        print(f"Cost: {chunk.usage.cost} credits")
    elif chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

LANGUAGE: TypeScript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: '{{API_KEY_REF}}',
});

async function chatCompletionWithUsage(messages) {
  const response = await openai.chat.completions.create({
    model: '{{MODEL}}',
    messages,
    usage: {
      include: true,
    },
    stream: true,
  });

  return response;
}

(async () => {
  for await (const chunk of chatCompletionWithUsage([
    { role: 'user', content: 'Write a haiku about Paris.' },
  ])) {
    if (chunk.usage) {
      console.log('\nUsage Statistics:');
      console.log(`Total Tokens: ${chunk.usage.total_tokens}`);
      console.log(`Prompt Tokens: ${chunk.usage.prompt_tokens}`);
      console.log(`Completion Tokens: ${chunk.usage.completion_tokens}`);
      console.log(`Cost: ${chunk.usage.cost} credits`);
    } else if (chunk.choices[0].delta.content) {
      process.stdout.write(chunk.choices[0].delta.content);
    }
  }
})();
```

----------------------------------------

TITLE: Sending Chat Completion Request with cURL
DESCRIPTION: Demonstrates how to send a POST request to the OpenRouter chat completions endpoint using the cURL command-line tool, including setting headers for authorization and content type, and providing a JSON request body.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl -X POST https://openrouter.ai/api/v1/chat/completions \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
  "model": "openai/gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
}'
```

----------------------------------------

TITLE: Defining OpenRouter Response Subtypes (TypeScript)
DESCRIPTION: Defines various TypeScript subtypes used within the OpenRouter completions response, including `NonChatChoice`, `NonStreamingChoice`, `StreamingChoice`, `ErrorResponse`, and `ToolCall`, detailing their properties like finish reasons, message/delta content, errors, and tool calls.
SOURCE: https://openrouter.ai/docs/api-reference/overview.mdx#_snippet_5

LANGUAGE: TypeScript
CODE:
```
// Subtypes:
type NonChatChoice = {
  finish_reason: string | null;
  text: string;
  error?: ErrorResponse;
};

type NonStreamingChoice = {
  finish_reason: string | null;
  native_finish_reason: string | null;
  message: {
    content: string | null;
    role: string;
    tool_calls?: ToolCall[];
  };
  error?: ErrorResponse;
};

type StreamingChoice = {
  finish_reason: string | null;
  native_finish_reason: string | null;
  delta: {
    content: string | null;
    role?: string;
    tool_calls?: ToolCall[];
  };
  error?: ErrorResponse;
};

type ErrorResponse = {
  code: number; // See "Error Handling" section
  message: string;
  metadata?: Record<string, unknown>; // Contains additional error information such as provider details, the raw error message, etc.
};

type ToolCall = {
  id: string;
  type: 'function';
  function: FunctionCall;
};
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with cURL (Shell)
DESCRIPTION: This cURL command demonstrates how to make a GET request to the OpenRouter API keys endpoint. It includes the necessary Authorization header with a bearer token (Provisioning API key) to authenticate the request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/keys \
     -H "Authorization: Bearer <token>"
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with JavaScript Fetch
DESCRIPTION: This JavaScript snippet uses the browser's or Node.js's `fetch` API to perform an asynchronous GET request to the OpenRouter API key endpoint. It includes the Authorization header and logs the JSON response or any errors.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/key';
const options = {method: 'GET', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Using Assistant Prefill in Chat Completions (TypeScript)
DESCRIPTION: This snippet illustrates how to use the assistant prefill feature in the OpenRouter chat completions API. By including a message with role: "assistant" and partial content at the end of the messages array, you can guide the model to complete a specific response. This example shows a request body configured for prefilling the assistant's reply.
SOURCE: https://openrouter.ai/docs/api-reference/overview.mdx#_snippet_2

LANGUAGE: typescript
CODE:
```
fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer <OPENROUTER_API_KEY>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'openai/gpt-4o',
    messages: [
      { role: 'user', content: 'What is the meaning of life?' },
      { role: 'assistant', content: "I'm not sure, but my best guess is" }
    ]
  })
});
```

----------------------------------------

TITLE: Sending Chat Completion Request with C# RestClient
DESCRIPTION: Shows how to use a RestClient library (commonly RestSharp) in C# to construct and execute a POST request to the OpenRouter chat completions endpoint, adding necessary headers and the JSON request body.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/chat/completions");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"model\": \"openai/gpt-3.5-turbo\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Defining OpenRouter API Error Response Structure - TypeScript
DESCRIPTION: This TypeScript type definition outlines the expected structure of a JSON error response returned by the OpenRouter API. It includes a nested 'error' object containing a numeric code, a string message, and optional metadata.
SOURCE: https://openrouter.ai/docs/api-reference/errors.mdx#_snippet_0

LANGUAGE: typescript
CODE:
```
type ErrorResponse = {
  error: {
    code: number;
    message: string;
    metadata?: Record<string, unknown>;
  };
};
```

----------------------------------------

TITLE: Create OpenRouter API Key using Python Requests
DESCRIPTION: Demonstrates how to create an OpenRouter API key using the Python requests library. It sets up the URL, request body payload, headers including authorization, and sends a POST request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/keys"

payload = { "name": "name" }
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Streaming Chat Completions with OpenRouter API (Python)
DESCRIPTION: Demonstrates how to make a streaming request to the OpenRouter chat completions API using Python's `requests` library. It sets `stream` to true and processes the Server-Sent Events (SSE) chunks, parsing JSON data and printing content deltas.
SOURCE: https://openrouter.ai/docs/api-reference/streaming.mdx#_snippet_0

LANGUAGE: Python
CODE:
```
import requests
import json

question = "How would you build the tallest building ever?"

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
  "Authorization": f"Bearer {{API_KEY_REF}}",
  "Content-Type": "application/json"
}

payload = {
  "model": "{{MODEL}}",
  "messages": [{"role": "user", "content": question}],
  "stream": True
}

buffer = ""
with requests.post(url, headers=headers, json=payload, stream=True) as r:
  for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
    buffer += chunk
    while True:
      try:
        # Find the next complete SSE line
        line_end = buffer.find('\n')
        if line_end == -1:
          break

        line = buffer[:line_end].strip()
        buffer = buffer[line_end + 1:]

        if line.startswith('data: '):
          data = line[6:]
          if data == '[DONE]':
            break

          try:
            data_obj = json.loads(data)
            content = data_obj["choices"][0]["delta"].get("content")
            if content:
              print(content, end="", flush=True)
          except json.JSONDecodeError:
            pass
      except Exception:
        break
```

----------------------------------------

TITLE: Basic Usage with Token Tracking (Python)
DESCRIPTION: Shows a Python example using the 'requests' library to make a chat completion request to OpenRouter with usage accounting enabled and how to access the response content and usage statistics.
SOURCE: https://openrouter.ai/docs/use-cases/usage-accounting.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests
import json

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {{API_KEY_REF}}",
    "Content-Type": "application/json"
}
payload = {
    "model": "{{MODEL}}",
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "usage": {
        "include": True
    }
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print("Response:", response.json()['choices'][0]['message']['content'])
print("Usage Stats:", response.json()['usage'])
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with cURL
DESCRIPTION: This snippet uses the cURL command-line tool to perform a GET request to the OpenRouter API key endpoint. It includes the necessary Authorization header with a bearer token.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/key \
     -H "Authorization: Bearer <token>"
```

----------------------------------------

TITLE: Delete OpenRouter API Key using cURL
DESCRIPTION: Example using cURL to send a DELETE request to the OpenRouter API endpoint. Includes the Authorization header with a bearer token.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl -X DELETE https://openrouter.ai/api/v1/keys/hash \
     -H "Authorization: Bearer <token>"
```

----------------------------------------

TITLE: Retrieve API Key - Shell (curl)
DESCRIPTION: Uses the curl command-line tool to perform a GET request to the OpenRouter API key endpoint. It includes the necessary Authorization header with a Bearer token.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_11

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/key \
     -H "Authorization: Bearer <token>"
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with Fetch (JavaScript)
DESCRIPTION: This JavaScript code uses the Fetch API to asynchronously retrieve the list of OpenRouter API keys. It constructs the request with the GET method and includes the Authorization header.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/keys';
const options = {method: 'GET', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Sending Completions Request with C# RestSharp
DESCRIPTION: Example using the C# RestSharp library to create and execute a POST request to the OpenRouter completions endpoint with headers and a request body parameter.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/completions");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"model\": \"model\",\n  \"prompt\": \"prompt\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Making Second OpenRouter API Call with Tool Results (Python/TypeScript)
DESCRIPTION: This snippet makes a subsequent API call to the OpenRouter chat completions endpoint. It sends the updated messages array, which now includes the results of the executed tool calls, along with the tools list again. The LLM is expected to use the tool results to generate the final response. The code then prints the final message content.
SOURCE: https://openrouter.ai/docs/features/tool-calling.mdx#_snippet_5

LANGUAGE: python
CODE:
```
request_2 = {
  "model": MODEL,
  "messages": messages,
  "tools": tools
}

response_2 = openai_client.chat.completions.create(**request_2)

print(response_2.choices[0].message.content)
```

LANGUAGE: typescript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: `Bearer {{API_KEY_REF}}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: '{{MODEL}}',
    messages,
    tools,
  }),
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

----------------------------------------

TITLE: Create OpenRouter API Key using JavaScript Fetch
DESCRIPTION: Example using the JavaScript Fetch API to create an OpenRouter API key. It configures the POST request with headers and body and handles the asynchronous response.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/keys';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"name":"name"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Send Image URL to OpenRouter Chat Completions API
DESCRIPTION: Demonstrates how to make a POST request to the OpenRouter chat completions endpoint with an image provided as a URL in the message content. Requires an API key and uses a multimodal model.
SOURCE: https://openrouter.ai/docs/features/images-and-pdfs.mdx#_snippet_0

LANGUAGE: python
CODE:
```
import requests
import json

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY_REF}",
    "Content-Type": "application/json"
}

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "What's in this image?"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                }
            }
        ]
    }
]

payload = {
    "model": "{{MODEL}}",
    "messages": messages
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

LANGUAGE: typescript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${API_KEY_REF}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: '{{MODEL}}',
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: "What's in this image?",
          },
          {
            type: 'image_url',
            image_url: {
              url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg',
            },
          },
        ],
      },
    ],
  }),
});

const data = await response.json();
console.log(data);
```

----------------------------------------

TITLE: Printing OpenRouter API Error Details - JavaScript
DESCRIPTION: This JavaScript code snippet demonstrates how to fetch a response from the OpenRouter API, check the HTTP status code, and parse the JSON body to access and print the error code and message if an error occurred. It shows how to access the nested 'error' object.
SOURCE: https://openrouter.ai/docs/api-reference/errors.mdx#_snippet_1

LANGUAGE: javascript
CODE:
```
const request = await fetch('https://openrouter.ai/...');
console.log(request.status); // Will be an error code unless the model started processing your request
const response = await request.json();
console.error(response.error?.status); // Will be an error code
console.error(response.error?.message);
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with JavaScript Fetch
DESCRIPTION: This JavaScript snippet uses the `fetch` API to make an asynchronous GET request to the OpenRouter API. It includes the required `Authorization` header and logs the parsed JSON response or any errors.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/keys/hash';
const options = {method: 'GET', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Listing Models with Python Requests
DESCRIPTION: Provides a Python example using the `requests` library to perform a GET request to the OpenRouter API models endpoint and print the JSON response.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/models"

response = requests.get(url)

print(response.json())
```

----------------------------------------

TITLE: Delete OpenRouter API Key using JavaScript Fetch
DESCRIPTION: JavaScript example using the `fetch` API to send a DELETE request. Includes error handling and logs the JSON response.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/keys/hash';
const options = {method: 'DELETE', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Sending PDF for Processing with OpenRouter API
DESCRIPTION: Demonstrates how to encode a PDF file into a base64 data URL and include it in the 'messages' array of an OpenRouter chat completion request. It also shows the optional 'plugins' configuration for specifying the parsing engine.
SOURCE: https://openrouter.ai/docs/features/images-and-pdfs.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests
import json
import base64
from pathlib import Path

def encode_pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode('utf-8')

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY_REF}",
    "Content-Type": "application/json"
}

# Read and encode the PDF
pdf_path = "path/to/your/document.pdf"
base64_pdf = encode_pdf_to_base64(pdf_path)
data_url = f"data:application/pdf;base64,{base64_pdf}"

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "What are the main points in this document?"
            },
            {
                "type": "file",
                "file": {
                    "filename": "document.pdf",
                    "file_data": data_url
                }
            },
        ]
    }
]

# Optional: Configure PDF processing engine
# PDF parsing will still work even if the plugin is not explicitly set
plugins = [
    {
        "id": "file-parser",
        "pdf": {
            "engine": "{{ENGINE}}"  # defaults to "{{DEFAULT_PDF_ENGINE}}". See Pricing below
        }
    }
]

payload = {
    "model": "{{MODEL}}",
    "messages": messages,
    "plugins": plugins
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

LANGUAGE: typescript
CODE:
```
async function encodePDFToBase64(pdfPath: string): Promise<string> {
  const pdfBuffer = await fs.promises.readFile(pdfPath);
  const base64PDF = pdfBuffer.toString('base64');
  return `data:application/pdf;base64,${base64PDF}`;
}

// Read and encode the PDF
const pdfPath = 'path/to/your/document.pdf';
const base64PDF = await encodePDFToBase64(pdfPath);

const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${API_KEY_REF}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: '{{MODEL}}',
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: 'What are the main points in this document?',
          },
          {
            type: 'file',
            file: {
              filename: 'document.pdf',
              file_data: base64PDF,
            },
          },
        ],
      },
    ],
    // Optional: Configure PDF processing engine
    // PDF parsing will still work even if the plugin is not explicitly set
    plugins: [
      {
        id: 'file-parser',
        pdf: {
          engine: '{{ENGINE}}', // defaults to "{{DEFAULT_PDF_ENGINE}}". See Pricing below
        },
      },
    ],
  }),
});

const data = await response.json();
console.log(data);
```

----------------------------------------

TITLE: OpenRouter Credits API Response Structure (JSON)
DESCRIPTION: This JSON snippet illustrates the data structure returned by the `GET /api/v1/credits` endpoint. It includes the `total_credits` purchased and `total_usage` in the `data` object, allowing calculation of the current balance.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_25

LANGUAGE: JSON
CODE:
```
{
  "data": {
    "total_credits": 50.0,
    "total_usage": 42.0
  }
}
```

----------------------------------------

TITLE: Calling OpenRouter API with Reasoning Max Tokens (Python)
DESCRIPTION: Demonstrates how to make a chat completion request to the OpenRouter API using Python's `requests` library, specifying the maximum number of tokens (or approximate effort) to allocate for the model's internal reasoning process via the `reasoning.max_tokens` parameter. It then prints the reasoning and content from the response.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests
import json

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {{API_KEY_REF}}",
    "Content-Type": "application/json"
}
payload = {
    "model": "{{MODEL}}",
    "messages": [
        {"role": "user", "content": "What's the most efficient algorithm for sorting a large dataset?"}
    ],
    "reasoning": {
        "max_tokens": 2000  # Allocate 2000 tokens (or approximate effort) for reasoning
    }
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.json()['choices'][0]['message']['reasoning'])
print(response.json()['choices'][0]['message']['content'])
```

----------------------------------------

TITLE: Initializing LangChain ChatOpenAI with OpenRouter (TypeScript)
DESCRIPTION: Provides a TypeScript example for initializing LangChain's `ChatOpenAI` model to use OpenRouter as the base path. It demonstrates setting the model name, temperature, streaming option, API key, and optional headers for site information.
SOURCE: https://openrouter.ai/docs/community/frameworks.mdx#_snippet_2

LANGUAGE: TypeScript
CODE:
```
const chat = new ChatOpenAI(
  {
    modelName: '<model_name>',
    temperature: 0.8,
    streaming: true,
    openAIApiKey: '${API_KEY_REF}',
  },
  {
    basePath: 'https://openrouter.ai/api/v1',
    baseOptions: {
      headers: {
        'HTTP-Referer': '<YOUR_SITE_URL>', // Optional. Site URL for rankings on openrouter.ai.
        'X-Title': '<YOUR_SITE_NAME>', // Optional. Site title for rankings on openrouter.ai.
      },
    },
  },
);
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with Python Requests
DESCRIPTION: This Python snippet uses the `requests` library to perform a GET request to the OpenRouter API. It sets the `Authorization` header with a Bearer token and prints the JSON response containing the API key details.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/keys/hash"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Exchange Auth Code for API Key - HTTP
DESCRIPTION: This HTTP snippet shows the endpoint and method used to exchange an authorization code for a user-controlled API key. It requires a POST request to the specified URL with a JSON content type.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_0

LANGUAGE: HTTP
CODE:
```
POST https://openrouter.ai/api/v1/auth/keys
Content-Type: application/json
```

----------------------------------------

TITLE: Sending Completions Request with Go net/http
DESCRIPTION: Example using Go's standard net/http package to construct and send a POST request to the OpenRouter completions endpoint with headers and a request body reader.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/completions"

	payload := strings.NewReader("{\n  \"model\": \"model\",\n  \"prompt\": \"prompt\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Listing OpenRouter API Keys via HTTP
DESCRIPTION: This snippet shows the basic HTTP structure for requesting a list of API keys from the OpenRouter API. It requires a GET request to the specified endpoint and an Authorization header with a Provisioning API key.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_0

LANGUAGE: http
CODE:
```
GET https://openrouter.ai/api/v1/keys
```

----------------------------------------

TITLE: POSTing to Auth Keys Endpoint with Go net/http
DESCRIPTION: Provides an example of sending a POST request to the /api/v1/auth/keys endpoint using Go's standard `net/http` package. It constructs the request, sets headers, and sends the JSON body.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/auth/keys"

	payload := strings.NewReader("{\n  \"code\": \"code\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/auth/keys"

	payload := strings.NewReader("{\n  \"code\": \"string\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - Python (requests)
DESCRIPTION: Demonstrates how to use the Python requests library to make a GET request to the OpenRouter API endpoint for listing model endpoints and print the JSON response. Requires the 'requests' library.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/models/author/slug/endpoints"

response = requests.get(url)

print(response.json())
```

----------------------------------------

TITLE: Update OpenRouter API Key using Python Requests
DESCRIPTION: Provides a Python example using the 'requests' library to update an OpenRouter API key. It constructs a PATCH request with the necessary URL, headers (Authorization, Content-Type), and an empty JSON payload.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/keys/hash"

payload = {}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.patch(url, json=payload, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: POSTing to Auth Keys Endpoint with JavaScript Fetch
DESCRIPTION: Illustrates making a POST request to the /api/v1/auth/keys endpoint using the browser's or Node.js's `fetch` API. It configures the method, headers, and request body.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/auth/keys';
const options = {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: '{"code":"code"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/auth/keys';
const options = {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: '{"code":"string"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Get Credits - Python (requests)
DESCRIPTION: Provides a Python example using the requests library to fetch user credit information from the OpenRouter API, including setting the necessary Authorization header and printing the JSON response.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/credits"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Calling OpenRouter API Excluding Reasoning Output (TypeScript)
DESCRIPTION: Demonstrates using the `openai` library with the OpenRouter API base URL in TypeScript to make a chat completion request, setting `reasoning.exclude: true`. This instructs the model to use reasoning internally but omit it from the response. It then attempts to log reasoning (which will be undefined) and the content.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_5

LANGUAGE: typescript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: '{{API_KEY_REF}}',
});

async function getResponseWithReasoning() {
  const response = await openai.chat.completions.create({
    model: '{{MODEL}}',
    messages: [
      {
        role: 'user',
        content: "How would you build the world's tallest skyscraper?",
      },
    ],
    reasoning: {
      effort: 'high',
      exclude: true, // Use reasoning but don't include it in the response
    },
  });

  console.log('REASONING:', response.choices[0].message.reasoning);
  console.log('CONTENT:', response.choices[0].message.content);
}

getResponseWithReasoning();
```

----------------------------------------

TITLE: Basic Usage with Token Tracking (TypeScript)
DESCRIPTION: Provides a TypeScript example using the OpenAI library configured for OpenRouter to perform a chat completion request with usage accounting enabled and log the response content and usage details.
SOURCE: https://openrouter.ai/docs/use-cases/usage-accounting.mdx#_snippet_3

LANGUAGE: typescript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: '{{API_KEY_REF}}',
});

async function getResponseWithUsage() {
  const response = await openai.chat.completions.create({
    model: '{{MODEL}}',
    messages: [
      {
        role: 'user',
        content: 'What is the capital of France?',
      },
    ],
    usage: {
      include: true,
    },
  });

  console.log('Response:', response.choices[0].message.content);
  console.log('Usage Stats:', response.usage);
}

getResponseWithUsage();
```

----------------------------------------

TITLE: POSTing to Auth Keys Endpoint with Python Requests
DESCRIPTION: Shows how to perform a POST request to the /api/v1/auth/keys endpoint using the Python `requests` library. It sets the `Content-Type` header and sends a JSON payload.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/auth/keys"

payload = { "code": "code" }
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/auth/keys"

payload = { "code": "string" }
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Get Current API Key - HTTP
DESCRIPTION: This snippet shows the HTTP GET request to retrieve information about the API key associated with the current authentication session.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_0

LANGUAGE: http
CODE:
```
GET https://openrouter.ai/api/v1/key
```

----------------------------------------

TITLE: Checking Available Credits via OpenRouter API (TypeScript)
DESCRIPTION: This code snippet shows how to make a GET request to the `/api/v1/credits` endpoint of the OpenRouter API using the `fetch` function. It requires an API key in the Authorization header. The response contains the total credits purchased and used.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_24

LANGUAGE: TypeScript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/credits', {
  method: 'GET',
  headers: { Authorization: 'Bearer <OPENROUTER_API_KEY>' },
});
const { data } = await response.json();
```

----------------------------------------

TITLE: List OpenRouter API Keys
DESCRIPTION: Demonstrates how to retrieve a list of the most recent API keys using a GET request to the `/api/v1/keys` endpoint. Shows how to include the Provisioning API key in the Authorization header and how to use the `offset` parameter for pagination.
SOURCE: https://openrouter.ai/docs/features/provisioning-api-keys.mdx#_snippet_0

LANGUAGE: python
CODE:
```
import requests

PROVISIONING_API_KEY = "your-provisioning-key"
BASE_URL = "https://openrouter.ai/api/v1/keys"

# List the most recent 100 API keys
response = requests.get(
    BASE_URL,
    headers={
        "Authorization": f"Bearer {PROVISIONING_API_KEY}",
        "Content-Type": "application/json"
    }
)

# You can paginate using the offset parameter
response = requests.get(
    f"{BASE_URL}?offset=100",
    headers={
        "Authorization": f"Bearer {PROVISIONING_API_KEY}",
        "Content-Type": "application/json"
    }
)
```

LANGUAGE: typescript
CODE:
```
const PROVISIONING_API_KEY = 'your-provisioning-key';
const BASE_URL = 'https://openrouter.ai/api/v1/keys';

// List the most recent 100 API keys
const listKeys = await fetch(BASE_URL, {
  headers: {
    Authorization: `Bearer ${PROVISIONING_API_KEY}`,
    'Content-Type': 'application/json',
  },
});

// You can paginate using the `offset` query parameter
const listKeys = await fetch(`${BASE_URL}?offset=100`, {
  headers: {
    Authorization: `Bearer ${PROVISIONING_API_KEY}`,
    'Content-Type': 'application/json',
  },
});
```

----------------------------------------

TITLE: Get Credits - JavaScript (fetch)
DESCRIPTION: Shows how to make an asynchronous GET request to the credits endpoint using JavaScript's fetch API, including handling the response and potential errors.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/credits';
const options = {method: 'GET', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with curl
DESCRIPTION: This curl command demonstrates how to make a GET request to the OpenRouter API to fetch details for a specific API key. It includes the necessary `Authorization` header with a Bearer token for authentication.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/keys/hash \
     -H "Authorization: Bearer <token>"
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with Swift URLSession
DESCRIPTION: This Swift snippet uses `URLSession` to make a GET request to the OpenRouter API. It sets the URL, HTTP method, and includes the `Authorization` header. The response or any error is handled asynchronously in the completion handler.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/keys/hash")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - JavaScript (fetch)
DESCRIPTION: Shows how to use the JavaScript Fetch API to perform an asynchronous GET request to the OpenRouter API endpoint for listing model endpoints and log the JSON response or any errors. Requires a modern JavaScript environment supporting `fetch` and `async/await`.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/models/author/slug/endpoints';
const options = {method: 'GET'};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: POSTing to Auth Keys Endpoint with cURL
DESCRIPTION: Demonstrates making a POST request to the /api/v1/auth/keys endpoint using the `curl` command-line tool. It includes setting the `Content-Type` header and sending a JSON body containing a `code` field.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl -X POST https://openrouter.ai/api/v1/auth/keys \
     -H "Content-Type: application/json" \
     -d '{
  "code": "code"
}'
```

LANGUAGE: shell
CODE:
```
curl -X POST https://openrouter.ai/api/v1/auth/keys \
     -H "Content-Type: application/json" \
     -d '{
  "code": "string"
}'
```

----------------------------------------

TITLE: Retrieve API Key - Python
DESCRIPTION: Demonstrates how to use the Python requests library to make a GET request to the OpenRouter API key endpoint. It sets the Authorization header and prints the JSON response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_12

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/key"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with URLSession (Swift)
DESCRIPTION: This Swift code uses URLSession to perform an asynchronous GET request to retrieve the list of OpenRouter API keys. It sets up the request with the URL, method, and includes the necessary Authorization header.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/keys")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Retrieve API Key - JavaScript (Fetch)
DESCRIPTION: Shows how to use the modern Fetch API in JavaScript to perform an asynchronous GET request to the OpenRouter API key endpoint. It includes the Authorization header and logs the JSON response data or any errors.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_13

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/key';
const options = {method: 'GET', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with Requests (Python)
DESCRIPTION: This Python snippet uses the requests library to perform a GET request to retrieve the list of OpenRouter API keys. It sets the Authorization header with the required bearer token.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/keys"

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Cancelling OpenRouter Stream with Python
DESCRIPTION: This Python snippet demonstrates how to cancel a streaming chat completion request to the OpenRouter API using the `requests` library and a `threading.Event`. A separate thread handles the streaming, allowing the main thread to signal cancellation via the event.
SOURCE: https://openrouter.ai/docs/api-reference/streaming.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests
from threading import Event, Thread

def stream_with_cancellation(prompt: str, cancel_event: Event):
    with requests.Session() as session:
        response = session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {{API_KEY_REF}}"
            },
            json={
                "model": "{{MODEL}}",
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "stream": True
            },
            stream=True
        )

        try:
            for line in response.iter_lines():
                if cancel_event.is_set():
                    response.close()
                    return
                if line:
                    print(line.decode(), end="", flush=True)
        finally:
            response.close()

# Example usage:
cancel_event = Event()
stream_thread = Thread(target=lambda: stream_with_cancellation("Write a story", cancel_event))
stream_thread.start()

# To cancel the stream:
cancel_event.set()
```

----------------------------------------

TITLE: Using OpenRouter Auto Router (JSON)
DESCRIPTION: Demonstrates how to specify the OpenRouter Auto Router using the special model ID "openrouter/auto" in the request payload. This allows OpenRouter to dynamically select the best model based on the prompt.
SOURCE: https://openrouter.ai/docs/features/model-routing.mdx#_snippet_0

LANGUAGE: json
CODE:
```
{
  "model": "openrouter/auto",
  ... // Other params
}
```

----------------------------------------

TITLE: Sending Chat Completion Request with Swift URLSession
DESCRIPTION: Demonstrates how to use Swift's `URLSession` to create and send a POST request to the OpenRouter chat completions API, including setting headers, serializing the JSON body, and handling the asynchronous response.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = ["model": "openai/gpt-3.5-turbo"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/chat/completions")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with Ruby net/http
DESCRIPTION: This Ruby snippet uses the standard `uri` and `net/http` libraries to make a GET request to the OpenRouter API. It sets up an HTTPS connection, adds the `Authorization` header, and prints the response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/keys/hash")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with Ruby net/http
DESCRIPTION: This Ruby snippet uses the standard `net/http` library to construct and send a GET request to the OpenRouter API key endpoint. It sets the Authorization header and prints the response body. SSL is enabled for the HTTPS connection.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/key")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Fetching Models with JavaScript
DESCRIPTION: Shows how to use the browser's or Node.js's `fetch` API to make a GET request to the OpenRouter API models endpoint and log the resulting JSON data.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/models';
const options = {method: 'GET'};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Make POST Request with curl in Shell
DESCRIPTION: This shell command uses curl to send a POST request to the specified OpenRouter API endpoint. It sets the HTTP method to POST, includes the Content-Type header, and provides the JSON request body using the -d flag.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_10

LANGUAGE: shell
CODE:
```
curl -X POST https://openrouter.ai/api/v1/auth/keys \
     -H "Content-Type: application/json" \
     -d '{
  "code": "string"
}'
```

----------------------------------------

TITLE: Using Fallback Models with OpenAI SDK (TypeScript)
DESCRIPTION: Example using the OpenAI SDK in TypeScript to configure fallback models via the `extra_body` parameter when making a chat completion request to OpenRouter. The primary model is specified in `model`, and fallbacks are listed in `models`.
SOURCE: https://openrouter.ai/docs/features/model-routing.mdx#_snippet_2

LANGUAGE: typescript
CODE:
```
import OpenAI from 'openai';

const openrouterClient = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  // API key and headers
});

async function main() {
  // @ts-expect-error
  const completion = await openrouterClient.chat.completions.create({
    model: 'openai/gpt-4o',
    models: ['anthropic/claude-3.5-sonnet', 'gryphe/mythomax-l2-13b'],
    messages: [
      {
        role: 'user',
        content: 'What is the meaning of life?',
      },
    ],
  });
  console.log(completion.choices[0].message);
}

main();
```

----------------------------------------

TITLE: Delete OpenRouter API Key using Python Requests
DESCRIPTION: Python example using the `requests` library to perform a DELETE request to the OpenRouter API. Sets the Authorization header and prints the JSON response.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/keys/hash"

headers = {"Authorization": "Bearer <token>"}

response = requests.delete(url, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Fetching Generation Statistics (TypeScript)
DESCRIPTION: Demonstrates how to use TypeScript and the `fetch` API to query the `/api/v1/generation` endpoint using a generation ID to retrieve detailed statistics, including native token counts and cost, after a completion request is complete.
SOURCE: https://openrouter.ai/docs/api-reference/overview.mdx#_snippet_7

LANGUAGE: TypeScript
CODE:
```
const generation = await fetch(
    'https://openrouter.ai/api/v1/generation?id=$GENERATION_ID',
    { headers },
  );

  const stats = await generation.json();
```

----------------------------------------

TITLE: Retrieve API Key - Swift
DESCRIPTION: Makes a GET request to the OpenRouter API key endpoint using URLSession, including setting the Authorization header with a Bearer token. It prints the HTTP response upon completion.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_10

LANGUAGE: swift
CODE:
```
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/key")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with Go net/http
DESCRIPTION: This Go snippet demonstrates how to use the standard `net/http` package to create and execute a GET request to the OpenRouter API key endpoint. It adds the Authorization header and prints the response status and body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/key"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")
	res, _ := http.DefaultClient.Do(req)
	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Get Credits - Shell (curl)
DESCRIPTION: Demonstrates how to use the curl command-line tool to make a GET request to the credits endpoint, including setting the Authorization header.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/credits \
     -H "Authorization: Bearer <token>"
```

----------------------------------------

TITLE: Update OpenRouter API Key using cURL
DESCRIPTION: Demonstrates how to update an OpenRouter API key using the cURL command-line tool. It sends a PATCH request to the specified endpoint with the Authorization and Content-Type headers and an empty JSON body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl -X PATCH https://openrouter.ai/api/v1/keys/hash \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{}'
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with net/http (Ruby)
DESCRIPTION: This Ruby script uses the net/http library to perform a GET request to fetch the list of OpenRouter API keys. It sets up the URI, creates an HTTP client, and adds the Authorization header to the request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/keys")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - Shell (curl)
DESCRIPTION: Example using curl to perform a GET request to the OpenRouter API endpoint for listing model endpoints. Replace 'author' and 'slug' with actual values.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/models/author/slug/endpoints
```

----------------------------------------

TITLE: Retrieve API Key - Go
DESCRIPTION: Illustrates making a GET request to the OpenRouter API key endpoint using Go's standard net/http package. It sets the Authorization header, executes the request, and prints the response status and body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_14

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/key"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with C# RestSharp
DESCRIPTION: This C# snippet uses the RestSharp library to create and execute a GET request to the OpenRouter API key endpoint. It adds the Authorization header to the request before executing it.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/key");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Retrieve API Key - PHP (GuzzleHttp)
DESCRIPTION: Demonstrates using the GuzzleHttp client in PHP to perform a GET request to the OpenRouter API key endpoint. It sets the Authorization header and echoes the response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_17

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/key', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with net/http (Go)
DESCRIPTION: This Go program demonstrates how to use the standard net/http package to make a GET request to the OpenRouter API keys endpoint. It creates a new request, adds the Authorization header, and executes the request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/keys"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with PHP GuzzleHttp
DESCRIPTION: This PHP snippet uses the `GuzzleHttp` client library to make a GET request to the OpenRouter API. It configures the request with the required `Authorization` header and outputs the response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/keys/hash', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();

```

----------------------------------------

TITLE: Create OpenRouter API Key using PHP Guzzle
DESCRIPTION: Illustrates creating an OpenRouter API key using the PHP Guzzle HTTP client. It shows how to configure the POST request with body and headers.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/keys', [
  'body' => '{
  "name": "name"
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: Checking OpenRouter API Key Limits (TypeScript/Python)
DESCRIPTION: Demonstrates how to make a GET request to the `/api/v1/auth/key` endpoint to retrieve information about an API key's usage, credit limit, free tier status, and rate limit configuration. Requires an API key provided in the `Authorization` header. The response contains details about credits used, the credit limit, and the request rate limit.
SOURCE: https://openrouter.ai/docs/api-reference/limits.mdx#_snippet_0

LANGUAGE: typescript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/auth/key', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer {{API_KEY_REF}}',
  },
});
```

LANGUAGE: python
CODE:
```
import requests
import json

response = requests.get(
  url="https://openrouter.ai/api/v1/auth/key",
  headers={
    "Authorization": f"Bearer {{API_KEY_REF}}"
  }
)

print(json.dumps(response.json(), indent=2))
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with Unirest (Java)
DESCRIPTION: This Java snippet utilizes the Unirest library to make a concise GET request to the OpenRouter API keys endpoint. It demonstrates setting the Authorization header directly on the request builder.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/keys")
  .header("Authorization", "Bearer <token>")
  .asString();
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with PHP GuzzleHttp
DESCRIPTION: This PHP snippet uses the GuzzleHttp client library to perform a GET request to the OpenRouter API key endpoint. It includes the Authorization header in the request options and echoes the response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/key', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: Sending Chat Completion Request with Java Unirest
DESCRIPTION: Demonstrates sending a POST request to the OpenRouter chat completions endpoint in Java using the Unirest library, including setting headers and the request body.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/chat/completions")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"model\": \"openai/gpt-3.5-turbo\"\n}")
  .asString();
```

----------------------------------------

TITLE: Make POST Request with URLSession in Swift
DESCRIPTION: This Swift snippet uses URLSession to make an asynchronous POST request. It constructs the request with the appropriate URL, sets the Content-Type header, and serializes a dictionary into the JSON request body. The completion handler processes the response or error.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = ["code": "string"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/auth/keys")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse);
  }
})

dataTask.resume();
```

----------------------------------------

TITLE: Get Specific OpenRouter API Key
DESCRIPTION: Illustrates how to retrieve details for a single API key using a GET request to the `/api/v1/keys/{key_hash}` endpoint. Requires the specific key hash and the Provisioning API key in the header.
SOURCE: https://openrouter.ai/docs/features/provisioning-api-keys.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

PROVISIONING_API_KEY = "your-provisioning-key"
BASE_URL = "https://openrouter.ai/api/v1/keys"

# Get a specific key
key_hash = "<YOUR_KEY_HASH>"
response = requests.get(
    f"{BASE_URL}/{key_hash}",
    headers={
        "Authorization": f"Bearer {PROVISIONING_API_KEY}",
        "Content-Type": "application/json"
    }
)
```

LANGUAGE: typescript
CODE:
```
const PROVISIONING_API_KEY = 'your-provisioning-key';
const BASE_URL = 'https://openrouter.ai/api/v1/keys';

// Get a specific key
const keyHash = '<YOUR_KEY_HASH>';
const getKey = await fetch(`${BASE_URL}/${keyHash}`, {
  headers: {
    Authorization: `Bearer ${PROVISIONING_API_KEY}`,
    'Content-Type': 'application/json',
  },
});
```

----------------------------------------

TITLE: Getting Generation Metadata with C# RestSharp
DESCRIPTION: Provides an example of making a GET request to the generation endpoint in C# using the RestSharp library, setting the Authorization header.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/generation?id=id");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: HTTP Request to Create API Key
DESCRIPTION: Defines the HTTP method, endpoint, and required content type header for creating a new OpenRouter API key. This operation requires a Provisioning API key for authentication.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_0

LANGUAGE: http
CODE:
```
POST https://openrouter.ai/api/v1/keys
Content-Type: application/json
```

----------------------------------------

TITLE: Get Credits - Swift (URLSession)
DESCRIPTION: Shows how to make a GET request to the credits endpoint in Swift using URLSession, setting the Authorization header and handling the asynchronous response.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/credits")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Fetching Models with Swift URLSession
DESCRIPTION: Shows how to use Swift's standard URLSession to create a GET request, initiate a data task, and handle the response or error asynchronously.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/models")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Retrieve API Key - Ruby
DESCRIPTION: Provides a Ruby example using the net/http library to perform a GET request to the OpenRouter API key endpoint. It sets the Authorization header and prints the response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_15

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/key")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Get Credits - Go (net/http)
DESCRIPTION: Demonstrates how to perform a GET request to the credits endpoint in Go using the standard net/http package, setting the Authorization header and reading the response body.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/credits"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")
	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Create OpenRouter API Key using Java Unirest
DESCRIPTION: Example using the Java Unirest library to send a POST request to create an OpenRouter API key. It demonstrates setting headers and the request body concisely.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/keys")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"name\": \"name\"\n}")
  .asString();
```

----------------------------------------

TITLE: Create OpenRouter API Key using Go net/http
DESCRIPTION: Illustrates how to create an OpenRouter API key using Go's standard net/http package. It constructs the request with headers and body, sends it, and reads the response.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/keys"

	payload := strings.NewReader("{\n  \"name\": \"name\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with GuzzleHttp (PHP)
DESCRIPTION: This PHP code uses the GuzzleHttp client to send a GET request to retrieve the list of OpenRouter API keys. It shows how to pass the Authorization header within the request options array.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/keys', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
?>
```

----------------------------------------

TITLE: Sending Chat Completion Request with PHP GuzzleHttp
DESCRIPTION: Provides a PHP example using the Guzzle HTTP client to send a POST request to the OpenRouter chat completions API, configuring the request body and headers.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/chat/completions', [
  'body' => '{
  "model": "openai/gpt-3.5-turbo"
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
?>
```

----------------------------------------

TITLE: Make POST Request to OpenRouter API - PHP (Guzzle)
DESCRIPTION: Demonstrates making a POST request to the OpenRouter API /auth/keys endpoint using the Guzzle HTTP client library in PHP. It shows how to set the request body and headers within the client's request options.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_21

LANGUAGE: PHP
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/auth/keys', [
  'body' => '{\n  "code": "string"\n}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: POSTing to Auth Keys Endpoint with Ruby Net::HTTP
DESCRIPTION: Demonstrates how to make a POST request to the /api/v1/auth/keys endpoint using Ruby's standard `net/http` library. It handles SSL and sets the content type and body.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/auth/keys")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"code\": \"code\"\n}"

response = http.request(request)
puts response.read_body
```

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/auth/keys")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"code\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with Java Unirest
DESCRIPTION: This Java snippet utilizes the Unirest library to make a concise GET request to the OpenRouter API key endpoint. It adds the Authorization header and retrieves the response as a string.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/key")
  .header("Authorization", "Bearer <token>")
  .asString();
```

----------------------------------------

TITLE: Update OpenRouter API Key using JavaScript Fetch
DESCRIPTION: Shows how to update an OpenRouter API key using the Fetch API in JavaScript. It creates a PATCH request object with the target URL, method, headers (Authorization, Content-Type), and an empty string body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/keys/hash';
const options = {
  method: 'PATCH',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Getting Generation Metadata with PHP Guzzle
DESCRIPTION: Illustrates how to retrieve generation metadata in PHP using the Guzzle HTTP client, setting the Authorization header and echoing the response body.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/generation?id=id', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: Getting Models with Ruby net/http
DESCRIPTION: Demonstrates how to use Ruby's standard `net/http` library to make an HTTPS GET request to the OpenRouter API models endpoint and print the response body.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/models")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with Java Unirest
DESCRIPTION: This Java snippet utilizes the `Unirest` library to perform a concise GET request to the OpenRouter API. It includes the necessary `Authorization` header and retrieves the response body as a string.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/keys/hash")
  .header("Authorization", "Bearer <token>")
  .asString();
```

----------------------------------------

TITLE: Make POST Request with fetch in JavaScript
DESCRIPTION: This JavaScript snippet uses the browser's native `fetch` API to perform a POST request. It configures the request method, headers, and body. The code demonstrates how to handle the asynchronous response and potential errors using async/await and a try/catch block.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_12

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/auth/keys';
const options = {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: '{"code":"string"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Get Credits - Java (Unirest)
DESCRIPTION: Shows a concise Java example using the Unirest library to perform a GET request to the credits endpoint and set the Authorization header.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/credits")
  .header("Authorization", "Bearer <token>")
  .asString();
```

----------------------------------------

TITLE: Make POST Request to OpenRouter API - Go
DESCRIPTION: Shows how to perform a POST request to the OpenRouter API /auth/keys endpoint using Go's standard net/http package. It sets the content type header, includes a JSON body, and prints the response status and body.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_18

LANGUAGE: Go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/auth/keys"

	payload := strings.NewReader("{\n  \"code\": \"string\"\n}")
	req, _ := http.NewRequest("POST", url, payload)
	req.Header.Add("Content-Type", "application/json")
	res, _ := http.DefaultClient.Do(req)
	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)
	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Delete OpenRouter API Key using PHP Guzzle
DESCRIPTION: PHP example using the Guzzle HTTP client to send a DELETE request. Sets the Authorization header and echoes the response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('DELETE', 'https://openrouter.ai/api/v1/keys/hash', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: Update OpenRouter API Key using Ruby Net::HTTP
DESCRIPTION: Provides a Ruby example using the Net::HTTP library to update an OpenRouter API key. It sets up an HTTPS connection, creates a PATCH request object, adds the necessary headers, and sends the empty JSON body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/keys/hash")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Patch.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{}"

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Make POST Request to OpenRouter API - JavaScript
DESCRIPTION: Demonstrates how to make a POST request to the OpenRouter API /auth/keys endpoint using the Fetch API. It includes setting headers and the request body, handling the response, and catching errors.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_17

LANGUAGE: JavaScript
CODE:
```
const url = 'https://openrouter.ai/api/v1/auth/keys';
const options = {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: '{"code":"string"}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Create Coinbase Charge using Python Requests
DESCRIPTION: Shows how to make the POST request in Python using the `requests` library. It defines the URL, payload dictionary, and headers, then sends the request and prints the JSON response.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/credits/coinbase"

payload = {
    "amount": 1.1,
    "sender": "sender",
    "chain_id": 1
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())
```

----------------------------------------

TITLE: Delete OpenRouter API Key using Java Unirest
DESCRIPTION: Java example using the Unirest library to send a DELETE request. Sets the Authorization header and retrieves the response as a string.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.delete("https://openrouter.ai/api/v1/keys/hash")
  .header("Authorization", "Bearer <token>")
  .asString();
```

----------------------------------------

TITLE: Cancelling OpenRouter Stream with TypeScript
DESCRIPTION: This TypeScript snippet shows how to cancel a streaming chat completion request to the OpenRouter API using the Fetch API and an `AbortController`. The `signal` property of the `AbortController` is passed to the fetch request, allowing cancellation by calling `controller.abort()`.
SOURCE: https://openrouter.ai/docs/api-reference/streaming.mdx#_snippet_3

LANGUAGE: typescript
CODE:
```
const controller = new AbortController();

try {
  const response = await fetch(
    'https://openrouter.ai/api/v1/chat/completions',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${{{API_KEY_REF}}}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: '{{MODEL}}',
        messages: [{
          role: 'user',
          content: 'Write a story'
        }],
        stream: true
      }),
      signal: controller.signal
    },
  );

  // Process the stream...
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('Stream cancelled');
  } else {
    throw error;
  }
}

// To cancel the stream:
controller.abort();
```

----------------------------------------

TITLE: Make POST Request to OpenRouter API - C# (RestSharp)
DESCRIPTION: Illustrates how to make a POST request to the OpenRouter API /auth/keys endpoint using the RestSharp library in C#. It shows adding headers and the request body as a parameter with the appropriate content type.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_22

LANGUAGE: C#
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/auth/keys");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"code\": \"string\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Get Credits - C# (RestSharp)
DESCRIPTION: Provides a C# example using the RestSharp library to create and execute a GET request to the credits endpoint, adding the required Authorization header.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/credits");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - C# (RestSharp)
DESCRIPTION: Demonstrates how to use the RestSharp library in C# to create a client and execute a GET request to the OpenRouter API endpoint for listing model endpoints. Requires the RestSharp library.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/models/author/slug/endpoints");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Create OpenRouter API Key using C# RestSharp
DESCRIPTION: Example using the C# RestSharp library to send a POST request to create an OpenRouter API key. It demonstrates adding headers and the request body as a parameter.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/keys");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"name\": \"name\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Delete OpenRouter API Key using C# RestSharp
DESCRIPTION: C# example using the RestSharp library to send a DELETE request. Sets the Authorization header and executes the request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/keys/hash");
var request = new RestRequest(Method.DELETE);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Streaming Chat Completions with OpenRouter API (TypeScript)
DESCRIPTION: Shows how to stream responses from the OpenRouter chat completions API in TypeScript using the `fetch` API. It reads the response body as a stream, decodes chunks, and processes Server-Sent Events (SSE) lines to extract and print content deltas.
SOURCE: https://openrouter.ai/docs/api-reference/streaming.mdx#_snippet_1

LANGUAGE: TypeScript
CODE:
```
const question = 'How would you build the tallest building ever?';
const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${API_KEY_REF}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: '{{MODEL}}',
    messages: [{ role: 'user', content: question }],
    stream: true,
  }),
});

const reader = response.body?.getReader();
if (!reader) {
  throw new Error('Response body is not readable');
}

const decoder = new TextDecoder();
let buffer = '';

try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // Append new chunk to buffer
    buffer += decoder.decode(value, { stream: true });

    // Process complete lines from buffer
    while (true) {
      const lineEnd = buffer.indexOf('\n');
      if (lineEnd === -1) break;

      const line = buffer.slice(0, lineEnd).trim();
      buffer = buffer.slice(lineEnd + 1);

      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') break;

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices[0].delta.content;
          if (content) {
            console.log(content);
          }
        } catch (e) {
          // Ignore invalid JSON
        }
      }
    }
  }
} finally {
  reader.cancel();
}
```

----------------------------------------

TITLE: Create Coinbase Charge using cURL
DESCRIPTION: Provides a command-line example using `curl` to send a POST request to the Coinbase charge endpoint. It includes setting the Authorization and Content-Type headers and providing the JSON request body with amount, sender, and chain ID.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl -X POST https://openrouter.ai/api/v1/credits/coinbase \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
  "amount": 1.1,
  "sender": "sender",
  "chain_id": 1
}'
```

----------------------------------------

TITLE: Getting Models with C# RestSharp
DESCRIPTION: Demonstrates how to use the RestSharp library in C# to create a client, define a GET request for the models endpoint, and execute it.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/models");
var request = new RestRequest(Method.GET);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Update OpenRouter API Key using Java Unirest
DESCRIPTION: Demonstrates updating an OpenRouter API key in Java using the Unirest library. It constructs a PATCH request, sets the Authorization and Content-Type headers, and includes an empty string as the request body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.patch("https://openrouter.ai/api/v1/keys/hash")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{}")
  .asString();
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with C# RestClient
DESCRIPTION: This C# snippet demonstrates how to use the `RestClient` library to perform a GET request to the OpenRouter API. It sets the target URL, defines the GET method, adds the `Authorization` header, and executes the request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/keys/hash");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Sending Chat Completion Request with Go net/http
DESCRIPTION: Provides a Go example using the standard `net/http` package to construct and send a POST request to the OpenRouter chat completions API, including setting headers and reading the response body.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/chat/completions"

	payload := strings.NewReader("{\n  \"model\": \"openai/gpt-3.5-turbo\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")
	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Getting Generation Metadata with Python Requests
DESCRIPTION: Shows how to fetch generation metadata using Python's requests library, setting the Authorization header and passing the 'id' as a query parameter.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_2

LANGUAGE: python
CODE:
```
import requests

url = "https://openrouter.ai/api/v1/generation"

querystring = {"id":"id"}

headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
```

----------------------------------------

TITLE: Listing OpenRouter API Keys with RestClient (C#)
DESCRIPTION: This C# snippet uses the RestClient library (likely RestSharp) to make a GET request to the OpenRouter API keys endpoint. It demonstrates creating a client, a request, adding the Authorization header, and executing the request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/list-api-keys.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/keys");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Enabling Streaming for Structured Outputs
DESCRIPTION: Illustrates the minimal JSON payload required to enable streaming responses when requesting structured outputs from the OpenRouter API.
SOURCE: https://openrouter.ai/docs/features/structured-outputs.mdx#_snippet_4

LANGUAGE: typescript
CODE:
```
{
  "stream": true,
  "response_format": {
    "type": "json_schema",
    // ... rest of your schema
  }
}
```

----------------------------------------

TITLE: Retrieve API Key - Java (Unirest)
DESCRIPTION: Shows how to use the Unirest library in Java to make a concise GET request to the OpenRouter API key endpoint, including setting the Authorization header.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_16

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/key")
  .header("Authorization", "Bearer <token>")
  .asString();
```

----------------------------------------

TITLE: Make POST Request with RestClient in C#
DESCRIPTION: This C# snippet uses the RestClient library to perform a POST request to the OpenRouter API. It sets the Content-Type header and adds the JSON body as a request parameter with the RequestBody type. The executed response is stored.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/auth/keys");
var request = new RestRequest(Method.POST);
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"code\": \"string\"\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Defining Provider Error Metadata Structure - TypeScript
DESCRIPTION: This TypeScript type definition describes the structure of the 'metadata' field within the error response when an error originates from the model provider. It includes the provider's name and the raw error data received from the provider.
SOURCE: https://openrouter.ai/docs/api-reference/errors.mdx#_snippet_3

LANGUAGE: typescript
CODE:
```
type ProviderErrorMetadata = {
  provider_name: string; // The name of the provider that encountered the error
  raw: unknown; // The raw error from the provider
};
```

----------------------------------------

TITLE: Fetching Models with Java Unirest
DESCRIPTION: Shows a concise Java example using the Unirest library to perform a GET request to the OpenRouter API models endpoint and retrieve the response as a string.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/models")
  .asString();
```

----------------------------------------

TITLE: Sending Completions Request with Java Unirest
DESCRIPTION: Example using the Java Unirest library to fluently construct and send a POST request to the OpenRouter completions endpoint.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/completions")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"model\": \"model\",\n  \"prompt\": \"prompt\"\n}")
  .asString();
```

----------------------------------------

TITLE: Create Coinbase Charge using Go net/http
DESCRIPTION: Shows how to make the POST request in Go using the standard `net/http` package. It constructs the request with the URL, method, and request body (read from a string), adds headers, executes the request, and prints the response status and body.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/credits/coinbase"

	payload := strings.NewReader("{\n  \"amount\": 1.1,\n  \"sender\": \"sender\",\n  \"chain_id\": 1\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Retrieve API Key - C# (RestClient)
DESCRIPTION: Provides a C# example using the RestClient library to make a GET request to the OpenRouter API key endpoint. It adds the Authorization header and executes the request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_18

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/key");
var request = new RestRequest(Method.GET);
request.AddHeader("Authorization", "Bearer <token>");
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Excluding Providers by Data Policy (deny)
DESCRIPTION: This example demonstrates how to exclude providers that may store user data by setting the `data_collection` field to `deny` within the `provider` object of the chat completions request body.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_6

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: 'Hello' }],
    provider: {
      data_collection: 'deny', // or "allow"
    },
  }),
});
```

----------------------------------------

TITLE: Sending Completions Request with Swift URLSession
DESCRIPTION: Example using Swift's URLSession to create and initiate a POST request to the OpenRouter completions endpoint with headers and a JSON-serialized request body.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = [
  "model": "model",
  "prompt": "prompt"
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/completions")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Specifying Fallback Models (JSON)
DESCRIPTION: Shows how to use the `models` parameter to provide a list of fallback models. If the primary model fails, OpenRouter will attempt to use the models in this list in order.
SOURCE: https://openrouter.ai/docs/features/model-routing.mdx#_snippet_1

LANGUAGE: json
CODE:
```
{
  "models": ["anthropic/claude-3.5-sonnet", "gryphe/mythomax-l2-13b"],
  ... // Other params
}
```

----------------------------------------

TITLE: Initializing PydanticAI Agent with OpenRouter (Python)
DESCRIPTION: Demonstrates how to configure a PydanticAI Agent to use OpenRouter models. It shows setting the base URL to OpenRouter's API endpoint and providing an API key. The example then runs a simple prompt.
SOURCE: https://openrouter.ai/docs/community/frameworks.mdx#_snippet_5

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

model = OpenAIModel(
    "anthropic/claude-3.5-sonnet",  # or any other OpenRouter model
    base_url="https://openrouter.ai/api/v1",
    api_key="sk-or-...",
)

agent = Agent(model)
result = await agent.run("What is the meaning of life?")
print(result)
```

----------------------------------------

TITLE: Installing OpenRouter AI SDK Provider (Bash)
DESCRIPTION: Provides the command to install the `@openrouter/ai-sdk-provider` package using npm, which is required to integrate OpenRouter with the Vercel AI SDK.
SOURCE: https://openrouter.ai/docs/community/frameworks.mdx#_snippet_6

LANGUAGE: bash
CODE:
```
npm install @openrouter/ai-sdk-provider
```

----------------------------------------

TITLE: Fetching OpenRouter API Key with Swift URLSession
DESCRIPTION: This Swift snippet uses the Foundation framework's URLSession to create and execute a GET request to the OpenRouter API key endpoint asynchronously. It sets the Authorization header and handles the response or error in a completion handler.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/key")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Calling OpenRouter API Excluding Reasoning Output (Python)
DESCRIPTION: Illustrates making a chat completion request to the OpenRouter API in Python using `requests`, configuring the `reasoning` parameter with `exclude: true`. This tells the model to perform internal reasoning (optionally specifying `effort`) but not include the reasoning output in the final response. It then prints only the content.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_4

LANGUAGE: python
CODE:
```
import requests
import json

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {{API_KEY_REF}}",
    "Content-Type": "application/json"
}
payload = {
    "model": "{{MODEL}}",
    "messages": [
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    "reasoning": {
        "effort": "high",
        "exclude": true  # Use reasoning but don't include it in the response
    }
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
# No reasoning field in the response
print(response.json()['choices'][0]['message']['content'])
```

----------------------------------------

TITLE: Make POST Request with GuzzleHttp in PHP
DESCRIPTION: This snippet demonstrates how to make a POST request to the OpenRouter API using the GuzzleHttp client in PHP. It sets the Content-Type header to application/json and includes a JSON body containing a 'code' field. The response body is then printed.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/auth/keys', [
  'body' => '{
  "code": "string"
}',
  'headers' => [
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: HTTP Request Method and Endpoint
DESCRIPTION: Specifies the HTTP method (POST) and the target URL for creating a Coinbase charge using the OpenRouter API. It also indicates the required content type for the request body.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_0

LANGUAGE: http
CODE:
```
POST https://openrouter.ai/api/v1/credits/coinbase
Content-Type: application/json
```

----------------------------------------

TITLE: Retrieving Models with Go net/http
DESCRIPTION: Provides a Go example using the standard `net/http` package to perform a GET request, read the response body, and print both the response status and body.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/models"

	req, _ := http.NewRequest("GET", url, nil)

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Using Fallback Models with OpenAI SDK (Python)
DESCRIPTION: Example using the OpenAI SDK in Python to configure fallback models via the `extra_body` parameter when making a chat completion request to OpenRouter. The primary model is specified in `model`, and fallbacks are listed in `models`.
SOURCE: https://openrouter.ai/docs/features/model-routing.mdx#_snippet_3

LANGUAGE: python
CODE:
```
from openai import OpenAI

openai_client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key={{API_KEY_REF}},
)

completion = openai_client.chat.completions.create(
    model="openai/gpt-4o",
    extra_body={
        "models": ["anthropic/claude-3.5-sonnet", "gryphe/mythomax-l2-13b"]
    },
    messages=[
        {
            "role": "user",
            "content": "What is the meaning of life?"
        }
    ]
)

print(completion.choices[0].message.content)
```

----------------------------------------

TITLE: Update OpenRouter API Key using Go net/http
DESCRIPTION: Illustrates updating an OpenRouter API key using Go's standard net/http package. It constructs a PATCH request with the URL, an empty request body, and adds the required Authorization and Content-Type headers.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/keys/hash"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("PATCH", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Calling OpenRouter API with Reasoning Max Tokens (TypeScript)
DESCRIPTION: Shows how to use the `openai` library with the OpenRouter API base URL in TypeScript to request a chat completion, setting the maximum tokens (or approximate effort) for the model's reasoning using the `reasoning.max_tokens` parameter. It logs the reasoning and content from the response.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_3

LANGUAGE: typescript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: '{{API_KEY_REF}}',
});

async function getResponseWithReasoning() {
  const response = await openai.chat.completions.create({
    model: '{{MODEL}}',
    messages: [
      {
        role: 'user',
        content: "How would you build the world's tallest skyscraper?",
      },
    ],
    reasoning: {
      max_tokens: 2000, // Allocate 2000 tokens (or approximate effort) for reasoning
    },
  });

  console.log('REASONING:', response.choices[0].message.reasoning);
  console.log('CONTENT:', response.choices[0].message.content);
}

getResponseWithReasoning();
```

----------------------------------------

TITLE: Delete OpenRouter API Key using Go net/http
DESCRIPTION: Go example demonstrating how to create and send a DELETE request using the standard `net/http` package. Sets the Authorization header and reads the response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/keys/hash"

	req, _ := http.NewRequest("DELETE", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: API Request: Sort by Price (Floor Shortcut) - TS/JS
DESCRIPTION: Illustrates using the `:floor` shortcut appended to the model slug (`meta-llama/llama-3.1-70b-instruct:floor`) as a shorthand for setting `provider.sort` to "price", prioritizing providers with the lowest price.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_2

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'meta-llama/llama-3.1-70b-instruct:floor',
    messages: [{ role: 'user', content: 'Hello' }]
  })
});
```

----------------------------------------

TITLE: Fetch OpenRouter API Key Details with Go net/http
DESCRIPTION: This Go snippet demonstrates how to use the standard `net/http` package to perform a GET request to the OpenRouter API. It constructs a request, adds the `Authorization` header, executes it, and prints the response status and body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/keys/hash"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: API Request: Sort by Throughput (Nitro Shortcut) - TS/JS
DESCRIPTION: Shows how to use the `:nitro` shortcut appended to the model slug (`meta-llama/llama-3.1-70b-instruct:nitro`) to achieve the same effect as setting `provider.sort` to "throughput", prioritizing providers with higher throughput.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_1

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'meta-llama/llama-3.1-70b-instruct:nitro',
    messages: [{ role: 'user', content: 'Hello' }]
  })
});
```

----------------------------------------

TITLE: Create OpenRouter API Key
DESCRIPTION: Shows how to create a new API key by sending a POST request to the `/api/v1/keys/` endpoint. Explains how to include the Provisioning API key and provide key details like name, label, and an optional limit in the request body.
SOURCE: https://openrouter.ai/docs/features/provisioning-api-keys.mdx#_snippet_1

LANGUAGE: python
CODE:
```
import requests

PROVISIONING_API_KEY = "your-provisioning-key"
BASE_URL = "https://openrouter.ai/api/v1/keys"

# Create a new API key
response = requests.post(
    f"{BASE_URL}/",
    headers={
        "Authorization": f"Bearer {PROVISIONING_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "name": "Customer Instance Key",
        "label": "customer-123",
        "limit": 1000  # Optional credit limit
    }
)
```

LANGUAGE: typescript
CODE:
```
const PROVISIONING_API_KEY = 'your-provisioning-key';
const BASE_URL = 'https://openrouter.ai/api/v1/keys';

// Create a new API key
const createKey = await fetch(`${BASE_URL}`, {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${PROVISIONING_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'Customer Instance Key',
    label: 'customer-123',
    limit: 1000, // Optional credit limit
  }),
});
```

----------------------------------------

TITLE: Update OpenRouter API Key using Swift URLSession
DESCRIPTION: Illustrates updating an OpenRouter API key in Swift using URLSession. It configures a NSMutableURLRequest with the PATCH method, sets the Authorization and Content-Type headers, and attaches an empty JSON object as the HTTP body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = [] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/keys/hash")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "PATCH"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Enabling Middle-Out Transform in OpenRouter Request
DESCRIPTION: This snippet demonstrates how to include the 'transforms' parameter in the OpenRouter API request body to enable the 'middle-out' compression strategy. This helps manage prompt length and message count when interacting with AI models.
SOURCE: https://openrouter.ai/docs/features/message-transforms.mdx#_snippet_0

LANGUAGE: typescript
CODE:
```
{
  transforms: ["middle-out"], // Compress prompts that are > context size.
  messages: [...],
  model // Works with any model
}
```

----------------------------------------

TITLE: Delete OpenRouter API Key using Swift URLSession
DESCRIPTION: Swift example using `URLSession` to create and send a DELETE request. Sets the Authorization header and handles the response asynchronously.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/keys/hash")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "DELETE"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - Java (Unirest)
DESCRIPTION: Shows a concise example using the Unirest library in Java to perform a GET request to the OpenRouter API endpoint for listing model endpoints. It retrieves the response as a String. Requires the Unirest Java library.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/models/author/slug/endpoints")
  .asString();
```

----------------------------------------

TITLE: Azure API Key Configuration Structure (Multiple)
DESCRIPTION: Shows how to provide configurations for multiple Azure AI Services models by using a JSON array. Each object in the array follows the single configuration structure, allowing different OpenRouter model slugs to map to specific Azure deployments.
SOURCE: https://openrouter.ai/docs/use-cases/byok.mdx#_snippet_1

LANGUAGE: json
CODE:
```
[
  {
    "model_slug": "mistralai/mistral-large",
    "endpoint_url": "https://example-project.openai.azure.com/openai/deployments/mistral-large/chat/completions?api-version=2024-08-01-preview",
    "api_key": "your-azure-api-key",
    "model_id": "mistral-large"
  },
  {
    "model_slug": "openai/gpt-4o",
    "endpoint_url": "https://example-project.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview",
    "api_key": "your-azure-api-key",
    "model_id": "gpt-4o"
  }
]
```

----------------------------------------

TITLE: Create OpenRouter API Key using Swift URLSession
DESCRIPTION: Shows how to create an OpenRouter API key using Swift's URLSession. It sets up the request with headers and body data and initiates the network task.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = ["name": "name"] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/keys")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: API Request: Order Specific Providers (Fallbacks Enabled) - TS/JS
DESCRIPTION: Demonstrates how to specify a preferred order of providers (e.g., `['OpenAI', 'Together']`) using the `provider.order` field. OpenRouter will try these providers in sequence and fall back to its normal list if none are available.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_3

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'mistralai/mixtral-8x7b-instruct',
    messages: [{ role: 'user', content: 'Hello' }],
    provider: {
      order: ['OpenAI', 'Together']
    }
  })
});
```

----------------------------------------

TITLE: API Request: Order Specific Providers (Fallbacks Disabled) - TS/JS
DESCRIPTION: Shows how to use the `provider.order` field to specify a sequence of providers while also setting `provider.allow_fallbacks` to `false`. This ensures the request will only be routed to the specified providers and will fail if none of them are available.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_4

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'mistralai/mixtral-8x7b-instruct',
    messages: [{ role: 'user', content: 'Hello' }],
    provider: {
      order: ['OpenAI', 'Together'],
      allow_fallbacks: false
    }
  })
});
```

----------------------------------------

TITLE: Get Credits - PHP (GuzzleHttp)
DESCRIPTION: Demonstrates how to use the GuzzleHttp client library in PHP to make a GET request to the credits endpoint, including setting the Authorization header and echoing the response body.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/credits', [
  'headers' => [
    'Authorization' => 'Bearer <token>',
  ],
]);

echo $response->getBody();

```

----------------------------------------

TITLE: Making Follow-up OpenRouter API Call with Annotations (JavaScript)
DESCRIPTION: This JavaScript snippet demonstrates how to make a follow-up API call to the OpenRouter chat completions endpoint. It checks for existing file annotations from a previous response and includes them in the subsequent request body, allowing the API to process further questions about the document without requiring the file data to be sent again. This optimizes performance and cost for document-based interactions.
SOURCE: https://openrouter.ai/docs/features/images-and-pdfs.mdx#_snippet_5

LANGUAGE: JavaScript
CODE:
```
if (initialData.choices && initialData.choices.length > 0) {
  if (initialData.choices[0].message.annotations) {
    fileAnnotations = initialData.choices[0].message.annotations;
  }
}

// Follow-up request using the annotations (without sending the PDF again)
if (fileAnnotations) {
  const followUpResponse = await fetch(
    'https://openrouter.ai/api/v1/chat/completions',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${API_KEY_REF}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: '{{MODEL}}',
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: 'What are the main points in this document?',
              },
              {
                type: 'file',
                file: {
                  filename: 'document.pdf',
                  file_data: base64PDF,
                },
              },
            ],
          },
          {
            role: 'assistant',
            content: 'The document contains information about...',
            annotations: fileAnnotations,
          },
          {
            role: 'user',
            content: 'Can you elaborate on the second point?',
          },
        ],
      }),
    },
  );

  const followUpData = await followUpResponse.json();
  console.log(followUpData);
}
```

----------------------------------------

TITLE: Make POST Request with net/http in Go
DESCRIPTION: This Go snippet demonstrates how to make a POST request using the standard library's `net/http` package. It creates a request with a string reader for the JSON body, sets the Content-Type header, and executes the request using the default client. The response status and body are then printed.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_13

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/auth/keys"

	payload := strings.NewReader("{\n  \"code\": \"string\"\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Delete OpenRouter API Key using Ruby Net::HTTP
DESCRIPTION: Ruby example using the `net/http` library to send a DELETE request. Sets the Authorization header and prints the response body.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/keys/hash")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Delete.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: AWS Bedrock API Key Configuration JSON
DESCRIPTION: This JSON object defines the required structure for providing AWS credentials to OpenRouter for accessing Amazon Bedrock. It includes the AWS access key ID, secret access key, and the AWS region where Bedrock models are located.
SOURCE: https://openrouter.ai/docs/use-cases/byok.mdx#_snippet_2

LANGUAGE: json
CODE:
```
{
  "accessKeyId": "your-aws-access-key-id",
  "secretAccessKey": "your-aws-secret-access-key",
  "region": "your-aws-region"
}
```

----------------------------------------

TITLE: API Request: Require Parameter Support (JSON Format) - TS/JS
DESCRIPTION: Explains how to use the `provider.require_parameters` field set to `true` to restrict the request to only providers that explicitly support all parameters included in the request body, such as `response_format: { type: 'json_object' }`.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_5

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: 'Hello' }],
    provider: {
      require_parameters: true
    },
    response_format: { type: 'json_object' }
  })
});
```

----------------------------------------

TITLE: Example AWS IAM Policy for Bedrock Access
DESCRIPTION: This JSON object provides an example IAM policy granting the minimum necessary permissions (`bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`) for an AWS user or role to interact with Amazon Bedrock models via OpenRouter.
SOURCE: https://openrouter.ai/docs/use-cases/byok.mdx#_snippet_3

LANGUAGE: json
CODE:
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

----------------------------------------

TITLE: Reuse PDF Annotations in API Calls
DESCRIPTION: Demonstrates how to make an initial API request with a PDF document, extract file annotations from the response, and then include these annotations in subsequent requests instead of re-sending the full PDF data. This process avoids re-parsing the document.
SOURCE: https://openrouter.ai/docs/features/images-and-pdfs.mdx#_snippet_4

LANGUAGE: python
CODE:
```
import requests
import json
import base64
from pathlib import Path

# First, encode and send the PDF
def encode_pdf_to_base64(pdf_path):
    with open(pdf_path, "rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode('utf-8')

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY_REF}",
    "Content-Type": "application/json"
}

# Read and encode the PDF
pdf_path = "path/to/your/document.pdf"
base64_pdf = encode_pdf_to_base64(pdf_path)
data_url = f"data:application/pdf;base64,{base64_pdf}"

# Initial request with the PDF
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "What are the main points in this document?"
            },
            {
                "type": "file",
                "file": {
                    "filename": "document.pdf",
                    "file_data": data_url
                }
            },
        ]
    }
]

payload = {
    "model": "{{MODEL}}",
    "messages": messages
}

response = requests.post(url, headers=headers, json=payload)
response_data = response.json()

# Store the annotations from the response
file_annotations = None
if response_data.get("choices") and len(response_data["choices"]) > 0:
    if "annotations" in response_data["choices"][0]["message"]:
        file_annotations = response_data["choices"][0]["message"]["annotations"]

# Follow-up request using the annotations (without sending the PDF again)
if file_annotations:
    follow_up_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What are the main points in this document?"
                },
                {
                    "type": "file",
                    "file": {
                        "filename": "document.pdf",
                        "file_data": data_url
                    }
                }
            ]
        },
        {
            "role": "assistant",
            "content": "The document contains information about...",
            "annotations": file_annotations
        },
        {
            "role": "user",
            "content": "Can you elaborate on the second point?"
        }
    ]

    follow_up_payload = {
        "model": "{{MODEL}}",
        "messages": follow_up_messages
    }

    follow_up_response = requests.post(url, headers=headers, json=follow_up_payload)
    print(follow_up_response.json())
    
```

LANGUAGE: typescript
CODE:
```
import fs from 'fs/promises';
import { fetch } from 'node-fetch';

async function encodePDFToBase64(pdfPath: string): Promise<string> {
  const pdfBuffer = await fs.readFile(pdfPath);
  const base64PDF = pdfBuffer.toString('base64');
  return `data:application/pdf;base64,${base64PDF}`;
}

// Initial request with the PDF
async function processDocument() {
  // Read and encode the PDF
  const pdfPath = 'path/to/your/document.pdf';
  const base64PDF = await encodePDFToBase64(pdfPath);

  const initialResponse = await fetch(
    'https://openrouter.ai/api/v1/chat/completions',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${API_KEY_REF}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: '{{MODEL}}',
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text: 'What are the main points in this document?',
              },
              {
                type: 'file',
                file: {
                  filename: 'document.pdf',
                  file_data: base64PDF,
                },
              },
            ],
          },
        ],
      }),
    },
  );

  const initialData = await initialResponse.json();

  // Store the annotations from the response
  let fileAnnotations = null;

```

----------------------------------------

TITLE: Ignoring Specific Providers (Azure)
DESCRIPTION: This example shows how to exclude specific providers, such as 'Azure', from being used for a chat completions request by listing them in the `ignore` array within the `provider` object.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_9

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'openai/gpt-4o',
    messages: [{ role: 'user', content: 'Hello' }],
    provider: {
      ignore: ['Azure'],
    },
  }),
});
```

----------------------------------------

TITLE: Allowing Only Specific Providers (Azure)
DESCRIPTION: This example demonstrates how to restrict a chat completions request to use only specific providers, in this case 'Azure', by listing them in the `only` array within the `provider` object.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_8

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'openai/gpt-4o',
    messages: [{ role: 'user', content: 'Hello' }],
    provider: {
      only: ['Azure'],
    },
  }),
});
```

----------------------------------------

TITLE: Update OpenRouter API Key using C# RestSharp
DESCRIPTION: Provides a C# example using the RestSharp library to update an OpenRouter API key. It creates a RestClient for the endpoint, sets the method to PATCH, adds the Authorization and Content-Type headers, and includes the empty JSON body as a request parameter.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/keys/hash");
var request = new RestRequest(Method.PATCH);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: API Request: Sort by Throughput (Provider Option) - TS/JS
DESCRIPTION: Demonstrates how to explicitly prioritize providers based on throughput by setting the `sort` field to "throughput" within the `provider` object in the API request body. This disables OpenRouter's default load balancing.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_0

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'meta-llama/llama-3.1-70b-instruct',
    messages: [{ role: 'user', content: 'Hello' }],
    provider: {
      sort: 'throughput'
    }
  })
});
```

----------------------------------------

TITLE: Making OpenRouter API Call with High Reasoning Effort
DESCRIPTION: Demonstrates how to make a chat completions API call to OpenRouter using the `reasoning.effort` parameter set to "high". Examples are provided in Python using the `requests` library and TypeScript using the `openai` library configured for OpenRouter, showing how to include the reasoning parameter and access the returned reasoning output.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_1

LANGUAGE: python
CODE:
```
import requests
import json

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {{API_KEY_REF}}",
    "Content-Type": "application/json"
}
payload = {
    "model": "{{MODEL}}",
    "messages": [
        {"role": "user", "content": "How would you build the world's tallest skyscraper?"}
    ],
    "reasoning": {
        "effort": "high"  # Use high reasoning effort
    }
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.json()['choices'][0]['message']['reasoning'])
```

LANGUAGE: typescript
CODE:
```
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: '{{API_KEY_REF}}',
});

async function getResponseWithReasoning() {
  const response = await openai.chat.completions.create({
    model: '{{MODEL}}',
    messages: [
      {
        role: 'user',
        content: "How would you build the world's tallest skyscraper?",
      },
    ],
    reasoning: {
      effort: 'high', // Use high reasoning effort
    },
  });

  console.log('REASONING:', response.choices[0].message.reasoning);
  console.log('CONTENT:', response.choices[0].message.content);
}

getResponseWithReasoning();
```

----------------------------------------

TITLE: Listing Models with PHP GuzzleHttp
DESCRIPTION: Provides a PHP example using the GuzzleHttp client library to make a GET request to the OpenRouter API models endpoint and echo the response body.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/models');

echo $response->getBody();
?>
```

----------------------------------------

TITLE: Update OpenRouter API Key using PHP Guzzle
DESCRIPTION: Shows a PHP example using the Guzzle HTTP client to update an OpenRouter API key. It initiates a PATCH request to the specified URL, providing the empty body and required headers (Authorization, Content-Type) in an options array.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('PATCH', 'https://openrouter.ai/api/v1/keys/hash', [
  'body' => '{}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: GET Credits Endpoint - HTTP
DESCRIPTION: Shows the basic HTTP GET request method and URL for accessing the OpenRouter API credits endpoint.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_0

LANGUAGE: http
CODE:
```
GET https://openrouter.ai/api/v1/credits
```

----------------------------------------

TITLE: Sending Completions Request with PHP Guzzle
DESCRIPTION: Example using the PHP Guzzle HTTP client to send a POST request to the OpenRouter completions endpoint with headers and a request body.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/completions', [
  'body' => '{
  "model": "model",
  "prompt": "prompt"
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: Defining Moderation Error Metadata Structure - TypeScript
DESCRIPTION: This TypeScript type definition specifies the structure of the 'metadata' field within the error response when a moderation error occurs. It includes details like the reasons for flagging, the flagged input segment, and the provider/model involved.
SOURCE: https://openrouter.ai/docs/api-reference/errors.mdx#_snippet_2

LANGUAGE: typescript
CODE:
```
type ModerationErrorMetadata = {
  reasons: string[]; // Why your input was flagged
  flagged_input: string; // The text segment that was flagged, limited to 100 characters. If the flagged input is longer than 100 characters, it will be truncated in the middle and replaced with ...
  provider_name: string; // The name of the provider that requested moderation
  model_slug: string;
};
```

----------------------------------------

TITLE: Sending Chat Completion Request with Ruby Net::HTTP
DESCRIPTION: Shows how to make a POST request to the OpenRouter chat completions API in Ruby using the `net/http` library, setting up the request with headers and body and processing the response.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/chat/completions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"model\": \"openai/gpt-3.5-turbo\"\n}"

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Send Base64 Image to OpenRouter API
DESCRIPTION: This snippet demonstrates how to read a local image file, encode it into a base64 data URL, and include it in the 'content' array of a chat completion request payload sent to the OpenRouter API. It requires libraries for file handling, base64 encoding, and making HTTP requests.
SOURCE: https://openrouter.ai/docs/features/images-and-pdfs.mdx#_snippet_1

LANGUAGE: python
CODE:
```
import requests
import json
import base64
from pathlib import Path

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY_REF}",
    "Content-Type": "application/json"
}

# Read and encode the image
image_path = "path/to/your/image.jpg"
base64_image = encode_image_to_base64(image_path)
data_url = f"data:image/jpeg;base64,{base64_image}"

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "What's in this image?"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": data_url
                }
            }
        ]
    }
]

payload = {
    "model": "{{MODEL}}",
    "messages": messages
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

LANGUAGE: typescript
CODE:
```
async function encodeImageToBase64(imagePath: string): Promise<string> {
  const imageBuffer = await fs.promises.readFile(imagePath);
  const base64Image = imageBuffer.toString('base64');
  return `data:image/jpeg;base64,${base64Image}`;
}

// Read and encode the image
const imagePath = 'path/to/your/image.jpg';
const base64Image = await encodeImageToBase64(imagePath);

const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${API_KEY_REF}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: '{{MODEL}}',
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'text',
            text: "What's in this image?",
          },
          {
            type: 'image_url',
            image_url: {
              url: base64Image,
            },
          },
        ],
      },
    ],
  }),
});

const data = await response.json();
console.log(data);
```

----------------------------------------

TITLE: GET Request to List Models (HTTP)
DESCRIPTION: Shows the basic HTTP GET request structure to retrieve the list of available models from the OpenRouter API.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_0

LANGUAGE: http
CODE:
```
GET https://openrouter.ai/api/v1/models
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - Ruby (net/http)
DESCRIPTION: Illustrates how to use Ruby's standard `uri` and `net/http` libraries to construct and send a GET request to the OpenRouter API endpoint for listing model endpoints. It prints the response body. Requires standard Ruby libraries.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/models/author/slug/endpoints")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - Swift (URLSession)
DESCRIPTION: Shows how to use Swift's Foundation framework with `URLSession` to create and execute a GET request to the OpenRouter API endpoint for listing model endpoints. It handles the asynchronous response and prints the HTTP response or any errors. Requires the Foundation framework.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/models/author/slug/endpoints")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: POSTing to Auth Keys Endpoint with Java Unirest
DESCRIPTION: Shows how to perform a POST request to the /api/v1/auth/keys endpoint using the Java Unirest library. It sets the header and sends the request body as a string.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/auth/keys")
  .header("Content-Type", "application/json")
  .body("{\n  \"code\": \"code\"\n}")
  .asString();
```

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.post("https:
```

----------------------------------------

TITLE: Sending Completions Request with Ruby Net::HTTP
DESCRIPTION: Example using Ruby's standard Net::HTTP library to create and send a POST request to the OpenRouter completions endpoint over SSL.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/completions")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"model\": \"model\",\n  \"prompt\": \"prompt\"\n}"

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Getting Generation Metadata with Java Unirest
DESCRIPTION: Demonstrates how to make a GET request to the generation endpoint in Java using the Unirest library, setting the Authorization header and getting the response as a string.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.get("https://openrouter.ai/api/v1/generation?id=id")
  .header("Authorization", "Bearer <token>")
  .asString();
```

----------------------------------------

TITLE: Getting Generation Metadata with JavaScript Fetch
DESCRIPTION: Illustrates how to retrieve generation metadata using JavaScript's fetch API, including setting the Authorization header and handling the response.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/generation?id=id';
const options = {method: 'GET', headers: {Authorization: 'Bearer <token>'}};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Enabling Usage Accounting in Request Body (JSON)
DESCRIPTION: Demonstrates how to include the 'usage' parameter in the API request payload to enable usage accounting for chat completions.
SOURCE: https://openrouter.ai/docs/use-cases/usage-accounting.mdx#_snippet_0

LANGUAGE: json
CODE:
```
{
  "model": "your-model",
  "messages": [],
  "usage": {
    "include": true
  }
}
```

----------------------------------------

TITLE: Getting Generation Metadata with Go net/http
DESCRIPTION: Provides an example of making a GET request to the generation endpoint in Go using the standard net/http package, setting the Authorization header and reading the response body.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/generation?id=id"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Extract Authorization Code (TypeScript)
DESCRIPTION: TypeScript code snippet to extract the authorization `code` parameter from the current page's URL query string after the user is redirected back from OpenRouter.
SOURCE: https://openrouter.ai/docs/use-cases/oauth-pkce.mdx#_snippet_4

LANGUAGE: typescript
CODE:
```
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
```

----------------------------------------

TITLE: Make POST Request to OpenRouter API - Swift
DESCRIPTION: Shows how to perform a POST request to the OpenRouter API /auth/keys endpoint using Swift's URLSession. It constructs the request with headers and a JSON body, then uses a data task to execute it asynchronously.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_23

LANGUAGE: Swift
CODE:
```
import Foundation

let headers = ["Content-Type": "application/json"]
let parameters = ["code": "string"] as [String : Any]

let postData = try? JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/auth/keys")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - Go (net/http)
DESCRIPTION: Provides a Go example using the standard `net/http` package to create and execute a GET request to the OpenRouter API endpoint for listing model endpoints. It reads and prints the response body. Requires standard Go libraries.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_4

LANGUAGE: go
CODE:
```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://openrouter.ai/api/v1/models/author/slug/endpoints"

	req, _ := http.NewRequest("GET", url, nil)

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

----------------------------------------

TITLE: Make POST Request to OpenRouter API - Ruby
DESCRIPTION: Illustrates how to make a POST request to the OpenRouter API /auth/keys endpoint using Ruby's standard net/http library. It handles SSL, sets the content type header, includes the JSON body, and prints the response body.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_19

LANGUAGE: Ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/auth/keys")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"code\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Azure API Key Configuration Structure (Single)
DESCRIPTION: Defines the required JSON structure for configuring a single Azure AI Services API key within OpenRouter's BYOK settings. It includes fields for the OpenRouter model slug, the Azure endpoint URL, the API key, and the Azure model deployment ID.
SOURCE: https://openrouter.ai/docs/use-cases/byok.mdx#_snippet_0

LANGUAGE: json
CODE:
```
{
  "model_slug": "the-openrouter-model-slug",
  "endpoint_url": "https://<resource>.services.ai.azure.com/deployments/<model-id>/chat/completions?api-version=<api-version>",
  "api_key": "your-azure-api-key",
  "model_id": "the-azure-model-id"
}
```

----------------------------------------

TITLE: Getting Generation Metadata with Ruby Net::HTTP
DESCRIPTION: Shows how to fetch generation metadata in Ruby using the Net::HTTP library, including setting the Authorization header and reading the response body.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/generation?id=id")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Getting Generation Metadata with Swift URLSession
DESCRIPTION: Shows how to fetch generation metadata in Swift using URLSession, setting the Authorization header and handling the asynchronous response.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = ["Authorization": "Bearer <token>"]

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/generation?id=id")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "GET"
request.allHTTPHeaderFields = headers

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: List Model Endpoints - OpenRouter API - PHP (Guzzle)
DESCRIPTION: Provides a PHP example using the Guzzle HTTP client library to make a GET request to the OpenRouter API endpoint for listing model endpoints and output the response body. Requires the Guzzle library.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://openrouter.ai/api/v1/models/author/slug/endpoints');

echo $response->getBody();
```

----------------------------------------

TITLE: Executing MCP Client and Interacting (Bash)
DESCRIPTION: This Bash snippet demonstrates how to run the `mcp-client.py` script from the command line. It shows the initial connection messages, the prompt for user input, and a sample interaction where the user queries about installed software, leading to tool calls and a final result.
SOURCE: https://openrouter.ai/docs/use-cases/mcp-servers.mdx#_snippet_4

LANGUAGE: bash
CODE:
```
% python mcp-client.py

Secure MCP Filesystem Server running on stdio
Allowed directories: [ '/Applications' ]

Connected to server with tools: ['read_file', 'read_multiple_files', 'write_file'...]

MCP Client Started!
Type your queries or 'quit' to exit.

Query: Do I have microsoft office installed?

Result:
[Calling tool list_allowed_directories with args {}]
I can check if Microsoft Office is installed in the Applications folder:

Query: continue

Result:
[Calling tool search_files with args {'path': '/Applications', 'pattern': 'Microsoft'}]
Now let me check specifically for Microsoft Office applications:

Query: continue

Result:
I can see from the search results that Microsoft Office is indeed installed on your system.
The search found the following main Microsoft Office applications:

1. Microsoft Excel - /Applications/Microsoft Excel.app
2. Microsoft PowerPoint - /Applications/Microsoft PowerPoint.app
3. Microsoft Word - /Applications/Microsoft Word.app
4. OneDrive - /Applications/OneDrive.app (which includes Microsoft SharePoint integration)
```

----------------------------------------

TITLE: Defining OpenRouter Completions Response Type (TypeScript)
DESCRIPTION: Defines the main TypeScript type `Response` for the OpenRouter completions API, detailing its structure including choices, creation timestamp, model, object type, optional system fingerprint, and usage data.
SOURCE: https://openrouter.ai/docs/api-reference/overview.mdx#_snippet_3

LANGUAGE: TypeScript
CODE:
```
// Definitions of subtypes are below
type Response = {
  id: string;
  // Depending on whether you set "stream" to "true" and
  // whether you passed in "messages" or a "prompt", you
  // will get a different output shape
  choices: (NonStreamingChoice | StreamingChoice | NonChatChoice)[];
  created: number; // Unix timestamp
  model: string;
  object: 'chat.completion' | 'chat.completion.chunk';

  system_fingerprint?: string; // Only present if the provider supports it

  // Usage data is always returned for non-streaming.
  // When streaming, you will get one usage object at
  // the end accompanied by an empty choices array.
  usage?: ResponseUsage;
};
```

----------------------------------------

TITLE: Configure Gemini Caching in User Message (JSON)
DESCRIPTION: Illustrates how to place a `cache_control` breakpoint within a user message's content array to cache a specific text block for Gemini models via OpenRouter.
SOURCE: https://openrouter.ai/docs/features/prompt-caching.mdx#_snippet_3

LANGUAGE: json
CODE:
```
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Based on the book text below:"
        },
        {
          "type": "text",
          "text": "HUGE TEXT BODY HERE",
          "cache_control": {
            "type": "ephemeral"
          }
        },
        {
          "type": "text",
          "text": "List all main characters mentioned in the text above."
        }
      ]
    }
  ]
}
```

----------------------------------------

TITLE: Disabling Provider Fallbacks
DESCRIPTION: This example shows how to disable provider fallbacks for a chat completions request by setting `allow_fallbacks` to `false` within the `provider` object. This ensures only the initial prioritized provider is used.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_7

LANGUAGE: TypeScript
CODE:
```
fetch('/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: 'Hello' }],
    provider: {
      allow_fallbacks: false,
    },
  }),
});
```

----------------------------------------

TITLE: Running MCP Client with Asyncio (Python)
DESCRIPTION: This Python code defines the main execution flow for the MCP client. The `main` function connects to the server, runs the interactive chat loop, and ensures resources are cleaned up using an `asyncio.run` wrapper. The `if __name__ == "__main__":` block makes the script executable.
SOURCE: https://openrouter.ai/docs/use-cases/mcp-servers.mdx#_snippet_3

LANGUAGE: python
CODE:
```
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()
                result = await self.process_query(query)
                print("Result:")
                print(result)

            except Exception as e:
                print(f"Error: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()

async def main():
    client = MCPClient()
    try:
        await client.connect_to_server(SERVER_CONFIG)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    import asyncio
    asyncio.run(main())
```

----------------------------------------

TITLE: Configure Anthropic Prompt Caching in System Message (JSON)
DESCRIPTION: This JSON snippet illustrates how to enable prompt caching for a large text body within a system message when using Anthropic models via OpenRouter. It demonstrates the use of the `cache_control` object with `type: "ephemeral"` applied to a specific text part within a multipart message structure.
SOURCE: https://openrouter.ai/docs/features/prompt-caching.mdx#_snippet_0

LANGUAGE: json
CODE:
```
{
  "messages": [
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "You are a historian studying the fall of the Roman Empire. You know the following book very well:"
        },
        {
          "type": "text",
          "text": "HUGE TEXT BODY",
          "cache_control": {
            "type": "ephemeral"
          }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What triggered the collapse?"
        }
      ]
    }
  ]
}
```

----------------------------------------

TITLE: Create OpenRouter API Key using Ruby net/http
DESCRIPTION: Shows how to make a POST request to create an OpenRouter API key using Ruby's standard net/http library. It sets up the URI, headers, request body, and sends the request.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/create-api-key.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/keys")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"name\": \"name\"\n}"

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Define GET Request for OpenRouter API Key
DESCRIPTION: This snippet defines the HTTP GET request structure used to retrieve details for a specific OpenRouter API key. It targets the `/api/v1/keys/{hash}` endpoint, where `{hash}` is the identifier for the desired key.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-api-key.mdx#_snippet_0

LANGUAGE: http
CODE:
```
GET https://openrouter.ai/api/v1/keys/{hash}
```

----------------------------------------

TITLE: Requesting FP8 Quantization with OpenRouter API (JavaScript)
DESCRIPTION: This code snippet demonstrates how to include the `quantizations` field within the `provider` object of a chat completion request body to filter for providers that support the 'fp8' quantization level. This ensures the request is routed only to providers offering models with this specific optimization.
SOURCE: https://openrouter.ai/docs/features/provider-routing.mdx#_snippet_10

LANGUAGE: JavaScript
CODE:
```
{
  model: 'meta-llama/llama-3.1-8b-instruct',
  messages: [{ role: 'user', content: 'Hello' }],
  provider: {
    quantizations: ['fp8'],
  },
}
```

----------------------------------------

TITLE: HTTP Request to Delete OpenRouter API Key
DESCRIPTION: Defines the HTTP method and endpoint for deleting an OpenRouter API key. Requires the API key hash as a path parameter.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/delete-api-key.mdx#_snippet_0

LANGUAGE: http
CODE:
```
DELETE https://openrouter.ai/api/v1/keys/{hash}
```

----------------------------------------

TITLE: Delete OpenRouter API Key
DESCRIPTION: Shows how to remove an API key by sending a DELETE request to the `/api/v1/keys/{key_hash}` endpoint. Requires the specific key hash and the Provisioning API key for authorization.
SOURCE: https://openrouter.ai/docs/features/provisioning-api-keys.mdx#_snippet_4

LANGUAGE: python
CODE:
```
import requests

PROVISIONING_API_KEY = "your-provisioning-key"
BASE_URL = "https://openrouter.ai/api/v1/keys"

# Delete a key
key_hash = "<YOUR_KEY_HASH>"
response = requests.delete(
    f"{BASE_URL}/{key_hash}",
    headers={
        "Authorization": f"Bearer {PROVISIONING_API_KEY}",
        "Content-Type": "application/json"
    }
)
```

LANGUAGE: typescript
CODE:
```
const PROVISIONING_API_KEY = 'your-provisioning-key';
const BASE_URL = 'https://openrouter.ai/api/v1/keys';

// Delete a key
const deleteKey = await fetch(`${BASE_URL}/${keyHash}`, {
  method: 'DELETE',
  headers: {
    Authorization: `Bearer ${PROVISIONING_API_KEY}`,
    'Content-Type': 'application/json',
  },
});
```

----------------------------------------

TITLE: Get Credits - Ruby (net/http)
DESCRIPTION: Provides a Ruby example using the net/http library to make an HTTPS GET request to the credits endpoint, including setting the Authorization header and printing the response body.
SOURCE: https://openrouter.ai/docs/api-reference/get-credits.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/credits")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = 'Bearer <token>'

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Exchange Code for API Key (TypeScript)
DESCRIPTION: TypeScript code snippet demonstrating how to make a POST request to the OpenRouter API endpoint to exchange the authorization code received in the callback URL for a user-controlled API key. Include `code_verifier` and `code_challenge_method` if a code challenge was used.
SOURCE: https://openrouter.ai/docs/use-cases/oauth-pkce.mdx#_snippet_5

LANGUAGE: typescript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/auth/keys', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    code: '<CODE_FROM_QUERY_PARAM>',
    code_verifier: '<CODE_VERIFIER>', // If code_challenge was used
    code_challenge_method: '<CODE_CHALLENGE_METHOD>', // If code_challenge was used
  }),
});

const { key } = await response.json();
```

----------------------------------------

TITLE: Convert MCP Tool Format to OpenAI
DESCRIPTION: Defines a helper function convert_tool_format that takes an MCP tool definition object and transforms it into an OpenAI-compatible tool definition dictionary, specifically for function calling.
SOURCE: https://openrouter.ai/docs/use-cases/mcp-servers.mdx#_snippet_1

LANGUAGE: python
CODE:
```

def convert_tool_format(tool):
    converted_tool = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": tool.inputSchema["properties"],
                "required": tool.inputSchema["required"]
            }
        }
    }
    return converted_tool

```

----------------------------------------

TITLE: OpenRouter Crypto Purchase API Response Structure (JSON)
DESCRIPTION: Example JSON response received from the OpenRouter `/api/v1/credits/coinbase` endpoint. Contains charge details like ID and expiration, and nested `web3_data` including `transfer_intent` with necessary `call_data` for executing the on-chain payment.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_1

LANGUAGE: JSON
CODE:
```
{
  "data": {
    "id": "...",
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-01-01T01:00:00Z",
    "web3_data": {
      "transfer_intent": {
        "metadata": {
          "chain_id": 8453,
          "contract_address": "0x03059433bcdb6144624cc2443159d9445c32b7a8",
          "sender": "0x9a85CB3bfd494Ea3a8C9E50aA6a3c1a7E8BACE11"
        },
        "call_data": {
          "recipient_amount": "...",
          "deadline": "...",
          "recipient": "...",
          "recipient_currency": "...",
          "refund_destination": "...",
          "fee_amount": "...",
          "id": "...",
          "operator": "...",
          "signature": "...",
          "prefix": "..."
        }
      }
    }
  }
}
```

----------------------------------------

TITLE: Create Coinbase Charge using C# RestClient
DESCRIPTION: Shows how to make the POST request in C# using a `RestClient` (commonly from RestSharp). It initializes the client with the base URL, creates a POST request, adds Authorization and Content-Type headers, adds the JSON body as a request parameter, and executes the request.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_8

LANGUAGE: csharp
CODE:
```
var client = new RestClient("https://openrouter.ai/api/v1/credits/coinbase");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"amount\": 1.1,\n  \"sender\": \"sender\",\n  \"chain_id\": 1\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

----------------------------------------

TITLE: Configuring PDF Parsing Engine for OpenRouter API
DESCRIPTION: Shows how to include the 'plugins' array in the OpenRouter chat completion request payload to explicitly select a specific PDF parsing engine like MistralOCR or PDFText.
SOURCE: https://openrouter.ai/docs/features/images-and-pdfs.mdx#_snippet_3

LANGUAGE: python
CODE:
```
plugins = [
    {
        "id": "file-parser",
        "pdf": {
            "engine": "{{ENGINE}}"
        }
    }
]
```

LANGUAGE: typescript
CODE:
```
{
  plugins: [
    {
      id: 'file-parser',
      pdf: {
        engine: '{{ENGINE}}',
      },
    },
  ],
}
```

----------------------------------------

TITLE: Setup and Configuration for MCP Client
DESCRIPTION: Imports necessary libraries (asyncio, typing, contextlib, mcp, openai, dotenv, json), loads environment variables from a .env file, defines the LLM model to use, and configures the MCP server command and arguments for the File System MCP.
SOURCE: https://openrouter.ai/docs/use-cases/mcp-servers.mdx#_snippet_0

LANGUAGE: python
CODE:
```
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()  # load environment variables from .env

MODEL = "anthropic/claude-3-7-sonnet"

SERVER_CONFIG = {
    "command": "npx",
    "args": ["-y",
              "@modelcontextprotocol/server-filesystem",
              f"/Applications/"],
    "env": None
}
```

----------------------------------------

TITLE: Sending Completions Request with cURL
DESCRIPTION: Example using the cURL command-line tool to send a POST request to the OpenRouter completions endpoint, including authorization and content type headers, and a JSON request body.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl -X POST https://openrouter.ai/api/v1/completions \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
  "model": "model",
  "prompt": "prompt"
}'
```

----------------------------------------

TITLE: Create Coinbase Charge using Java Unirest
DESCRIPTION: Shows how to make the POST request in Java using the `Unirest` library. It specifies the URL, adds Authorization and Content-Type headers, sets the JSON string body, and executes the request, storing the response.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_6

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/credits/coinbase")
  .header("Authorization", "Bearer <token>")
  .header("Content-Type", "application/json")
  .body("{\n  \"amount\": 1.1,\n  \"sender\": \"sender\",\n  \"chain_id\": 1\n}")
  .asString();
```

----------------------------------------

TITLE: Make POST Request with Unirest in Java
DESCRIPTION: This Java snippet demonstrates making a POST request using the Unirest library. It specifies the URL, sets the Content-Type header, provides the JSON request body, and executes the request, expecting a String response.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_15

LANGUAGE: java
CODE:
```
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/auth/keys")
  .header("Content-Type", "application/json")
  .body("{\n  \"code\": \"string\"\n}")
  .asString();
```

----------------------------------------

TITLE: Make POST Request to OpenRouter API - Java (Unirest)
DESCRIPTION: Shows how to make a POST request to the OpenRouter API /auth/keys endpoint using the Unirest library in Java. It demonstrates setting the content type header and the request body in a concise manner.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_20

LANGUAGE: Java
CODE:
```
HttpResponse<String> response = Unirest.post("https://openrouter.ai/api/v1/auth/keys")
  .header("Content-Type", "application/json")
  .body("{\n  \"code\": \"string\"\n}")
  .asString();
```

----------------------------------------

TITLE: Requesting Crypto Purchase Calldata via OpenRouter API (TypeScript)
DESCRIPTION: Makes a POST request to the OpenRouter API endpoint to initiate a cryptocurrency credit purchase. Specifies the desired amount in USD, the sender's EVM address, and the target chain ID. Requires an OpenRouter API key for authorization.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_0

LANGUAGE: TypeScript
CODE:
```
const response = await fetch('https://openrouter.ai/api/v1/credits/coinbase', {
  method: 'POST',
  headers: {
    Authorization: 'Bearer <OPENROUTER_API_KEY>',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    amount: 10, // Target credit amount in USD
    sender: '0x9a85CB3bfd494Ea3a8C9E50aA6a3c1a7E8BACE11',
    chain_id: 8453,
  }),
});
const responseJSON = await response.json();
```

----------------------------------------

TITLE: Getting Generation Metadata with cURL
DESCRIPTION: Demonstrates how to make a GET request to the generation endpoint using cURL, including setting the Authorization header and passing the required 'id' query parameter.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl -G https://openrouter.ai/api/v1/generation \
     -H "Authorization: Bearer <token>" \
     -d id=id
```

----------------------------------------

TITLE: Make POST Request with net/http in Ruby
DESCRIPTION: This Ruby snippet uses the standard library's `net/http` to perform a POST request. It constructs the URI, sets up an HTTP connection (with SSL enabled), creates a POST request object, sets the Content-Type header, and assigns the JSON body. The response body is then printed.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_14

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/auth/keys")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/json'
request.body = "{\n  \"code\": \"string\"\n}"

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: Fetching Models with Curl (Shell)
DESCRIPTION: Demonstrates how to use the `curl` command-line tool to make a GET request to the OpenRouter API models endpoint.
SOURCE: https://openrouter.ai/docs/api-reference/list-available-models.mdx#_snippet_1

LANGUAGE: shell
CODE:
```
curl https://openrouter.ai/api/v1/models
```

----------------------------------------

TITLE: MCP Client Class Implementation
DESCRIPTION: Implements the MCPClient class to manage the stateful interaction with an MCP server via OpenRouter. It includes methods for connecting to the server, listing and converting tools, processing user queries by calling the LLM and executing tools based on its response, and managing message history.
SOURCE: https://openrouter.ai/docs/use-cases/mcp-servers.mdx#_snippet_2

LANGUAGE: python
CODE:
```
class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI(
            base_url="https://openrouter.ai/api/v1"
        )

    async def connect_to_server(self, server_config):
        server_params = StdioServerParameters(**server_config)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools from the MCP server
        response = await self.session.list_tools()
        print("\nConnected to server with tools:", [tool.name for tool in response.tools])

        self.messages = []

    async def process_query(self, query: str) -> str:

        self.messages.append({
            "role": "user",
            "content": query
        })

        response = await self.session.list_tools()
        available_tools = [convert_tool_format(tool) for tool in response.tools]

        response = self.openai.chat.completions.create(
            model=MODEL,
            tools=available_tools,
            messages=self.messages
        )
        self.messages.append(response.choices[0].message.model_dump())

        final_text = []
        content = response.choices[0].message
        if content.tool_calls is not None:
            tool_name = content.tool_calls[0].function.name
            tool_args = content.tool_calls[0].function.arguments
            tool_args = json.loads(tool_args) if tool_args else {}

            # Execute tool call
            try:
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
            except Exception as e:
                print(f"Error calling tool {tool_name}: {e}")
                result = None

            self.messages.append({
                "role": "tool",
                "tool_call_id": content.tool_calls[0].id,
                "name": tool_name,
                "content": result.content
            })

            response = self.openai.chat.completions.create(
                model=MODEL,
                max_tokens=1000,
                messages=self.messages,
            )

            final_text.append(response.choices[0].message.content)
        else:
            final_text.append(content.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
```

----------------------------------------

TITLE: Example API Response Format (JSON)
DESCRIPTION: This JSON snippet illustrates the structure of a typical successful API response from OpenRouter, specifically showing the format for listing API keys. It includes a 'data' array containing objects representing individual keys with properties like creation/update timestamps, hash, label, name, status, limit, and usage.
SOURCE: https://openrouter.ai/docs/features/provisioning-api-keys.mdx#_snippet_5

LANGUAGE: json
CODE:
```
{
  "data": [
    {
      "created_at": "2025-02-19T20:52:27.363244+00:00",
      "updated_at": "2025-02-19T21:24:11.708154+00:00",
      "hash": "<YOUR_KEY_HASH>",
      "label": "sk-or-v1-customkey",
      "name": "Customer Key",
      "disabled": false,
      "limit": 10,
      "usage": 0
    }
  ]
}
```

----------------------------------------

TITLE: Generate SHA-256 Code Challenge (TypeScript)
DESCRIPTION: TypeScript function using the Web Crypto API and Buffer to generate a SHA-256 code challenge from a code verifier. This is used for the S256 code challenge method in the PKCE flow.
SOURCE: https://openrouter.ai/docs/use-cases/oauth-pkce.mdx#_snippet_3

LANGUAGE: typescript
CODE:
```
import { Buffer } from 'buffer';

async function createSHA256CodeChallenge(input: string) {
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return Buffer.from(hash).toString('base64url');
}

const codeVerifier = 'your-random-string';
const generatedCodeChallenge = await createSHA256CodeChallenge(codeVerifier);
```

----------------------------------------

TITLE: Create Coinbase Charge using Ruby Net::HTTP
DESCRIPTION: Provides a Ruby example using the `net/http` library to send the POST request. It sets up the URI, creates an HTTP object with SSL enabled, constructs the POST request, adds headers, sets the body, sends the request, and prints the response body.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_5

LANGUAGE: ruby
CODE:
```
require 'uri'
require 'net/http'

url = URI("https://openrouter.ai/api/v1/credits/coinbase")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"amount\": 1.1,\n  \"sender\": \"sender\",\n  \"chain_id\": 1\n}"

response = http.request(request)
puts response.read_body
```

----------------------------------------

TITLE: OpenRouter API Key Response Type (TypeScript)
DESCRIPTION: Defines the TypeScript type structure for the response received from the `/api/v1/auth/key` endpoint. It details the `data` object containing properties like `label`, `usage`, `limit`, `is_free_tier`, and `rate_limit` (with nested `requests` and `interval`). This helps developers understand the expected data format when parsing the API response.
SOURCE: https://openrouter.ai/docs/api-reference/limits.mdx#_snippet_1

LANGUAGE: typescript
CODE:
```
type Key = {
  data: {
    label: string;
    usage: number; // Number of credits used
    limit: number | null; // Credit limit for the key, or null if unlimited
    is_free_tier: boolean; // Whether the user has paid for credits before
    rate_limit: {
      requests: number; // Number of requests allowed...
      interval: string; // in this interval, e.g. "10s"
    };
  };
};
```

----------------------------------------

TITLE: Update OpenRouter API Key
DESCRIPTION: Demonstrates how to modify an existing API key's properties (like name or disabled status) using a PATCH request to the `/api/v1/keys/{key_hash}` endpoint. Requires the key hash, Provisioning API key, and the fields to update in the request body.
SOURCE: https://openrouter.ai/docs/features/provisioning-api-keys.mdx#_snippet_3

LANGUAGE: python
CODE:
```
import requests

PROVISIONING_API_KEY = "your-provisioning-key"
BASE_URL = "https://openrouter.ai/api/v1/keys"

# Update a key
key_hash = "<YOUR_KEY_HASH>"
response = requests.patch(
    f"{BASE_URL}/{key_hash}",
    headers={
        "Authorization": f"Bearer {PROVISIONING_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "name": "Updated Key Name",
        "disabled": True  # Disable the key
    }
)
```

LANGUAGE: typescript
CODE:
```
const PROVISIONING_API_KEY = 'your-provisioning-key';
const BASE_URL = 'https://openrouter.ai/api/v1/keys';

// Update a key
const keyHash = '<YOUR_KEY_HASH>';
const updateKey = await fetch(`${BASE_URL}/${keyHash}`, {
  method: 'PATCH',
  headers: {
    Authorization: `Bearer ${PROVISIONING_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'Updated Key Name',
    disabled: true, // Disable the key
  }),
});
```

----------------------------------------

TITLE: OpenRouter API Request Payload for Reasoning Tokens
DESCRIPTION: Defines the structure of the `reasoning` object within the OpenRouter chat completions API request body, allowing control over reasoning effort, token limits, and exclusion from the response. It shows the mutually exclusive `effort` and `max_tokens` options, and the optional `exclude` flag.
SOURCE: https://openrouter.ai/docs/use-cases/reasoning-tokens.mdx#_snippet_0

LANGUAGE: json
CODE:
```
{
  "model": "your-model",
  "messages": [],
  "reasoning": {
    // One of the following (not both):
    "effort": "high", // Can be "high", "medium", or "low" (OpenAI-style)
    "max_tokens": 2000, // Specific token limit (Anthropic-style)

    // Optional: Default is false. All models support this.
    "exclude": false // Set to true to exclude reasoning tokens from response
  }
}
```

----------------------------------------

TITLE: Configure Anthropic Prompt Caching in User Message (JSON)
DESCRIPTION: This JSON example shows how to apply prompt caching to a large text section included within a user message for Anthropic models. It utilizes the `cache_control` object with `type: "ephemeral"` on a text part, suitable for caching data provided by the user, such as book excerpts or datasets.
SOURCE: https://openrouter.ai/docs/features/prompt-caching.mdx#_snippet_1

LANGUAGE: json
CODE:
```
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Given the book below:"
        },
        {
          "type": "text",
          "text": "HUGE TEXT BODY",
          "cache_control": {
            "type": "ephemeral"
          }
        },
        {
          "type": "text",
          "text": "Name all the characters in the above book"
        }
      ]
    }
  ]
}
```

----------------------------------------

TITLE: Configure Gemini Caching in System Message (JSON)
DESCRIPTION: Demonstrates how to include a `cache_control` breakpoint within a system message's content array to enable caching for a specific text part when using Gemini models on OpenRouter.
SOURCE: https://openrouter.ai/docs/features/prompt-caching.mdx#_snippet_2

LANGUAGE: json
CODE:
```
{
  "messages": [
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "You are a historian studying the fall of the Roman Empire. Below is an extensive reference book:"
        },
        {
          "type": "text",
          "text": "HUGE TEXT BODY HERE",
          "cache_control": {
            "type": "ephemeral"
          }
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What triggered the collapse?"
        }
      ]
    }
  ]
}
```

----------------------------------------

TITLE: Define OpenRouter API Key Update Endpoint
DESCRIPTION: Defines the HTTP method, endpoint URL structure, and required content type for updating an existing OpenRouter API key. The key to be updated is identified by its hash in the path.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/update-api-key.mdx#_snippet_0

LANGUAGE: http
CODE:
```
PATCH https://openrouter.ai/api/v1/keys/{hash}
Content-Type: application/json
```

----------------------------------------

TITLE: HTTP Request for Completions
DESCRIPTION: Shows the basic HTTP method and endpoint for the OpenRouter completions API, along with the required Content-Type header.
SOURCE: https://openrouter.ai/docs/api-reference/completion.mdx#_snippet_0

LANGUAGE: http
CODE:
```
POST https://openrouter.ai/api/v1/completions
Content-Type: application/json
```

----------------------------------------

TITLE: Initiating and Resuming URLSession Data Task in Swift
DESCRIPTION: This snippet shows how to create a data task with a URLRequest using URLSession, define a completion handler to process the response or error, and start the task execution by calling `resume()`. It includes basic error handling and printing the HTTP response.
SOURCE: https://openrouter.ai/docs/api-reference/api-keys/get-current-api-key.mdx#_snippet_19

LANGUAGE: Swift
CODE:
```
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Initiate PKCE Flow (S256)
DESCRIPTION: Construct the URL to redirect the user to OpenRouter to initiate the OAuth PKCE flow using the recommended S256 code challenge method. Replace <YOUR_SITE_URL> with your callback URL and <CODE_CHALLENGE> with the generated code challenge.
SOURCE: https://openrouter.ai/docs/use-cases/oauth-pkce.mdx#_snippet_0

LANGUAGE: txt
CODE:
```
https://openrouter.ai/auth?callback_url=<YOUR_SITE_URL>&code_challenge=<CODE_CHALLENGE>&code_challenge_method=S256
```

----------------------------------------

TITLE: Initiate PKCE Flow (Plain)
DESCRIPTION: Construct the URL to redirect the user to OpenRouter to initiate the OAuth PKCE flow using the plain code challenge method. Replace <YOUR_SITE_URL> with your callback URL and <CODE_CHALLENGE> with the code verifier itself.
SOURCE: https://openrouter.ai/docs/use-cases/oauth-pkce.mdx#_snippet_1

LANGUAGE: txt
CODE:
```
https://openrouter.ai/auth?callback_url=<YOUR_SITE_URL>&code_challenge=<CODE_CHALLENGE>&code_challenge_method=plain
```

----------------------------------------

TITLE: Create Coinbase Charge using JavaScript Fetch
DESCRIPTION: Provides a JavaScript example using the `fetch` API to send the POST request. It sets the method, headers (including Authorization and Content-Type), and the JSON string body, then handles the response and potential errors.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_3

LANGUAGE: javascript
CODE:
```
const url = 'https://openrouter.ai/api/v1/credits/coinbase';
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"amount":1.1,"sender":"sender","chain_id":1}'
};

try {
  const response = await fetch(url, options);
  const data = await response.json();
  console.log(data);
} catch (error) {
  console.error(error);
}
```

----------------------------------------

TITLE: Function: subsidizedTransferToken (Nonpayable)
DESCRIPTION: Executes a subsidized token transfer using a TransferIntent and EIP2612 signature data. This function modifies the contract state and requires a transaction.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_13

LANGUAGE: JSON
CODE:
```
{
    "inputs": [
      {
        "components": [
          { "internalType": "uint256", "name": "recipientAmount", "type": "uint256" },
          { "internalType": "uint256", "name": "deadline", "type": "uint256" },
          {
            "internalType": "address payable",
            "name": "recipient",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "recipientCurrency",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "refundDestination",
            "type": "address"
          },
          { "internalType": "uint256", "name": "feeAmount", "type": "uint256" },
          { "internalType": "bytes16", "name": "id", "type": "bytes16" },
          { "internalType": "address", "name": "operator", "type": "address" },
          { "internalType": "bytes", "name": "signature", "type": "bytes" },
          { "internalType": "bytes", "name": "prefix", "type": "bytes" }
        ],
        "internalType": "struct TransferIntent",
        "name": "_intent",
        "type": "tuple"
      },
      {
        "components": [
          { "internalType": "address", "name": "owner", "type": "address" },
          { "internalType": "bytes", "name": "signature", "type": "bytes" }
        ],
        "internalType": "struct EIP2612SignatureTransferData",
        "name": "_signatureTransferData",
        "type": "tuple"
      }
    ],
    "name": "subsidizedTransferToken",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Create Coinbase Charge using PHP Guzzle
DESCRIPTION: Provides a PHP example using the Guzzle HTTP client to send the POST request. It creates a client instance, makes a POST request to the URL, providing the JSON body and headers (Authorization and Content-Type) in an options array, and echoes the response body.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_7

LANGUAGE: php
CODE:
```
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://openrouter.ai/api/v1/credits/coinbase', [
  'body' => '{
  "amount": 1.1,
  "sender": "sender",
  "chain_id": 1
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

----------------------------------------

TITLE: Create Coinbase Charge using Swift URLSession
DESCRIPTION: Provides a Swift example using `URLSession` to send the POST request. It sets up headers and parameters, serializes the parameters to JSON data for the body, creates a URLRequest, sets the method and headers, assigns the body, creates a data task, handles the response/error, and resumes the task.
SOURCE: https://openrouter.ai/docs/api-reference/create-a-coinbase-charge.mdx#_snippet_9

LANGUAGE: swift
CODE:
```
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = [
  "amount": 1.1,
  "sender": "sender",
  "chain_id": 1
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://openrouter.ai/api/v1/credits/coinbase")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```

----------------------------------------

TITLE: Function: registerOperator (Nonpayable)
DESCRIPTION: Registers the caller as an operator. This function modifies the contract state and requires a transaction.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_9

LANGUAGE: JSON
CODE:
```
{
    "inputs": [],
    "name": "registerOperator",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Initializing Viem Clients and ABI (TypeScript)
DESCRIPTION: Sets up viem public and wallet clients for interacting with the Base network, derives an account from a private key, and defines the ABI for the Coinbase onchain payment protocol contract, which is necessary for interacting with the contract functions like `swapAndTransferUniswapV3Native()`.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_2

LANGUAGE: TypeScript
CODE:
```
import { createPublicClient, createWalletClient, http, parseEther } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';
import { base } from 'viem/chains';

// The ABI for Coinbase's onchain payment protocol
const abi = [
  {
    inputs: [
      {
        internalType: 'contract IUniversalRouter',
        name: '_uniswap',
        type: 'address',
      },
      { internalType: 'contract Permit2', name: '_permit2', type: 'address' },
      { internalType: 'address', name: '_initialOperator', type: 'address' },
      {
        internalType: 'address',
        name: '_initialFeeDestination',
        type: 'address',
      },
      {
        internalType: 'contract IWrappedNativeCurrency',
        name: '_wrappedNativeCurrency',
        type: 'address',
      },
    ],
    stateMutability: 'nonpayable',
    type: 'constructor',
  },
  { inputs: [], name: 'AlreadyProcessed', type: 'error' },
  { inputs: [], name: 'ExpiredIntent', type: 'error' },
  {
    inputs: [
      { internalType: 'address', name: 'attemptedCurrency', type: 'address' },
    ],
    name: 'IncorrectCurrency',
    type: 'error',
  },
  { inputs: [], name: 'InexactTransfer', type: 'error' },
  {
    inputs: [{ internalType: 'uint256', name: 'difference', type: 'uint256' }],
    name: 'InsufficientAllowance',
    type: 'error',
  },
  {
    inputs: [{ internalType: 'uint256', name: 'difference', type: 'uint256' }],
    name: 'InsufficientBalance',
    type: 'error',
  },
  {
    inputs: [{ internalType: 'int256', name: 'difference', type: 'int256' }],
    name: 'InvalidNativeAmount',
    type: 'error',
  },
  { inputs: [], name: 'InvalidSignature', type: 'error' },
  { inputs: [], name: 'InvalidTransferDetails', type: 'error' },
  {
    inputs: [
      { internalType: 'address', name: 'recipient', type: 'address' },
      { internalType: 'uint256', name: 'amount', type: 'uint256' },
      { internalType: 'bool', name: 'isRefund', type: 'bool' },
      { internalType: 'bytes', name: 'data', type: 'bytes' },
    ],
    name: 'NativeTransferFailed',
    type: 'error',
  },
  { inputs: [], name: 'NullRecipient', type: 'error' },
  { inputs: [], name: 'OperatorNotRegistered', type: 'error' },
  { inputs: [], name: 'PermitCallFailed', type: 'error' },
  {
    inputs: [{ internalType: 'bytes', name: 'reason', type: 'bytes' }],
    name: 'SwapFailedBytes',
    type: 'error',
  },
  {
    inputs: [{ internalType: 'string', name: 'reason', type: 'string' }],
    name: 'SwapFailedString',
    type: 'error',
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: false,
        internalType: 'address',
        name: 'operator',
        type: 'address',
      },
      {
        indexed: false,
        internalType: 'address',
        name: 'feeDestination',
        type: 'address',
      },
    ],
    name: 'OperatorRegistered',
    type: 'event',
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: false,
        internalType: 'address',
        name: 'operator',
        type: 'address',
      },
    ],
    name: 'OperatorUnregistered',
    type: 'event',
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: true,
        internalType: 'address',
        name: 'previousOwner',
        type: 'address',
      },
      {
        indexed: true,
        internalType: 'address',
        name: 'newOwner',
        type: 'address',
      },\n    ],
    name: 'OwnershipTransferred',
    type: 'event',
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: false,
        internalType: 'address',
        name: 'account',
        type: 'address',
      },
    ],
    name: 'Paused',
    type: 'event',
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: true,
        internalType: 'address',
        name: 'operator',
        type: 'address',
      },
      { indexed: false, internalType: 'bytes16', name: 'id', type: 'bytes16' },
      {
        indexed: false,
        internalType: 'address',
        name: 'recipient',
        type: 'address',
      },
      {
        indexed: false,
        internalType: 'address',
        name: 'sender',
        type: 'address',
      },
      {
        indexed: false,
        internalType: 'uint256',
        name: 'amount',
        type: 'uint256',
      },
      {
        indexed: false,
        internalType: 'address',
        name: 'currency',
        type: 'address',
      },
      {
        indexed: false,
        internalType: 'bytes',
        name: 'data',
        type: 'bytes',
      },
    ],
    name: 'PaymentProcessed',
    type: 'event',
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: false,
        internalType: 'address',
        name: 'account',
        type: 'address',
      },
    ],
    name: 'Unpaused',
    type: 'event',
  },
  {
    inputs: [
      { internalType: 'address', name: 'operator', type: 'address' },
      { internalType: 'address', name: 'feeDestination', type: 'address' },
    ],
    name: 'registerOperator',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function',
  },
  {
    inputs: [
      { internalType: 'bytes16', name: 'id', type: 'bytes16' },
      { internalType: 'address', name: 'recipient', type: 'address' },
      { internalType: 'uint256', name: 'amount', type: 'uint256' },
      { internalType: 'address', name: 'currency', type: 'address' },
      { internalType: 'bytes', name: 'data', type: 'bytes' },
      { internalType: 'bytes', name: 'signature', type: 'bytes' },
    ],
    name: 'swapAndTransferUniswapV3Native',
    outputs: [],
    stateMutability: 'payable',
    type: 'function',
  },
  {
    inputs: [
      { internalType: 'bytes16', name: 'id', type: 'bytes16' },
      { internalType: 'address', name: 'recipient', type: 'address' },
      { internalType: 'uint256', name: 'amount', type: 'uint256' },
      { internalType: 'address', name: 'currency', type: 'address' },
      { internalType: 'bytes', name: 'data', type: 'bytes' },
      { internalType: 'bytes', name: 'signature', type: 'bytes' },
    ],
    name: 'swapAndTransferUniswapV3Token',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function',
  },
  {
    inputs: [{ internalType: 'address', name: 'operator', type: 'address' }],
    name: 'unregisterOperator',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function',
  },
];

// Replace with your actual private key and contract address
const privateKey = '0x...'; // Your private key
const contractAddress = '0x...'; // Coinbase Onchain Payment Protocol contract address

const account = privateKeyToAccount(privateKey);

const publicClient = createPublicClient({
  chain: base,
  transport: http()
});

const walletClient = createWalletClient({
  account,
  chain: base,
  transport
```

----------------------------------------

TITLE: Simulating and Sending Contract Transaction with viem (TypeScript)
DESCRIPTION: This snippet shows how to set up viem clients (public and wallet), extract transaction parameters from an OpenRouter API response, simulate the contract call to validate inputs, and then send the transaction on the blockchain using the wallet client. It specifically targets the `swapAndTransferUniswapV3Native` function.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_23

LANGUAGE: TypeScript
CODE:
```
          { internalType: 'bytes', name: 'signature', type: 'bytes' },
          { internalType: 'bytes', name: 'prefix', type: 'bytes' },
        ],
        internalType: 'struct TransferIntent',
        name: '_intent',
        type: 'tuple',
      },
    ],
    name: 'wrapAndTransfer',
    outputs: [],
    stateMutability: 'payable',
    type: 'function',
  },
  { stateMutability: 'payable', type: 'receive' },
];

// Set up viem clients
const publicClient = createPublicClient({
  chain: base,
  transport: http(),
});
const account = privateKeyToAccount('0x...');
const walletClient = createWalletClient({
  chain: base,
  transport: http(),
  account,
});

// Use the calldata included in the charge response
const { contract_address } =
  responseJSON.data.web3_data.transfer_intent.metadata;
const call_data = responseJSON.data.web3_data.transfer_intent.call_data;

// When transacting in ETH, a pool fees tier of 500 (the lowest) is very
// likely to be sufficient. However, if you plan to swap with a different
// contract method, using less-common ERC-20 tokens, it is recommended to
// call that chain's Uniswap QuoterV2 contract to check its liquidity.
// Depending on the results, choose the lowest fee tier which has enough
// liquidity in the pool.
const poolFeesTier = 500;

// Simulate the transaction first to prevent most common revert reasons
const { request } = await publicClient.simulateContract({
  abi,
  account,
  address: contract_address,
  functionName: 'swapAndTransferUniswapV3Native',
  args: [
    {
      recipientAmount: BigInt(call_data.recipient_amount),
      deadline: BigInt(
        Math.floor(new Date(call_data.deadline).getTime() / 1000),
      ),
      recipient: call_data.recipient,
      recipientCurrency: call_data.recipient_currency,
      refundDestination: call_data.refund_destination,
      feeAmount: BigInt(call_data.fee_amount),
      id: call_data.id,
      operator: call_data.operator,
      signature: call_data.signature,
      prefix: call_data.prefix,
    },
    poolFeesTier,
  ],
  // Transaction value in ETH. You'll want to include a little extra to
  // ensure the transaction & swap is successful. All excess funds return
  // back to your sender address afterwards.
  value: parseEther('0.004'),
});

// Send the transaction on chain
const txHash = await walletClient.writeContract(request);
console.log('Transaction hash:', txHash);
```

----------------------------------------

TITLE: Function: permit2 (View)
DESCRIPTION: Retrieves the address of the associated Permit2 contract. This is a view function and does not modify the contract state.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_8

LANGUAGE: JSON
CODE:
```
{
    "inputs": [],
    "name": "permit2",
    "outputs": [{"internalType": "contract Permit2", "name": "", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
  }
```

----------------------------------------

TITLE: Function: setSweeper (Nonpayable)
DESCRIPTION: Sets the address of the contract sweeper. This function modifies the contract state and requires a transaction.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_12

LANGUAGE: JSON
CODE:
```
{
    "inputs": [{"internalType": "address", "name": "newSweeper", "type": "address"}],
    "name": "setSweeper",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Function: renounceOwnership (Nonpayable)
DESCRIPTION: Renounces ownership of the contract, transferring it to the zero address. This function modifies the contract state and requires a transaction.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_11

LANGUAGE: JSON
CODE:
```
{
    "inputs": [],
    "name": "renounceOwnership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Usage Accounting Response Format (JSON)
DESCRIPTION: Illustrates the structure of the 'usage' object returned in the API response when usage accounting is enabled, detailing token counts, cost, and caching information.
SOURCE: https://openrouter.ai/docs/use-cases/usage-accounting.mdx#_snippet_1

LANGUAGE: json
CODE:
```
{
  "object": "chat.completion.chunk",
  "usage": {
    "completion_tokens": 2,
    "completion_tokens_details": {
      "reasoning_tokens": 0
    },
    "cost": 197,
    "prompt_tokens": 194,
    "prompt_tokens_details": {
      "cached_tokens": 0
    },
    "total_tokens": 196
  }
}
```

----------------------------------------

TITLE: Function: unwrapAndTransfer (ABI)
DESCRIPTION: Defines a non-payable function named 'unwrapAndTransfer'. It takes two complex struct inputs: '_intent' (type 'TransferIntent') and '_signatureTransferData' (type 'Permit2SignatureTransferData'). It returns no outputs and is likely used for a wrapped token transfer involving Permit2 signatures.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_21

LANGUAGE: JSON
CODE:
```
{
    "inputs": [
      {
        "components": [
          { "internalType": "uint256", "name": "recipientAmount", "type": "uint256" },
          { "internalType": "uint256", "name": "deadline", "type": "uint256" },
          {
            "internalType": "address payable",
            "name": "recipient",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "recipientCurrency",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "refundDestination",
            "type": "address"
          },
          { "internalType": "uint256", "name": "feeAmount", "type": "uint256" },
          { "internalType": "bytes16", "name": "id", "type": "bytes16" },
          { "internalType": "address", "name": "operator", "type": "address" },
          { "internalType": "bytes", "name": "signature", "type": "bytes" },
          { "internalType": "bytes", "name": "prefix", "type": "bytes" }
        ],
        "internalType": "struct TransferIntent",
        "name": "_intent",
        "type": "tuple"
      },
      {
        "components": [
          {
            "components": [
              {
                "components": [
                  { "internalType": "address", "name": "token", "type": "address" },
                  { "internalType": "uint256", "name": "amount", "type": "uint256" }
                ],
                "internalType": "struct ISignatureTransfer.TokenPermissions",
                "name": "permitted",
                "type": "tuple"
              },
              { "internalType": "uint256", "name": "nonce", "type": "uint256" },
              { "internalType": "uint256", "name": "deadline", "type": "uint256" }
            ],
            "internalType": "struct ISignatureTransfer.PermitTransferFrom",
            "name": "permit",
            "type": "tuple"
          },
          {
            "components": [
              { "internalType": "address", "name": "to", "type": "address" },
              {
                "internalType": "uint256",
                "name": "requestedAmount",
                "type": "uint256"
              }
            ],
            "internalType": "struct ISignatureTransfer.SignatureTransferDetails",
            "name": "transferDetails",
            "type": "tuple"
          },
          { "internalType": "bytes", "name": "signature", "type": "bytes" }
        ],
        "internalType": "struct Permit2SignatureTransferData",
        "name": "_signatureTransferData",
        "type": "tuple"
      }
    ],
    "name": "unwrapAndTransfer",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Function: unwrapAndTransferPreApproved (ABI)
DESCRIPTION: Defines a non-payable function named 'unwrapAndTransferPreApproved'. It takes one complex struct input: '_intent' (type 'TransferIntent'). It returns no outputs and is likely used for a wrapped token transfer that has been pre-approved.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_22

LANGUAGE: JSON
CODE:
```
{
    "inputs": [
      {
        "components": [
          { "internalType": "uint256", "name": "recipientAmount", "type": "uint256" },
          { "internalType": "uint256", "name": "deadline", "type": "uint256" },
          {
            "internalType": "address payable",
            "name": "recipient",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "recipientCurrency",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "refundDestination",
            "type": "address"
          },
          { "internalType": "uint256", "name": "feeAmount", "type": "uint256" },
          { "internalType": "bytes16", "name": "id", "type": "bytes16" },
          { "internalType": "address", "name": "operator", "type": "address" },
          { "internalType": "bytes", "name": "signature", "type": "bytes" },
          { "internalType": "bytes", "name": "prefix", "type": "bytes" }
        ],
        "internalType": "struct TransferIntent",
        "name": "_intent",
        "type": "tuple"
      }
    ],
    "name": "unwrapAndTransferPreApproved",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Function: pause (Nonpayable)
DESCRIPTION: Pauses the contract, preventing certain operations. This function modifies the contract state and requires a transaction.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_6

LANGUAGE: JSON
CODE:
```
{
    "inputs": [],
    "name": "pause",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Event: Unpaused
DESCRIPTION: This event is emitted when the contract transitions from a paused state to an unpaused state, indicating the account that triggered the unpause.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_4

LANGUAGE: JSON
CODE:
```
{
        "anonymous": false,
        "inputs": [
          {
            "indexed": false,
            "internalType": "address",
            "name": "account",
            "type": "address"
          }
        ],
        "name": "Unpaused",
        "type": "event"
      }
```

----------------------------------------

TITLE: Example OpenRouter Completions Response (JSON)
DESCRIPTION: Provides a concrete example of a non-streaming OpenRouter completions API response in JSON format, illustrating the structure including the ID, choices array with message content and finish reasons, usage data, and the model identifier.
SOURCE: https://openrouter.ai/docs/api-reference/overview.mdx#_snippet_6

LANGUAGE: JSON
CODE:
```
{
  "id": "gen-xxxxxxxxxxxxxx",
  "choices": [
    {
      "finish_reason": "stop", // Normalized finish_reason
      "native_finish_reason": "stop", // The raw finish_reason from the provider
      "message": {
        // will be "delta" if streaming
        "role": "assistant",
        "content": "Hello there!"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 4,
    "total_tokens": 4
  },
  "model": "openai/gpt-3.5-turbo" // Could also be "anthropic/claude-2.1", etc, depending on the "model" that ends up being used
}
```

----------------------------------------

TITLE: Function: unregisterOperator (ABI)
DESCRIPTION: Defines a non-payable function named 'unregisterOperator'. It takes no inputs and returns no outputs. This function is likely used to remove an address from a list of authorized operators.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_20

LANGUAGE: JSON
CODE:
```
{
    "inputs": [],
    "name": "unregisterOperator",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Function: swapAndTransferUniswapV3Native (Payable)
DESCRIPTION: Performs a token swap via Uniswap V3 and then transfers the resulting native tokens based on a TransferIntent and pool fees tier. This function is payable and modifies the contract state.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_14

LANGUAGE: JSON
CODE:
```
{
    "inputs": [
      {
        "components": [
          { "internalType": "uint256", "name": "recipientAmount", "type": "uint256" },
          { "internalType": "uint256", "name": "deadline", "type": "uint256" },
          {
            "internalType": "address payable",
            "name": "recipient",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "recipientCurrency",
            "type": "address"
          },
          {
            "internalType": "address",
            "name": "refundDestination",
            "type": "address"
          },
          { "internalType": "uint256", "name": "feeAmount", "type": "uint256" },
          { "internalType": "bytes16", "name": "id", "type": "bytes16" },
          { "internalType": "address", "name": "operator", "type": "address" },
          { "internalType": "bytes", "name": "signature", "type": "bytes" },
          { "internalType": "bytes", "name": "prefix", "type": "bytes" }
        ],
        "internalType": "struct TransferIntent",
        "name": "_intent",
        "type": "tuple"
      },
      { "internalType": "uint24", "name": "poolFeesTier", "type": "uint24" }
    ],
    "name": "swapAndTransferUniswapV3Native",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Initiate PKCE Flow (No Challenge)
DESCRIPTION: Construct the URL to redirect the user to OpenRouter to initiate the OAuth flow without a code challenge. This method is less secure and not recommended for production applications.
SOURCE: https://openrouter.ai/docs/use-cases/oauth-pkce.mdx#_snippet_2

LANGUAGE: txt
CODE:
```
https://openrouter.ai/auth?callback_url=<YOUR_SITE_URL>
```

----------------------------------------

TITLE: Installing PydanticAI (Bash)
DESCRIPTION: Provides the bash command necessary to install the PydanticAI library with the OpenAI integration using pip. This is a prerequisite for using PydanticAI with OpenRouter via its OpenAI compatibility layer.
SOURCE: https://openrouter.ai/docs/community/frameworks.mdx#_snippet_4

LANGUAGE: Bash
CODE:
```
pip install 'pydantic-ai-slim[openai]'
```

----------------------------------------

TITLE: Defining OpenRouter Response Usage Type (TypeScript)
DESCRIPTION: Defines the TypeScript type `ResponseUsage` which describes the structure of the usage data returned in the OpenRouter completions response, including prompt, completion, and total token counts.
SOURCE: https://openrouter.ai/docs/api-reference/overview.mdx#_snippet_4

LANGUAGE: TypeScript
CODE:
```
// If the provider returns usage, we pass it down
// as-is. Otherwise, we count using the GPT-4 tokenizer.

type ResponseUsage = {
  /** Including images and tools if any */
  prompt_tokens: number;
  /** The tokens generated */
  completion_tokens: number;
  /** Sum of the above two fields */
  total_tokens: number;
};
```

----------------------------------------

TITLE: Function: registerOperatorWithFeeDestination (Nonpayable)
DESCRIPTION: Registers the caller as an operator with a specified fee destination address. This function modifies the contract state and requires a transaction.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_10

LANGUAGE: JSON
CODE:
```
{
    "inputs": [
      { "internalType": "address", "name": "_feeDestination", "type": "address" }
    ],
    "name": "registerOperatorWithFeeDestination",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Function: transferTokenPreApproved (ABI)
DESCRIPTION: Defines a non-payable function named 'transferTokenPreApproved'. It takes no inputs and returns no outputs. This function likely facilitates a token transfer that has been pre-approved.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_18

LANGUAGE: JSON
CODE:
```
{
    "name": "transferTokenPreApproved",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Event: Transferred
DESCRIPTION: This event is emitted when a transfer operation is successfully completed, detailing the recipient, amount spent, and currency used.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_3

LANGUAGE: JSON
CODE:
```
{
        "anonymous": false,
        "inputs": [
          {
            "indexed": false,
            "internalType": "address payable",
            "name": "recipient",
            "type": "address"
          },
          {
            "indexed": false,
            "internalType": "uint256",
            "name": "spentAmount",
            "type": "uint256"
          },
          {
            "indexed": false,
            "internalType": "address",
            "name": "spentCurrency",
            "type": "address"
          }
        ],
        "name": "Transferred",
        "type": "event"
      }
```

----------------------------------------

TITLE: Function: paused (View)
DESCRIPTION: Checks if the contract is currently in a paused state. This is a view function and does not modify the contract state.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_7

LANGUAGE: JSON
CODE:
```
{
    "inputs": [],
    "name": "paused",
    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
    "stateMutability": "view",
    "type": "function"
  }
```

----------------------------------------

TITLE: Define transferToken Function ABI (JSON)
DESCRIPTION: Defines the ABI entry for the `transferToken` function. This function is non-payable and accepts a `TransferIntent` struct and Permit2 signature transfer data. It is used for transferring tokens using the Permit2 mechanism.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_17

LANGUAGE: JSON
CODE:
```
{
    inputs: [
      {
        components: [
          { internalType: 'uint256', name: 'recipientAmount', type: 'uint256' },
          { internalType: 'uint256', name: 'deadline', type: 'uint256' },
          {
            internalType: 'address payable',
            name: 'recipient',
            type: 'address',
          },
          {
            internalType: 'address',
            name: 'recipientCurrency',
            type: 'address',
          },
          {
            internalType: 'address',
            name: 'refundDestination',
            type: 'address',
          },
          { internalType: 'uint256', name: 'feeAmount', type: 'uint256' },
          { internalType: 'bytes16', name: 'id', type: 'bytes16' },
          { internalType: 'address', name: 'operator', type: 'address' },
          { internalType: 'bytes', name: 'signature', type: 'bytes' },
          { internalType: 'bytes', name: 'prefix', type: 'bytes' },
        ],
        internalType: 'struct TransferIntent',
        name: '_intent',
        type: 'tuple',
      },
      {
        components: [
          {
            components: [
              {
                components: [
                  { internalType: 'address', name: 'token', type: 'address' },
                  { internalType: 'uint256', name: 'amount', type: 'uint256' },
                ],
                internalType: 'struct ISignatureTransfer.TokenPermissions',
                name: 'permitted',
                type: 'tuple',
              },
              { internalType: 'uint256', name: 'nonce', type: 'uint256' },
              { internalType: 'uint256', name: 'deadline', type: 'uint256' },
            ],
            internalType: 'struct ISignatureTransfer.PermitTransferFrom',
            name: 'permit',
            type: 'tuple',
          },
          {
            components: [
              { internalType: 'address', name: 'to', type: 'address' },
              {
                internalType: 'uint256',
                name: 'requestedAmount',
                type: 'uint256',
              },
            ],
            internalType: 'struct ISignatureTransfer.SignatureTransferDetails',
            name: 'transferDetails',
            type: 'tuple',
          },
          { internalType: 'bytes', name: 'signature', type: 'bytes' },
        ],
        internalType: 'struct Permit2SignatureTransferData',
        name: '_signatureTransferData',
        type: 'tuple',
      },
    ],
    name: 'transferToken',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function'
  }
```

----------------------------------------

TITLE: Define transferNative Function ABI (JSON)
DESCRIPTION: Defines the ABI entry for the `transferNative` function. This function is payable and accepts a `TransferIntent` struct as input. It is used for transferring native currency.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_15

LANGUAGE: JSON
CODE:
```
{
          internalType: 'uint256', name: 'recipientAmount', type: 'uint256' },
          { internalType: 'uint256', name: 'deadline', type: 'uint256' },
          {
            internalType: 'address payable',
            name: 'recipient',
            type: 'address',
          },
          {
            internalType: 'address',
            name: 'recipientCurrency',
            type: 'address',
          },
          {
            internalType: 'address',
            name: 'refundDestination',
            type: 'address',
          },
          { internalType: 'uint256', name: 'feeAmount', type: 'uint256' },
          { internalType: 'bytes16', name: 'id', type: 'bytes16' },
          { internalType: 'address', name: 'operator', type: 'address' },
          { internalType: 'bytes', name: 'signature', type: 'bytes' },
          { internalType: 'bytes', name: 'prefix', type: 'bytes' },
        ],
        internalType: 'struct TransferIntent',
        name: '_intent',
        type: 'tuple',
      },
    ],
    name: 'transferNative',
    outputs: [],
    stateMutability: 'payable',
    type: 'function'
  }
```

----------------------------------------

TITLE: Print JSON Response - Python
DESCRIPTION: Prints the JSON response object received from an API call. This is a common way to inspect the result of a request in Python.
SOURCE: https://openrouter.ai/docs/api-reference/authentication/exchange-authorization-code-for-api-key.mdx#_snippet_16

LANGUAGE: Python
CODE:
```
print(response.json())
```

----------------------------------------

TITLE: GET Model Endpoints - OpenRouter API - HTTP
DESCRIPTION: Defines the HTTP method and endpoint path for listing available endpoints for a specific model on the OpenRouter API. Requires 'author' and 'slug' path parameters.
SOURCE: https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.mdx#_snippet_0

LANGUAGE: http
CODE:
```
GET https://openrouter.ai/api/v1/models/{author}/{slug}/endpoints
```

----------------------------------------

TITLE: HTTP Request Method and Endpoint
DESCRIPTION: Specifies the HTTP method and endpoint for retrieving generation metadata.
SOURCE: https://openrouter.ai/docs/api-reference/get-a-generation.mdx#_snippet_0

LANGUAGE: http
CODE:
```
GET https://openrouter.ai/api/v1/generation
```

----------------------------------------

TITLE: HTTP Request Method and Endpoint
DESCRIPTION: Specifies the HTTP method (POST) and the API endpoint for chat completions on OpenRouter.ai, along with the required Content-Type header.
SOURCE: https://openrouter.ai/docs/api-reference/chat-completion.mdx#_snippet_0

LANGUAGE: http
CODE:
```
POST https://openrouter.ai/api/v1/chat/completions
Content-Type: application/json
```

----------------------------------------

TITLE: Example Model List Response JSON
DESCRIPTION: This JSON object shows the expected format for the response from the provider's 'List Models' endpoint. It includes details for each model such as ID, name, creation timestamp, context length, optional description and max completion tokens, required quantization type, and pricing information per token, image, and request. Note that pricing fields are strings in USD to avoid floating-point issues.
SOURCE: https://openrouter.ai/docs/use-cases/for-providers.mdx#_snippet_0

LANGUAGE: json
CODE:
```
{
  "data": [
    {
      "id": "anthropic/claude-2.0",
      "name": "Anthropic: Claude v2.0",
      "created": 1690502400,
      "description": "Anthropic's flagship model...", // Optional
      "context_length": 100000, // Required
      "max_completion_tokens": 4096, // Optional
      "quantization": "fp8", // Required
      "pricing": {
        "prompt": "0.000008", // pricing per 1 token
        "completion": "0.000024", // pricing per 1 token
        "image": "0", // pricing per 1 image
        "request": "0" // pricing per 1 request
      }
    }
  ]
}
```

----------------------------------------

TITLE: Define transferOwnership Function ABI (JSON)
DESCRIPTION: Defines the ABI entry for the `transferOwnership` function. This function is non-payable and accepts a new owner address as input. It is used to transfer ownership of the contract.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_16

LANGUAGE: JSON
CODE:
```
{
    inputs: [{ internalType: 'address', name: 'newOwner', type: 'address' }],
    name: 'transferOwnership',
    outputs: [],
    stateMutability: 'nonpayable',
    type: 'function'
  }
```

----------------------------------------

TITLE: Function: unpause (ABI)
DESCRIPTION: Defines a non-payable function named 'unpause'. It takes no inputs and returns no outputs. This function is likely used to resume operations on a paused contract.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_19

LANGUAGE: JSON
CODE:
```
{
    "inputs": [],
    "name": "unpause",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
```

----------------------------------------

TITLE: Function: owner (View)
DESCRIPTION: Retrieves the address of the contract owner. This is a view function and does not modify the contract state.
SOURCE: https://openrouter.ai/docs/use-cases/crypto-api.mdx#_snippet_5

LANGUAGE: JSON
CODE:
```
{
    "inputs": [],
    "name": "owner",
    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
  }
```
