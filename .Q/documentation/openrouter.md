---
title: Frameworks
subtitle: Using OpenRouter with Frameworks
headline: Integration Frameworks | OpenRouter SDK and Library Support
canonical-url: 'https://openrouter.ai/docs/community/frameworks'
'og:site_name': OpenRouter Documentation
'og:title': Integration Frameworks - OpenRouter SDK Support
'og:description': >-
  Integrate OpenRouter using popular frameworks and SDKs. Complete guides for
  OpenAI SDK, LangChain, PydanticAI, and Vercel AI SDK integration.
'og:image':
  type: url
  value: >-
    https://openrouter.ai/dynamic-og?title=Frameworks&description=Frameworks%20and%20SDK%20Support
'og:image:width': 1200
'og:image:height': 630
'twitter:card': summary_large_image
'twitter:site': '@OpenRouterAI'
noindex: false
nofollow: false
---

import { API_KEY_REF } from '../../../imports/constants';

You can find a few examples of using OpenRouter with other frameworks in [this Github repository](https://github.com/OpenRouterTeam/openrouter-examples). Here are some examples:

## Using the OpenAI SDK

- Using `pip install openai`: [github](https://github.com/OpenRouterTeam/openrouter-examples-python/blob/main/src/openai_test.py).
- Using `npm i openai`: [github](https://github.com/OpenRouterTeam/openrouter-examples/blob/main/examples/openai/index.ts).
  <Tip>
    You can also use
    [Grit](https://app.grit.io/studio?key=RKC0n7ikOiTGTNVkI8uRS) to
    automatically migrate your code. Simply run `npx @getgrit/launcher
    openrouter`.
  </Tip>

<CodeGroup>

```typescript title="TypeScript"
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

```python title="Python"
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

</CodeGroup>

## Using LangChain

- Using [LangChain for Python](https://github.com/langchain-ai/langchain): [github](https://github.com/alexanderatallah/openrouter-streamlit/blob/main/pages/2_Langchain_Quickstart.py)
- Using [LangChain.js](https://github.com/langchain-ai/langchainjs): [github](https://github.com/OpenRouterTeam/openrouter-examples/blob/main/examples/langchain/index.ts)
- Using [Streamlit](https://streamlit.io/): [github](https://github.com/alexanderatallah/openrouter-streamlit)

<CodeGroup>

```typescript title="TypeScript"
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

```python title="Python"
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

</CodeGroup>

---

## Using PydanticAI

[PydanticAI](https://github.com/pydantic/pydantic-ai) provides a high-level interface for working with various LLM providers, including OpenRouter.

### Installation

```bash
pip install 'pydantic-ai-slim[openai]'
```

### Configuration

You can use OpenRouter with PydanticAI through its OpenAI-compatible interface:

```python
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

For more details about using PydanticAI with OpenRouter, see the [PydanticAI documentation](https://ai.pydantic.dev/models/#api_key-argument).

---

## Vercel AI SDK

You can use the [Vercel AI SDK](https://www.npmjs.com/package/ai) to integrate OpenRouter with your Next.js app. To get started, install [@openrouter/ai-sdk-provider](https://github.com/OpenRouterTeam/ai-sdk-provider):

```bash
npm install @openrouter/ai-sdk-provider
```

And then you can use [streamText()](https://sdk.vercel.ai/docs/reference/ai-sdk-core/stream-text) API to stream text from OpenRouter.

<CodeGroup>

```typescript title="TypeScript"
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

</CodeGroup>

## Mastra

Integrate OpenRouter with Mastra to access a variety of AI models through a unified interface. This guide provides complete examples from basic setup to advanced configurations.

### Step 1: Initialize a new Mastra project

The simplest way to start is using the automatic project creation:

```bash
# Create a new project using create-mastra
npx create-mastra@latest
```

You'll be guided through prompts to set up your project. For this example, select:

- Name your project: my-mastra-openrouter-app
- Components: Agents (recommended)
- For default provider, select OpenAI (recommended) - we'll configure OpenRouter manually later
- Optionally include example code

For detailed instructions on setting up a Mastra project manually or adding Mastra to an existing project, refer to the [official Mastra documentation](https://mastra.ai/en/docs/getting-started/installation).

### Step 2: Configure your environment variables

After creating your project with `create-mastra`, you'll find a `.env.development` file in your project root. Since we selected OpenAI during setup but will be using OpenRouter instead:

1. Open the `.env.development` file
2. Remove or comment out the `OPENAI_API_KEY` line
3. Add your OpenRouter API key:

```
# .env.development
# OPENAI_API_KEY=your-openai-key  # Comment out or remove this line
OPENROUTER_API_KEY=sk-or-your-api-key-here
```

You can also remove the `@ai-sdk/openai` package since we'll be using OpenRouter instead:

```bash
npm uninstall @ai-sdk/openai
```

```bash
npm install @openrouter/ai-sdk-provider
```

### Step 3: Configure your agent to use OpenRouter

After setting up your Mastra project, you'll need to modify the agent files to use OpenRouter instead of the default OpenAI provider.

If you used `create-mastra`, you'll likely have a file at `src/mastra/agents/agent.ts` or similar. Replace its contents with:

```typescript
import { Agent } from '@mastra/core/agent';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

// Initialize OpenRouter provider
const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

// Create an agent
export const assistant = new Agent({
  model: openrouter('anthropic/claude-3-opus'),
  name: 'Assistant',
  instructions:
    'You are a helpful assistant with expertise in technology and science.',
});
```

Also make sure to update your Mastra entry point at `src/mastra/index.ts` to use your renamed agent:

```typescript
import { Mastra } from '@mastra/core';

import { assistant } from './agents/agent'; // Update the import path if you used a different filename

export const mastra = new Mastra({
  agents: { assistant }, // Use the same name here as you exported from your agent file
});
```

### Step 4: Running the Application

Once you've configured your agent to use OpenRouter, you can run the Mastra development server:

```bash
npm run dev
```

This will start the Mastra development server and make your agent available at:

- REST API endpoint: `http://localhost:4111/api/agents/assistant/generate`
- Interactive playground: `http://localhost:4111`

The Mastra playground provides a user-friendly interface where you can interact with your agent and test its capabilities without writing any additional code.

You can also test the API endpoint using curl if needed:

```bash
curl -X POST http://localhost:4111/api/agents/assistant/generate \
-H "Content-Type: application/json" \
-d '{"messages": ["What are the latest advancements in quantum computing?"]}'
```

### Basic Integration with Mastra

The simplest way to integrate OpenRouter with Mastra is by using the OpenRouter AI provider with Mastra's Agent system:

```typescript
import { Agent } from '@mastra/core/agent';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

// Initialize the OpenRouter provider
const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

// Create an agent using OpenRouter
const assistant = new Agent({
  model: openrouter('anthropic/claude-3-opus'),
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});

// Generate a response
const response = await assistant.generate([
  {
    role: 'user',
    content: 'Tell me about renewable energy sources.',
  },
]);

console.log(response.text);
```

### Advanced Configuration

For more control over your OpenRouter requests, you can pass additional configuration options:

```typescript
import { Agent } from '@mastra/core/agent';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

// Initialize with advanced options
const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
  extraBody: {
    reasoning: {
      max_tokens: 10,
    },
  },
});

// Create an agent with model-specific options
const chefAgent = new Agent({
  model: openrouter('anthropic/claude-3.7-sonnet:thinking', {
    extraBody: {
      reasoning: {
        max_tokens: 10,
      },
    },
  }),
  name: 'Chef',
  instructions: 'You are a chef assistant specializing in French cuisine.',
});
```

### Provider-Specific Options

You can also pass provider-specific options in your requests:

```typescript
// Get a response with provider-specific options
const response = await chefAgent.generate([
  {
    role: 'system',
    content:
      'You are Chef Michel, a culinary expert specializing in ketogenic (keto) diet...',
    providerOptions: {
      // Provider-specific options - key can be 'anthropic' or 'openrouter'
      anthropic: {
        cacheControl: { type: 'ephemeral' },
      },
    },
  },
  {
    role: 'user',
    content: 'Can you suggest a keto breakfast?',
  },
]);
```

### Using Multiple Models with OpenRouter

OpenRouter gives you access to various models from different providers. Here's how to use multiple models:

```typescript
import { Agent } from '@mastra/core/agent';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

// Create agents using different models
const claudeAgent = new Agent({
  model: openrouter('anthropic/claude-3-opus'),
  name: 'ClaudeAssistant',
  instructions: 'You are a helpful assistant powered by Claude.',
});

const gptAgent = new Agent({
  model: openrouter('openai/gpt-4'),
  name: 'GPTAssistant',
  instructions: 'You are a helpful assistant powered by GPT-4.',
});

// Use different agents based on your needs
const claudeResponse = await claudeAgent.generate([
  {
    role: 'user',
    content: 'Explain quantum mechanics simply.',
  },
]);
console.log(claudeResponse.text);

const gptResponse = await gptAgent.generate([
  {
    role: 'user',
    content: 'Explain quantum mechanics simply.',
  },
]);
console.log(gptResponse.text);
```

### Resources

For more information and detailed documentation, check out these resources:

- [OpenRouter Documentation](https://openrouter.ai/docs) - Learn about OpenRouter's capabilities and available models
- [Mastra Documentation](https://mastra.ai/docs) - Comprehensive documentation for the Mastra framework
- [AI SDK Documentation](https://sdk.vercel.ai/docs) - Detailed information about the AI SDK that powers Mastra's model interactions

