TITLE: Define and Run Pydantic-AI Agent with Tools (Python)
DESCRIPTION: This snippet defines a Pydantic-AI Agent for a dice game. It registers two tools: `roll_die` using `@agent.tool_plain` as it doesn't require agent context, and `get_player_name` using `@agent.tool` which accesses dependencies via `RunContext`. The agent is then run with a user prompt and a dependency (the player's name).
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_0

LANGUAGE: python
CODE:
```
import random

from pydantic_ai import Agent, RunContext

agent = Agent(
    'google-gla:gemini-1.5-flash',  # (1)!
    deps_type=str,  # (2)!
    system_prompt=(
        "You're a dice game, you should roll the die and see if the number "
        "you get back matches the user's guess. If so, tell them they're a winner. "
        "Use the player's name in the response."
    ),
)


@agent.tool_plain  # (3)!
def roll_die() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))


@agent.tool  # (4)!
def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps


dice_result = agent.run_sync('My guess is 4', deps='Anne')  # (5)!
print(dice_result.output)
#>
```

----------------------------------------

TITLE: Basic Agent Implementation with PydanticAI
DESCRIPTION: A simple example showing how to create and use a basic PydanticAI agent with a static system prompt. The agent uses the Google Gemini model to answer a query about the origin of 'hello world' with a concise response.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/README.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

# Define a very simple agent including the model to use, you can also set the model when running the agent.
agent = Agent(
    'google-gla:gemini-1.5-flash',
    # Register a static system prompt using a keyword argument to the agent.
    # For more complex dynamically-generated system prompts, see the example below.
    system_prompt='Be concise, reply with one sentence.',
)

# Run the agent synchronously, conducting a conversation with the LLM.
# Here the exchange should be very short: PydanticAI will send the system prompt and the user query to the LLM,
# the model will return a text response. See below for a more complex run.
result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

----------------------------------------

TITLE: Simulating a Roulette Wheel with PydanticAI Agent (Python)
DESCRIPTION: This snippet demonstrates how to create a PydanticAI Agent with a tool. It defines an Agent that takes an integer dependency and produces a boolean output, simulating a roulette wheel by checking if a provided square matches the dependency number using an asynchronous tool function. The example shows how to run the agent synchronously with a text prompt and a dependency value.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_0

LANGUAGE: Python
CODE:
```
from pydantic_ai import Agent, RunContext

roulette_agent = Agent(  # (1)!
    'openai:gpt-4o',
    deps_type=int,
    output_type=bool,
    system_prompt=(
        'Use the `roulette_wheel` function to see if the '
        'customer has won based on the number they provide.'
    ),
)


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:  # (2)!
    """check if the square is a winner"""
    return 'winner' if square == ctx.deps else 'loser'


# Run the agent
success_number = 18  # (3)!
result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
print(result.output)  # (4)!
#> True

result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
print(result.output)
#> False
```

----------------------------------------

TITLE: Evaluate Recipe Generation with LLMJudge (Python)
DESCRIPTION: This snippet defines Pydantic models for customer orders and recipes, sets up an AI agent for recipe generation, and creates a `pydantic-evals` Dataset to evaluate the agent's output using `LLMJudge` and `IsInstance` evaluators. It demonstrates how to define case-specific and dataset-level evaluation rubrics and run the evaluation process.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_5

LANGUAGE: python
CODE:
```
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from pydantic_ai import Agent, format_as_xml
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance, LLMJudge


class CustomerOrder(BaseModel):  # (1)!
    dish_name: str
    dietary_restriction: str | None = None


class Recipe(BaseModel):
    ingredients: list[str]
    steps: list[str]


recipe_agent = Agent(
    'groq:llama-3.3-70b-versatile',
    output_type=Recipe,
    system_prompt=(
        'Generate a recipe to cook the dish that meets the dietary restrictions.'
    ),
)


async def transform_recipe(customer_order: CustomerOrder) -> Recipe:  # (2)!
    r = await recipe_agent.run(format_as_xml(customer_order))
    return r.output


recipe_dataset = Dataset[CustomerOrder, Recipe, Any](  # (3)!
    cases=[
        Case(
            name='vegetarian_recipe',
            inputs=CustomerOrder(
                dish_name='Spaghetti Bolognese', dietary_restriction='vegetarian'
            ),
            expected_output=None,  # (4)
            metadata={'focus': 'vegetarian'},
            evaluators=(
                LLMJudge(  # (5)!
                    rubric='Recipe should not contain meat or animal products',
                ),
            ),
        ),
        Case(
            name='gluten_free_recipe',
            inputs=CustomerOrder(
                dish_name='Chocolate Cake', dietary_restriction='gluten-free'
            ),
            expected_output=None,
            metadata={'focus': 'gluten-free'},
            # Case-specific evaluator with a focused rubric
            evaluators=(
                LLMJudge(
                    rubric='Recipe should not contain gluten or wheat products',
                ),
            ),
        ),
    ],
    evaluators=[  # (6)!
        IsInstance(type_name='Recipe'),
        LLMJudge(
            rubric='Recipe should have clear steps and relevant ingredients',
            include_input=True,
            model='anthropic:claude-3-7-sonnet-latest',  # (7)!
        ),
    ],
)


report = recipe_dataset.evaluate_sync(transform_recipe)
print(report)

```

----------------------------------------

TITLE: Maintaining Conversation History Across PydanticAI Runs (Python)
DESCRIPTION: This snippet shows how to conduct a multi-turn conversation using a PydanticAI Agent by passing the message history from a previous run (`result1.new_messages()`) to the subsequent run (`result2`). This allows the model to understand the context of the conversation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_9

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')

# First run
result1 = agent.run_sync('Who was Albert Einstein?')
print(result1.output)
#> Albert Einstein was a German-born theoretical physicist.

# Second run, passing previous messages
result2 = agent.run_sync(
    'What was his most famous equation?',
    message_history=result1.new_messages(),  # (1)!
)
print(result2.output)
#> Albert Einstein's most famous equation is (E = mc^2).
```

----------------------------------------

TITLE: Basic Hello World Agent Implementation in Python with PydanticAI
DESCRIPTION: Demonstrates basic usage of PydanticAI by creating a simple agent that uses Gemini 1.5 Flash model to answer a question with a concise response. Shows agent initialization, system prompt configuration, and synchronous execution.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/index.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent(
    'google-gla:gemini-1.5-flash',
    system_prompt='Be concise, reply with one sentence.',
)

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

----------------------------------------

TITLE: Advanced Bank Support Agent with Tools and Dependency Injection
DESCRIPTION: Implements a bank support agent using PydanticAI with structured output validation, dependency injection, dynamic system prompts, and tool functions. Shows integration with external services and type-safe implementation patterns.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/index.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn


@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn


class SupportOutput(BaseModel):
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description='Risk level of query', ge=0, le=10)


support_agent = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    system_prompt=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)


@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


@support_agent.tool
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool
) -> float:
    """Returns the customer's current account balance."""
    return await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )


async def main():
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    result = await support_agent.run('What is my balance?', deps=deps)
    print(result.output)
    """
    support_advice='Hello John, your current account balance, including pending transactions, is $123.45.' block_card=False risk=1
    """

    result = await support_agent.run('I just lost my card!', deps=deps)
    print(result.output)
    """
    support_advice="I'm sorry to hear that, John. We are temporarily blocking your card to prevent unauthorized transactions." block_card=True risk=8
    """
```

----------------------------------------

TITLE: Advanced PydanticAI Implementation with Tools and Dependency Injection
DESCRIPTION: A comprehensive example demonstrating how to create a bank support agent using PydanticAI with dependency injection, tools, dynamic system prompts, and structured responses. The agent interacts with a database to retrieve customer information and provide support based on customer queries.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/README.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn


# SupportDependencies is used to pass data, connections, and logic into the model that will be needed when running
# system prompt and tool functions. Dependency injection provides a type-safe way to customise the behavior of your agents.
@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn


# This pydantic model defines the structure of the output returned by the agent.
class SupportOutput(BaseModel):
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description='Risk level of query', ge=0, le=10)


# This agent will act as first-tier support in a bank.
# Agents are generic in the type of dependencies they accept and the type of output they return.
# In this case, the support agent has type `Agent[SupportDependencies, SupportOutput]`.
support_agent = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
    # The response from the agent will, be guaranteed to be a SupportOutput,
    # if validation fails the agent is prompted to try again.
    output_type=SupportOutput,
    system_prompt=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)


# Dynamic system prompts can make use of dependency injection.
# Dependencies are carried via the `RunContext` argument, which is parameterized with the `deps_type` from above.
# If the type annotation here is wrong, static type checkers will catch it.
@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


# `tool` let you register functions which the LLM may call while responding to a user.
# Again, dependencies are carried via `RunContext`, any other arguments become the tool schema passed to the LLM.
# Pydantic is used to validate these arguments, and errors are passed back to the LLM so it can retry.
@support_agent.tool
async def customer_balance(
        ctx: RunContext[SupportDependencies], include_pending: bool
) -> float:
    """Returns the customer's current account balance."""
    # The docstring of a tool is also passed to the LLM as the description of the tool.
    # Parameter descriptions are extracted from the docstring and added to the parameter schema sent to the LLM.
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
    return balance


...  # In a real use case, you'd add more tools and a longer system prompt


async def main():
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    # Run the agent asynchronously, conducting a conversation with the LLM until a final response is reached.
    # Even in this fairly simple case, the agent will exchange multiple messages with the LLM as tools are called to retrieve an output.
    result = await support_agent.run('What is my balance?', deps=deps)
    # The `result.output` will be validated with Pydantic to guarantee it is a `SupportOutput`. Since the agent is generic,
    # it'll also be typed as a `SupportOutput` to aid with static type checking.
    print(result.output)
    """
    support_advice='Hello John, your current account balance, including pending transactions, is $123.45.' block_card=False risk=1
    """

    result = await support_agent.run('I just lost my card!', deps=deps)
    print(result.output)
    """
    support_advice="I'm sorry to hear that, John. We are temporarily blocking your card to prevent unauthorized transactions." block_card=True risk=8
    """
```

----------------------------------------

TITLE: Fixing RuntimeError with nest-asyncio in Python
DESCRIPTION: This code snippet imports and applies the `nest_asyncio` library to resolve event loop conflicts that can occur when running PydanticAI in interactive environments like Jupyter Notebooks, Google Colab, or Marimo. It should be executed before running any PydanticAI agents.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/troubleshooting.md#_snippet_0

LANGUAGE: python
CODE:
```
import nest_asyncio

nest_asyncio.apply()
```

----------------------------------------

TITLE: Implementing Agent Delegation with PydanticAI
DESCRIPTION: Demonstrates a simple agent delegation pattern where a joke selection agent uses a joke generation agent via a tool. Shows usage tracking across multiple agents and basic error handling.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/multi-agent-applications.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits

joke_selection_agent = Agent(
    'openai:gpt-4o',
    system_prompt=(
        'Use the `joke_factory` to generate some jokes, then choose the best. '
        'You must return just a single joke.'
    ),
)
joke_generation_agent = Agent(
    'google-gla:gemini-1.5-flash', output_type=list[str]
)

@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[None], count: int) -> list[str]:
    r = await joke_generation_agent.run(
        f'Please generate {count} jokes.',
        usage=ctx.usage,
    )
    return r.output

result = joke_selection_agent.run_sync(
    'Tell me a joke.',
    usage_limits=UsageLimits(request_limit=5, total_tokens_limit=300),
)
print(result.output)
print(result.usage())
```

----------------------------------------

TITLE: function_tool_output.py
DESCRIPTION: This snippet illustrates the various return types supported by Pydantic AI function tools. Tools can return anything serializable by Pydantic to JSON, including standard types (`datetime`), Pydantic models (`User`), and multi-modal content types like `ImageUrl` and `DocumentUrl`. The agent uses these tools to answer user queries based on the returned data.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_3

LANGUAGE: python
CODE:
```
from datetime import datetime\n\nfrom pydantic import BaseModel\n\nfrom pydantic_ai import Agent, DocumentUrl, ImageUrl\nfrom pydantic_ai.models.openai import OpenAIResponsesModel\n\n\nclass User(BaseModel):\n    name: str\n    age: int\n\n\nagent = Agent(model=OpenAIResponsesModel('gpt-4o'))\n\n\n@agent.tool_plain\ndef get_current_time() -> datetime:\n    return datetime.now()\n\n\n@agent.tool_plain\ndef get_user() -> User:\n    return User(name='John', age=30)\n\n\n@agent.tool_plain\ndef get_company_logo() -> ImageUrl:\n    return ImageUrl(url='https://iili.io/3Hs4FMg.png')\n\n\n@agent.tool_plain\ndef get_document() -> DocumentUrl:\n    return DocumentUrl(url='https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf')\n\n\nresult = agent.run_sync('What time is it?')\nprint(result.output)\n#> The current time is 10:45 PM on April 17, 2025.\n\nresult = agent.run_sync('What is the user name?')\nprint(result.output)\n#> The user's name is John.\n\nresult = agent.run_sync('What is the company name in the logo?')\nprint(result.output)\n#> The company name in the logo is \"Pydantic.\"\n\nresult = agent.run_sync('What is the main content of the document?')\nprint(result.output)\n#> The document contains just the text \"Dummy PDF file.\"\n
```

----------------------------------------

TITLE: Disabling Real Model Requests Globally (Python)
DESCRIPTION: Set this global flag to 'False' to prevent any accidental calls to non-test language models during the execution of your test suite, ensuring tests are isolated and deterministic.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/testing.md#_snippet_0

LANGUAGE: python
CODE:
```
ALLOW_MODEL_REQUESTS=False
```

----------------------------------------

TITLE: Installing PydanticAI Slim with Multiple Integrations
DESCRIPTION: Installation command showing how to install slim version with multiple optional dependencies (OpenAI, VertexAI, and Logfire).
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/install.md#2025-04-22_snippet_4

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[openai,vertexai,logfire]"
```

----------------------------------------

TITLE: Basic OpenAI Model Initialization
DESCRIPTION: Simple initialization of an OpenAI model using the Agent class with model name reference.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')
...
```

----------------------------------------

TITLE: Accessing Messages During and After Streaming - Pydantic-AI - Python
DESCRIPTION: This example demonstrates how to use the `StreamedRunResult` object to access messages during the streaming process (showing only the request initially) and after the stream completes (showing both request and final response). It also shows how to iterate over the streamed text output.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/message-history.md#_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')


async def main():
    async with agent.run_stream('Tell me a joke.') as result:
        # incomplete messages before the stream finishes
        print(result.all_messages())
        """
        [
            ModelRequest(
                parts=[
                    SystemPromptPart(
                        content='Be a helpful assistant.',
                        timestamp=datetime.datetime(...),
                        dynamic_ref=None,
                        part_kind='system-prompt',
                    ),
                    UserPromptPart(
                        content='Tell me a joke.',
                        timestamp=datetime.datetime(...),
                        part_kind='user-prompt',
                    ),
                ],
                instructions=None,
                kind='request',
            )
        ]
        """

        async for text in result.stream_text():
            print(text)
            # > Did you hear
            # > Did you hear about the toothpaste
            # > Did you hear about the toothpaste scandal? They called
            # > Did you hear about the toothpaste scandal? They called it Colgate.

        # complete messages once the stream finishes
        print(result.all_messages())
        """
        [
            ModelRequest(
                parts=[
                    SystemPromptPart(
                        content='Be a helpful assistant.',
                        timestamp=datetime.datetime(...),
                        dynamic_ref=None,
                        part_kind='system-prompt',
                    ),
                    UserPromptPart(
                        content='Tell me a joke.',
                        timestamp=datetime.datetime(...),
                        part_kind='user-prompt',
                    ),
                ],
                instructions=None,
                kind='request',
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='Did you hear about the toothpaste scandal? They called it Colgate.',
                        part_kind='text',
                    )
                ],
                usage=Usage(
                    requests=0,
                    request_tokens=50,
                    response_tokens=12,
                    total_tokens=62,
                    details=None,
                ),
                model_name='gpt-4o',
                timestamp=datetime.datetime(...),
                kind='response',
            ),
        ]
        """

```

----------------------------------------

TITLE: Defining Pydantic-Graph Human-in-the-Loop Q&A Graph Structure - Python
DESCRIPTION: This snippet defines the nodes and state for a Pydantic-Graph representing a human-in-the-loop question and answer flow. It includes nodes for asking a question (Ask), getting user input (Answer), evaluating the answer using an AI (Evaluate), and reprimanding the user (Reprimand), managing the graph state using QuestionState. The graph allows for state persistence to pause and resume the process waiting for user input.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_13

LANGUAGE: python
CODE:
```
from __future__ import annotations as _annotations

from dataclasses import dataclass, field

from groq import BaseModel
from pydantic_graph import (
    BaseNode,
    End,
    Graph,
    GraphRunContext,
)

from pydantic_ai import Agent, format_as_xml
from pydantic_ai.messages import ModelMessage

ask_agent = Agent('openai:gpt-4o', output_type=str, instrument=True)


@dataclass
class QuestionState:
    question: str | None = None
    ask_agent_messages: list[ModelMessage] = field(default_factory=list)
    evaluate_agent_messages: list[ModelMessage] = field(default_factory=list)


@dataclass
class Ask(BaseNode[QuestionState]):
    async def run(self, ctx: GraphRunContext[QuestionState]) -> Answer:
        result = await ask_agent.run(
            'Ask a simple question with a single correct answer.',
            message_history=ctx.state.ask_agent_messages,
        )
        ctx.state.ask_agent_messages += result.new_messages()
        ctx.state.question = result.output
        return Answer(result.output)


@dataclass
class Answer(BaseNode[QuestionState]):
    question: str

    async def run(self, ctx: GraphRunContext[QuestionState]) -> Evaluate:
        answer = input(f'{self.question}: ')
        return Evaluate(answer)


class EvaluationResult(BaseModel, use_attribute_docstrings=True):
    correct: bool
    """Whether the answer is correct."""
    comment: str
    """Comment on the answer, reprimand the user if the answer is wrong."""


evaluate_agent = Agent(
    'openai:gpt-4o',
    output_type=EvaluationResult,
    system_prompt='Given a question and answer, evaluate if the answer is correct.',
)


@dataclass
class Evaluate(BaseNode[QuestionState, None, str]):
    answer: str

    async def run(
        self,
        ctx: GraphRunContext[QuestionState],
    ) -> End[str] | Reprimand:
        assert ctx.state.question is not None
        result = await evaluate_agent.run(
            format_as_xml({'question': ctx.state.question, 'answer': self.answer}),
            message_history=ctx.state.evaluate_agent_messages,
        )
        ctx.state.evaluate_agent_messages += result.new_messages()
        if result.output.correct:
            return End(result.output.comment)
        else:
            return Reprimand(result.output.comment)


@dataclass
class Reprimand(BaseNode[QuestionState]):
    comment: str

    async def run(self, ctx: GraphRunContext[QuestionState]) -> Ask:
        print(f'Comment: {self.comment}')
        ctx.state.question = None
        return Ask()


question_graph = Graph(
    nodes=(Ask, Answer, Evaluate, Reprimand), state_type=QuestionState
)
```

----------------------------------------

TITLE: Implementing Multi-Agent Flight Booking System in Python
DESCRIPTION: The main Python script for the flight booking system. It contains the implementation of the multi-agent workflow, including agent definitions, delegation logic, and the booking process.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/flight-booking.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/flight_booking.py
```

----------------------------------------

TITLE: Handling Olympics Location Data with Pydantic-AI
DESCRIPTION: Demonstrates using Pydantic-AI to extract structured location data about Olympic games using a Gemini model. Shows how to define output types and access usage statistics.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/output.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from pydantic import BaseModel

from pydantic_ai import Agent


class CityLocation(BaseModel):
    city: str
    country: str


agent = Agent('google-gla:gemini-1.5-flash', output_type=CityLocation)
result = agent.run_sync('Where were the olympics held in 2012?')
print(result.output)
#> city='London' country='United Kingdom'
print(result.usage())
#> Usage(requests=1, request_tokens=57, response_tokens=8, total_tokens=65, details=None)
```

----------------------------------------

TITLE: Unit Testing Weather Agent with TestModel in Python
DESCRIPTION: This snippet shows how to write a unit test for the `run_weather_forecast` function using `pydantic-ai`'s `TestModel`. It demonstrates capturing messages, overriding the agent's model with `TestModel`, running the function, asserting the stored result, and asserting the captured messages. It also shows setting `pytestmark` and `models.ALLOW_MODEL_REQUESTS`.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/testing.md#_snippet_2

LANGUAGE: python
CODE:
```
from datetime import timezone
import pytest

from dirty_equals import IsNow, IsStr

from pydantic_ai import models, capture_run_messages
from pydantic_ai.models.test import TestModel
from pydantic_ai.messages import (
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    ModelRequest,
)
from pydantic_ai.usage import Usage

from fake_database import DatabaseConn
from weather_app import run_weather_forecast, weather_agent

pytestmark = pytest.mark.anyio  # (1)!
models.ALLOW_MODEL_REQUESTS = False  # (2)!


async def test_forecast():
    conn = DatabaseConn()
    user_id = 1
    with capture_run_messages() as messages:
        with weather_agent.override(model=TestModel()):  # (3)!
            prompt = 'What will the weather be like in London on 2024-11-28?'
            await run_weather_forecast([(prompt, user_id)], conn)  # (4)!

    forecast = await conn.get_forecast(user_id)
    assert forecast == '{"weather_forecast":"Sunny with a chance of rain"}'  # (5)!

    assert messages == [  # (6)!
        ModelRequest(
            parts=[
                SystemPromptPart(
                    content='Providing a weather forecast at the locations the user provides.',
                    timestamp=IsNow(tz=timezone.utc),
                ),
                UserPromptPart(
                    content='What will the weather be like in London on 2024-11-28?',
                    timestamp=IsNow(tz=timezone.utc),  # (7)!
                ),
            ]
        ),
        ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='weather_forecast',
                    args={
                        'location': 'a',
                        'forecast_date': '2024-01-01',  # (8)!
                    },

```

----------------------------------------

TITLE: Continue Agent Conversation with Message History (Python)
DESCRIPTION: Demonstrates how to maintain conversation context across multiple agent runs by passing the message history from a previous run's result (`result1.new_messages()`) to the `message_history` parameter of `agent.run_sync`. This allows the agent to respond based on the prior turn.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/message-history.md#_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync('Explain?', message_history=result1.new_messages())
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            SystemPromptPart(
                content='Be a helpful assistant.',
                timestamp=datetime.datetime(...),
                dynamic_ref=None,
                part_kind='system-prompt',
            ),
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            ),
        ],
        instructions=None,
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.',
                part_kind='text',
            )
        ],
        usage=Usage(
            requests=1,
            request_tokens=60,
            response_tokens=12,
            total_tokens=72,
            details=None,
        ),
        model_name='gpt-4o',
        timestamp=datetime.datetime(...),
        kind='response',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            )
        ],
        instructions=None,
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invented by Samuel Colvin, it needs no explanation.',
                part_kind='text',
            )
        ],
        usage=Usage(
            requests=1,
            request_tokens=61,
            response_tokens=26,
            total_tokens=87,
            details=None,
        ),
        model_name='gpt-4o',
        timestamp=datetime.datetime(...),
        kind='response',
    ),
]
"""
```

----------------------------------------

TITLE: simple_eval_complete.py
DESCRIPTION: This snippet demonstrates a complete evaluation setup using pydantic-evals. It defines a test case (`Case`), a custom evaluator (`MyEvaluator`), a dataset (`Dataset`) containing the case and evaluators, and a simple function (`guess_city`) to be evaluated. Finally, it runs the evaluation synchronously using `evaluate_sync` and prints the resulting report. The comments explain each step of the process.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext, IsInstance

case1 = Case(  # (1)!
    name='simple_case',
    inputs='What is the capital of France?',
    expected_output='Paris',
    metadata={'difficulty': 'easy'},
)


class MyEvaluator(Evaluator[str, str]):
    def evaluate(self, ctx: EvaluatorContext[str, str]) -> float:
        if ctx.output == ctx.expected_output:
            return 1.0
        elif (
            isinstance(ctx.output, str)
            and ctx.expected_output.lower() in ctx.output.lower()
        ):
            return 0.8
        else:
            return 0.0


dataset = Dataset(
    cases=[case1],
    evaluators=[IsInstance(type_name='str'), MyEvaluator()],  # (3)!
)


async def guess_city(question: str) -> str:  # (4)!
    return 'Paris'


report = dataset.evaluate_sync(guess_city)  # (5)!
report.print(include_input=True, include_output=True, include_durations=False)  # (6)!
"""
                              Evaluation Summary: guess_city
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Case ID     ┃ Inputs                         ┃ Outputs ┃ Scores            ┃ Assertions ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ simple_case │ What is the capital of France? │ Paris   │ MyEvaluator: 1.00 │ ✔          │
├─────────────┼────────────────────────────────┼─────────┼───────────────────┼────────────┤
│ Averages    │                                │         │ MyEvaluator: 1.00 │ 100.0% ✔   │
└─────────────┴────────────────────────────────┴─────────┴───────────────────┴────────────┘
"""
```

----------------------------------------

TITLE: Streaming Pydantic-AI Agent Run with Async Iteration
DESCRIPTION: This Python code demonstrates how to set up and stream a Pydantic-AI agent run. It defines a `WeatherService` with methods for fetching weather data, an `Agent` configured with this service and an output type, and a tool function `weather_forecast` that uses the service. The `main` function shows how to use `async with agent.iter()` and `async for node in run` to process the agent's execution step-by-step, handling different node types (user prompt, model request, tool calls, end node) and streaming events within those nodes.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_4

LANGUAGE: python
CODE:
```
import asyncio
from dataclasses import dataclass
from datetime import date

from pydantic_ai import Agent
from pydantic_ai.messages import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ToolCallPartDelta,
)
from pydantic_ai.tools import RunContext


@dataclass
class WeatherService:
    async def get_forecast(self, location: str, forecast_date: date) -> str:
        # In real code: call weather API, DB queries, etc.
        return f'The forecast in {location} on {forecast_date} is 24°C and sunny.'

    async def get_historic_weather(self, location: str, forecast_date: date) -> str:
        # In real code: call a historical weather API or DB
        return (
            f'The weather in {location} on {forecast_date} was 18°C and partly cloudy.'
        )


weather_agent = Agent[WeatherService, str](
    'openai:gpt-4o',
    deps_type=WeatherService,
    output_type=str,  # We'll produce a final answer as plain text
    system_prompt='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
async def weather_forecast(
    ctx: RunContext[WeatherService],
    location: str,
    forecast_date: date,
) -> str:
    if forecast_date >= date.today():
        return await ctx.deps.get_forecast(location, forecast_date)
    else:
        return await ctx.deps.get_historic_weather(location, forecast_date)


output_messages: list[str] = []


async def main():
    user_prompt = 'What will the weather be like in Paris on Tuesday?'

    # Begin a node-by-node, streaming iteration
    async with weather_agent.iter(user_prompt, deps=WeatherService()) as run:
        async for node in run:
            if Agent.is_user_prompt_node(node):
                # A user prompt node => The user has provided input
                output_messages.append(f'=== UserPromptNode: {node.user_prompt} ===')
            elif Agent.is_model_request_node(node):
                # A model request node => We can stream tokens from the model's request
                output_messages.append(
                    '=== ModelRequestNode: streaming partial request tokens ==='
                )
                async with node.stream(run.ctx) as request_stream:
                    async for event in request_stream:
                        if isinstance(event, PartStartEvent):
                            output_messages.append(
                                f'[Request] Starting part {event.index}: {event.part!r}'
                            )
                        elif isinstance(event, PartDeltaEvent):
                            if isinstance(event.delta, TextPartDelta):
                                output_messages.append(
                                    f'[Request] Part {event.index} text delta: {event.delta.content_delta!r}'
                                )
                            elif isinstance(event.delta, ToolCallPartDelta):
                                output_messages.append(
                                    f'[Request] Part {event.index} args_delta={event.delta.args_delta}'
                                )
                        elif isinstance(event, FinalResultEvent):
                            output_messages.append(
                                f'[Result] The model produced a final output (tool_name={event.tool_name})'
                            )
            elif Agent.is_call_tools_node(node):
                # A handle-response node => The model returned some data, potentially calls a tool
                output_messages.append(
                    '=== CallToolsNode: streaming partial response & tool usage ==='
                )
                async with node.stream(run.ctx) as handle_stream:
                    async for event in handle_stream:
                        if isinstance(event, FunctionToolCallEvent):
                            output_messages.append(
                                f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})'
                            )
                        elif isinstance(event, FunctionToolResultEvent):
                            output_messages.append(
                                f'[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}'
                            )
            elif Agent.is_end_node(node):
                assert run.result.output == node.data.output
                # Once an End node is reached, the agent run is complete
                output_messages.append(
                    f'=== Final Agent Output: {run.result.output} ==='
                )


if __name__ == '__main__':
    asyncio.run(main())

    print(output_messages)
```

----------------------------------------

TITLE: Using TestModel for Unit Testing PydanticAI Agents
DESCRIPTION: Example showing how to use TestModel to unit test an AI agent implementation. The code demonstrates setting up a test agent, overriding its model with TestModel, and verifying the agent's behavior and function tool usage.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/test.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

my_agent = Agent('openai:gpt-4o', system_prompt='...')


async def test_my_agent():
    """Unit test for my_agent, to be run by pytest."""
    m = TestModel()
    with my_agent.override(model=m):
        result = await my_agent.run('Testing my agent...')
        assert result.output == 'success (no tool calls)'
    assert m.last_model_request_parameters.function_tools == []
```

----------------------------------------

TITLE: Using Tavily Search Tool with PydanticAI Agent
DESCRIPTION: Example of how to use the Tavily search tool with a PydanticAI agent. It demonstrates importing the tool, setting up the API key, creating an agent, and running a search query.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/common-tools.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
import os

from pydantic_ai.agent import Agent
from pydantic_ai.common_tools.tavily import tavily_search_tool

api_key = os.getenv('TAVILY_API_KEY')
assert api_key is not None

agent = Agent(
    'openai:o3-mini',
    tools=[tavily_search_tool(api_key)],
    system_prompt='Search Tavily for the given query and return the results.',
)

result = agent.run_sync('Tell me the top news in the GenAI world, give me links.')
print(result.output)
"""
Here are some of the top recent news articles related to GenAI:

1. How CLEAR users can improve risk analysis with GenAI – Thomson Reuters
   Read more: https://legal.thomsonreuters.com/blog/how-clear-users-can-improve-risk-analysis-with-genai/
   (This article discusses how CLEAR's new GenAI-powered tool streamlines risk analysis by quickly summarizing key information from various public data sources.)

2. TELUS Digital Survey Reveals Enterprise Employees Are Entering Sensitive Data Into AI Assistants More Than You Think – FT.com
   Read more: https://markets.ft.com/data/announce/detail?dockey=600-202502260645BIZWIRE_USPRX____20250226_BW490609-1
   (This news piece highlights findings from a TELUS Digital survey showing that many enterprise employees use public GenAI tools and sometimes even enter sensitive data.)

3. The Essential Guide to Generative AI – Virtualization Review
   Read more: https://virtualizationreview.com/Whitepapers/2025/02/SNOWFLAKE-The-Essential-Guide-to-Generative-AI.aspx
   (This guide provides insights into how GenAI is revolutionizing enterprise strategies and productivity, with input from industry leaders.)

Feel free to click on the links to dive deeper into each story!
"""
```

----------------------------------------

TITLE: Generating Tool Schema with Docstrings
DESCRIPTION: This snippet demonstrates how PydanticAI extracts function parameters and docstring information from a function signature and docstring (using Google style) to build a JSON schema for a tool. It uses `FunctionModel` to print the generated schema and shows how to explicitly set the docstring format and require parameter descriptions.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

agent = Agent()


@agent.tool_plain(docstring_format='google', require_parameter_descriptions=True)
def foobar(a: int, b: str, c: dict[str, list[float]]) -> str:
    """Get me foobar.

    Args:
        a: apple pie
        b: banana cake
        c: carrot smoothie
    """
    return f'{a} {b} {c}'


def print_schema(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    tool = info.function_tools[0]
    print(tool.description)
    #> Get me foobar.
    print(tool.parameters_json_schema)
    """
    {
        'additionalProperties': False,
        'properties': {
            'a': {'description': 'apple pie', 'type': 'integer'},
            'b': {'description': 'banana cake', 'type': 'string'},
            'c': {
                'additionalProperties': {'items': {'type': 'number'}, 'type': 'array'},
                'description': 'carrot smoothie',
                'type': 'object',
            },
        },
        'required': ['a', 'b', 'c'],
        'type': 'object',
    }
    """
    return ModelResponse(parts=[TextPart('foobar')])


agent.run_sync('hello', model=FunctionModel(print_schema))
```

----------------------------------------

TITLE: Bank Support Agent Implementation in Python
DESCRIPTION: This Python script implements a bank support agent using PydanticAI. The code is located in the file 'bank_support.py' within the 'examples/pydantic_ai_examples/' directory.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/bank-support.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/bank_support.py
```

----------------------------------------

TITLE: Demonstrating PydanticAI Agent Type Errors (Python)
DESCRIPTION: This snippet shows a PydanticAI agent definition and usage that contains type mismatches between the agent's expected dependency/output types and the types used in decorated functions or subsequent calls, illustrating how static type checkers can catch these errors.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_10

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext


@dataclass
class User:
    name: str


agent = Agent(
    'test',
    deps_type=User,  # (1)!
    output_type=bool,
)


@agent.system_prompt
def add_user_name(ctx: RunContext[str]) -> str:  # (2)!
    return f"The user's name is {ctx.deps}."


def foobar(x: bytes) -> None:
    pass


result = agent.run_sync('Does their name start with "A"?', deps=User('Anne'))
foobar(result.output)  # (3)!
```

----------------------------------------

TITLE: Implementing Chat App Backend with FastAPI in Python
DESCRIPTION: Python code that runs the chat application backend using FastAPI. This file handles the server-side logic, including message processing and response streaming.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/chat-app.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/chat_app.py
```

----------------------------------------

TITLE: Using DuckDuckGo Search Tool with PydanticAI Agent
DESCRIPTION: Example of how to use the DuckDuckGo search tool with a PydanticAI agent. It demonstrates importing the tool, creating an agent, and running a search query.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/common-tools.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

agent = Agent(
    'openai:o3-mini',
    tools=[duckduckgo_search_tool()],
    system_prompt='Search DuckDuckGo for the given query and return the results.',
)

result = agent.run_sync(
    'Can you list the top five highest-grossing animated films of 2025?'
)
print(result.output)
"""
I looked into several sources on animated box‐office performance in 2025, and while detailed
rankings can shift as more money is tallied, multiple independent reports have already
highlighted a couple of record‐breaking shows. For example:

• Ne Zha 2 – News outlets (Variety, Wikipedia's "List of animated feature films of 2025", and others)
    have reported that this Chinese title not only became the highest‑grossing animated film of 2025
    but also broke records as the highest‑grossing non‑English animated film ever. One article noted
    its run exceeded US$1.7 billion.
• Inside Out 2 – According to data shared on Statista and in industry news, this Pixar sequel has been
    on pace to set new records (with some sources even noting it as the highest‑grossing animated film
    ever, as of January 2025).

Beyond those two, some entertainment trade sites (for example, a Just Jared article titled
"Top 10 Highest-Earning Animated Films at the Box Office Revealed") have begun listing a broader
top‑10. Although full consolidated figures can sometimes differ by source and are updated daily during
a box‑office run, many of the industry trackers have begun to single out five films as the biggest
earners so far in 2025.

Unfortunately, although multiple articles discuss the "top animated films" of 2025, there isn't yet a
single, universally accepted list with final numbers that names the complete top five. (Box‑office
rankings, especially mid‑year, can be fluid as films continue to add to their totals.)

Based on what several sources note so far, the two undisputed leaders are:
1. Ne Zha 2
2. Inside Out 2

The remaining top spots (3–5) are reported by some outlets in their "Top‑10 Animated Films"
lists for 2025 but the titles and order can vary depending on the source and the exact cut‑off
date of the data. For the most up‑to‑date and detailed ranking (including the 3rd, 4th, and 5th
highest‑grossing films), I recommend checking resources like:
• Wikipedia's "List of animated feature films of 2025" page
• Box‑office tracking sites (such as Box Office Mojo or The Numbers)
• Trade articles like the one on Just Jared

To summarize with what is clear from the current reporting:
1. Ne Zha 2
2. Inside Out 2
3–5. Other animated films (yet to be definitively finalized across all reporting outlets)

If you're looking for a final, consensus list of the top five, it may be best to wait until
the 2025 year‑end box‑office tallies are in or to consult a regularly updated entertainment industry source.

Would you like help finding a current source or additional details on where to look for the complete updated list?
"""
```

----------------------------------------

TITLE: Running PydanticAI Agent (Sync, Async, Stream)
DESCRIPTION: Demonstrates the basic usage of `agent.run_sync()` for synchronous execution, `agent.run()` for asynchronous execution, and `agent.run_stream()` for streaming results. Note that the async parts require an event loop to run.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_1

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')

result_sync = agent.run_sync('What is the capital of Italy?')
print(result_sync.output)
#/> Rome


async def main():
    result = await agent.run('What is the capital of France?')
    print(result.output)
    #/> Paris

    async with agent.run_stream('What is the capital of the UK?') as response:
        print(await response.get_output())
        #/> London
```

----------------------------------------

TITLE: Defining Weather Agent and Tool in Python
DESCRIPTION: This snippet defines a `pydantic-ai` agent (`weather_agent`) using the `gpt-4o` model and a `WeatherService` dependency. It includes a tool function `weather_forecast` that calls different methods on the dependency based on the forecast date. It also defines an async function `run_weather_forecast` to process multiple user prompts in parallel and store results.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/testing.md#_snippet_1

LANGUAGE: python
CODE:
```
import asyncio
from datetime import date

from pydantic_ai import Agent, RunContext

from fake_database import DatabaseConn  # (1)!
from weather_service import WeatherService  # (2)!

weather_agent = Agent(
    'openai:gpt-4o',
    deps_type=WeatherService,
    system_prompt='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
def weather_forecast(
    ctx: RunContext[WeatherService], location: str, forecast_date: date
) -> str:
    if forecast_date < date.today():  # (3)!
        return ctx.deps.get_historic_weather(location, forecast_date)
    else:
        return ctx.deps.get_forecast(location, forecast_date)


async def run_weather_forecast(  # (4)!
    user_prompts: list[tuple[str, int]], conn: DatabaseConn
):
    """Run weather forecast for a list of user prompts and save."""
    async with WeatherService() as weather_service:

        async def run_forecast(prompt: str, user_id: int):
            result = await weather_agent.run(prompt, deps=weather_service)
            await conn.store_forecast(user_id, result.output)

        # run all prompts in parallel
        await asyncio.gather(
            *(run_forecast(prompt, user_id) for (prompt, user_id) in user_prompts)
        )
```

----------------------------------------

TITLE: Testing Weather Forecast with FunctionModel
DESCRIPTION: Demonstrates how to use `FunctionModel` to test an agent's tool call logic. It defines a custom function `call_weather_forecast` to simulate the LLM's response, extracting parameters from the prompt and returning a `ToolCallPart` or `TextPart`. The agent's model is then overridden with `FunctionModel` wrapping this custom function for the test.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/testing.md#_snippet_4

LANGUAGE: python
CODE:
```
import re

import pytest

from pydantic_ai import models
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from fake_database import DatabaseConn
from weather_app import run_weather_forecast, weather_agent

pytestmark = pytest.mark.anyio
models.ALLOW_MODEL_REQUESTS = False


def call_weather_forecast(  # (1)!
    messages: list[ModelMessage], info: AgentInfo
) -> ModelResponse:
    if len(messages) == 1:
        # first call, call the weather forecast tool
        user_prompt = messages[0].parts[-1]
        m = re.search(r'\d{4}-\d{2}-\d{2}', user_prompt.content)
        assert m is not None
        args = {'location': 'London', 'forecast_date': m.group()}  # (2)!
        return ModelResponse(parts=[ToolCallPart('weather_forecast', args)])
    else:
        # second call, return the forecast
        msg = messages[-1].parts[0]
        assert msg.part_kind == 'tool-return'
        return ModelResponse(parts=[TextPart(f'The forecast is: {msg.content}')])


async def test_forecast_future():
    conn = DatabaseConn()
    user_id = 1
    with weather_agent.override(model=FunctionModel(call_weather_forecast)):  # (3)!
        prompt = 'What will the weather be like in London on 2032-01-01?'
        await run_weather_forecast([(prompt, user_id)], conn)

    forecast = await conn.get_forecast(user_id)
    assert forecast == 'The forecast is: Rainy with a chance of sun'
```

----------------------------------------

TITLE: Running Graph from File Persistence (Python)
DESCRIPTION: This snippet demonstrates how to initialize a graph run with file-based state persistence and then repeatedly resume execution of the graph from the persisted state using `iter_from_persistence` until the run completes. It simulates scenarios where a graph run might be interrupted and resumed later, highlighting how the `run_node` function can operate independently given just the run ID.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_12

LANGUAGE: python
CODE:
```
from pathlib import Path

from pydantic_graph import End
from pydantic_graph.persistence.file import FileStatePersistence

from count_down import CountDown, CountDownState, count_down_graph


async def main():
    run_id = 'run_abc123'
    persistence = FileStatePersistence(Path(f'count_down_{run_id}.json'))  # (1)!
    state = CountDownState(counter=5)
    await count_down_graph.initialize(  # (2)!
        CountDown(), state=state, persistence=persistence
    )

    done = False
    while not done:
        done = await run_node(run_id)


async def run_node(run_id: str) -> bool:  # (3)!
    persistence = FileStatePersistence(Path(f'count_down_{run_id}.json'))
    async with count_down_graph.iter_from_persistence(persistence) as run:  # (4)!
        node_or_end = await run.next()  # (5)!

    print('Node:', node_or_end)
    #/> Node: CountDown()
    #/> Node: CountDown()
    #/> Node: CountDown()
    #/> Node: CountDown()
    #/> Node: CountDown()
    #/> Node: End(data=0)
    return isinstance(node_or_end, End)  # (6)!
```

----------------------------------------

TITLE: Implementing Basic Fallback Model in Python
DESCRIPTION: Demonstrates how to implement a fallback mechanism between OpenAI and Anthropic models using FallbackModel. Shows configuration of multiple models and handling of fallback responses.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/index.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIModel

openai_model = OpenAIModel('gpt-4o')
anthropic_model = AnthropicModel('claude-3-5-sonnet-latest')
fallback_model = FallbackModel(openai_model, anthropic_model)

agent = Agent(fallback_model)
response = agent.run_sync('What is the capital of France?')
print(response.data)
#> Paris

print(response.all_messages())
```

----------------------------------------

TITLE: Defining Static and Dynamic System Prompts for PydanticAI Agent (Python)
DESCRIPTION: This snippet demonstrates how to define both a static system prompt using the `system_prompt` parameter in the Agent constructor and dynamic system prompts using the `@agent.system_prompt` decorator. It shows how dynamic prompts can access runtime context like dependencies.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_12

LANGUAGE: python
CODE:
```
from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-4o',
    deps_type=str,  # (1)!
    system_prompt="Use the customer's name while replying to them.",  # (2)!
)


@agent.system_prompt  # (3)!
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.system_prompt
def add_the_date() -> str:  # (4)!
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.
```

----------------------------------------

TITLE: Defining Intermediate Node in pydantic-graph Python
DESCRIPTION: This Python class defines a node (`MyNode`) for use in a `pydantic-graph`. It inherits from `BaseNode`, is parameterized with a state type (`MyState`), has a field (`foo`), and its `run` method returns another node (`AnotherNode`), indicating an outgoing edge.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_1

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

from pydantic_graph import BaseNode, GraphRunContext


@dataclass
class MyNode(BaseNode[MyState]):  # (1)!
    foo: int  # (2)!

    async def run(
        self,
        ctx: GraphRunContext[MyState],  # (3)!
    ) -> AnotherNode:  # (4)!
        ...
        return AnotherNode()
```

----------------------------------------

TITLE: Implementing AI Email Feedback Graph with PydanticAI
DESCRIPTION: Defines a graph using Pydantic-Graph nodes (`WriteEmail`, `Feedback`) and PydanticAI agents. The `WriteEmail` node uses an agent to write an email, potentially incorporating feedback. The `Feedback` node uses another agent to review the email and determine if rewriting is needed based on user interests. Requires PydanticAI and Pydantic-Graph.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_9

LANGUAGE: python
CODE:
```
from __future__ import annotations as _annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, EmailStr

from pydantic_ai import Agent, format_as_xml
from pydantic_ai.messages import ModelMessage
from pydantic_graph import BaseNode, End, Graph, GraphRunContext


@dataclass
class User:
    name: str
    email: EmailStr
    interests: list[str]


@dataclass
class Email:
    subject: str
    body: str


@dataclass
class State:
    user: User
    write_agent_messages: list[ModelMessage] = field(default_factory=list)


email_writer_agent = Agent(
    'google-vertex:gemini-1.5-pro',
    output_type=Email,
    system_prompt='Write a welcome email to our tech blog.',
)


@dataclass
class WriteEmail(BaseNode[State]):
    email_feedback: str | None = None

    async def run(self, ctx: GraphRunContext[State]) -> Feedback:
        if self.email_feedback:
            prompt = (
                f'Rewrite the email for the user:\n'
                f'{format_as_xml(ctx.state.user)}\n'
                f'Feedback: {self.email_feedback}'
            )
        else:
            prompt = (
                f'Write a welcome email for the user:\n'
                f'{format_as_xml(ctx.state.user)}'
            )

        result = await email_writer_agent.run(
            prompt,
            message_history=ctx.state.write_agent_messages,
        )
        ctx.state.write_agent_messages += result.new_messages()
        return Feedback(result.output)


class EmailRequiresWrite(BaseModel):
    feedback: str


class EmailOk(BaseModel):
    pass


feedback_agent = Agent[None, EmailRequiresWrite | EmailOk](
    'openai:gpt-4o',
    output_type=EmailRequiresWrite | EmailOk,  # type: ignore
    system_prompt=(
        'Review the email and provide feedback, email must reference the users specific interests.'
    ),
)


@dataclass
class Feedback(BaseNode[State, None, Email]):
    email: Email

    async def run(
        self,
        ctx: GraphRunContext[State],
    ) -> WriteEmail | End[Email]:
        prompt = format_as_xml({'user': ctx.state.user, 'email': self.email})
        result = await feedback_agent.run(prompt)
        if isinstance(result.output, EmailRequiresWrite):
            return WriteEmail(email_feedback=result.output.feedback)
        else:
            return End(self.email)


async def main():
    user = User(
        name='John Doe',
        email='john.joe@example.com',
        interests=['Haskel', 'Lisp', 'Fortran'],
    )
    state = State(user)
    feedback_graph = Graph(nodes=(WriteEmail, Feedback))
    result = await feedback_graph.run(WriteEmail(), state=state)
    print(result.output)
    """
    Email(
        subject='Welcome to our tech blog!',
        body='Hello John, Welcome to our tech blog! ...',
    )
    """

```

----------------------------------------

TITLE: Complete Example with Dependencies in System Prompts, Tools, and Output Validators
DESCRIPTION: A comprehensive example showing dependencies used across all PydanticAI components: system prompts, tools, and output validators. Each component receives the RunContext parameter to access dependencies for HTTP requests and API authentication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, ModelRetry, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,
)


@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    response = await ctx.deps.http_client.get('https://example.com')
    response.raise_for_status()
    return f'Prompt: {response.text}'


@agent.tool  # (1)!
async def get_joke_material(ctx: RunContext[MyDeps], subject: str) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com#jokes',
        params={'subject': subject},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    return response.text


@agent.output_validator  # (2)!
async def validate_output(ctx: RunContext[MyDeps], output: str) -> str:
    response = await ctx.deps.http_client.post(
        'https://example.com#validate',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
        params={'query': output},
    )
    if response.status_code == 400:
        raise ModelRetry(f'invalid response: {response.text}')
    response.raise_for_status()
    return output


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

----------------------------------------

TITLE: Advanced Streaming User Profile with Error Handling
DESCRIPTION: Shows a more sophisticated implementation with fine-grained validation control and error handling. Uses stream_structured and validate_structured_output methods with debouncing for better control over the streaming process.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/output.md#2025-04-22_snippet_7

LANGUAGE: python
CODE:
```
from datetime import date

from pydantic import ValidationError
from typing_extensions import TypedDict

from pydantic_ai import Agent


class UserProfile(TypedDict, total=False):
    name: str
    dob: date
    bio: str


agent = Agent('openai:gpt-4o', output_type=UserProfile)


async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for message, last in result.stream_structured(debounce_by=0.01):
            try:
                profile = await result.validate_structured_output(
                    message,
                    allow_partial=not last,
                )
            except ValidationError:
                continue
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
```

----------------------------------------

TITLE: SQL Query Validation with Output Validator
DESCRIPTION: Implements asynchronous SQL query validation using output validator functions. Demonstrates handling both successful queries and invalid requests.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/output.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
from typing import Union

from fake_database import DatabaseConn, QueryError
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry


class Success(BaseModel):
    sql_query: str


class InvalidRequest(BaseModel):
    error_message: str


Output = Union[Success, InvalidRequest]
agent: Agent[DatabaseConn, Output] = Agent(
    'google-gla:gemini-1.5-flash',
    output_type=Output,  # type: ignore
    deps_type=DatabaseConn,
    system_prompt='Generate PostgreSQL flavored SQL queries based on user input.',
)


@agent.output_validator
async def validate_sql(ctx: RunContext[DatabaseConn], output: Output) -> Output:
    if isinstance(output, InvalidRequest):
        return output
    try:
        await ctx.deps.execute(f'EXPLAIN {output.sql_query}')
    except QueryError as e:
        raise ModelRetry(f'Invalid query: {e}') from e
    else:
        return output


result = agent.run_sync(
    'get me users who were last active yesterday.', deps=DatabaseConn()
)
print(result.output)
#> sql_query='SELECT * FROM users WHERE last_active::date = today() - interval 1 day'
```

----------------------------------------

TITLE: Implementing Basic Evaluation with Pydantic Evals
DESCRIPTION: Demonstrates how to create and run evaluations using Pydantic Evals, including defining test cases, custom evaluators, and running evaluations on a simple question-answering function.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/pydantic_evals/README.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext, IsInstance

# Define a test case with inputs and expected output
case = Case(
    name='capital_question',
    inputs='What is the capital of France?',
    expected_output='Paris',
)

# Define a custom evaluator
class MatchAnswer(Evaluator[str, str]):
    def evaluate(self, ctx: EvaluatorContext[str, str]) -> float:
        if ctx.output == ctx.expected_output:
            return 1.0
        elif isinstance(ctx.output, str) and ctx.expected_output.lower() in ctx.output.lower():
            return 0.8
        return 0.0

# Create a dataset with the test case and evaluators
dataset = Dataset(
    cases=[case],
    evaluators=[IsInstance(type_name='str'), MatchAnswer()],
)

# Define the function to evaluate
async def answer_question(question: str) -> str:
    return 'Paris'

# Run the evaluation
report = dataset.evaluate_sync(answer_question)
report.print(include_input=True, include_output=True)
```

----------------------------------------

TITLE: Raising ModelRetry for Explicit Retries (Python)
DESCRIPTION: This snippet demonstrates how to raise the `ModelRetry` exception within a tool function to explicitly request the LLM to retry the tool call. This is useful when the tool's internal logic determines the input or execution needs modification, even if validation passed. The message provided to `ModelRetry` is sent back to the LLM.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_8

LANGUAGE: python
CODE:
```
from pydantic_ai import ModelRetry

def my_flaky_tool(query: str) -> str:
    if query == 'bad':
        # Tell the LLM the query was bad and it should try again
        raise ModelRetry("The query 'bad' is not allowed. Please provide a different query.")
    # ... process query ...
    return 'Success!'
```

----------------------------------------

TITLE: Pytest Fixture to Override Agent Model
DESCRIPTION: Shows how to create a Pytest fixture to override an agent's model (e.g., with `TestModel` or `FunctionModel`) for multiple tests. This allows for reusable model mocking across test functions.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/testing.md#_snippet_5

LANGUAGE: python
CODE:
```
import pytest
from weather_app import weather_agent

from pydantic_ai.models.test import TestModel


@pytest.fixture
def override_weather_agent():
    with weather_agent.override(model=TestModel()):
        yield


async def test_forecast(override_weather_agent: None):
    ...
    # test code here
```

----------------------------------------

TITLE: Expose PydanticAI Agent as A2A Server
DESCRIPTION: Demonstrates how to initialize a PydanticAI Agent and convert it into an A2A server ASGI application using the `to_a2a` method. Requires the `pydantic-ai[a2a]` installation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/a2a.md#_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4.1', instructions='Be fun!')
app = agent.to_a2a()
```

----------------------------------------

TITLE: Providing Image Input via URL with pydantic-ai (Python)
DESCRIPTION: This snippet demonstrates how to provide an image to a pydantic-ai Agent using a direct URL. It initializes an agent with a multi-modal model ('openai:gpt-4o') and sends a list containing a text query and an ImageUrl object referencing the image URL. The agent then processes both inputs.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/input.md#_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent, ImageUrl

agent = Agent(model='openai:gpt-4o')
result = agent.run_sync(
    [
        'What company is this logo from?',
        ImageUrl(url='https://iili.io/3Hs4FMg.png'),
    ]
)
print(result.output)
```

----------------------------------------

TITLE: RAG Search Implementation in Python
DESCRIPTION: This code snippet represents the main implementation of the RAG search example. It includes the full content of the rag.py file, which likely contains the PydanticAI agent setup, tool definitions, and search functionality.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/rag.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/rag.py
```

----------------------------------------

TITLE: Defining Agent Dependencies with Dataclasses in Python
DESCRIPTION: Example demonstrating how to define a dependency class using dataclasses and provide it to an Agent. This shows the pattern of defining a dependency type, specifying it in the Agent constructor, and passing an instance when running the agent.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent


@dataclass
class MyDeps:  # (1)!
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,  # (2)!
)


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run(
            'Tell me a joke.',
            deps=deps,  # (3)!
        )
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

----------------------------------------

TITLE: Accessing All Messages After Run Completion - Pydantic-AI - Python
DESCRIPTION: This snippet shows how to retrieve all messages (requests and responses) from a Pydantic-AI run result object after the run has finished. The output demonstrates the structure of the `ModelRequest` and `ModelResponse` objects.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/message-history.md#_snippet_1

LANGUAGE: python
CODE:
```
print(result.all_messages())
```

----------------------------------------

TITLE: Testing Agent Dependencies with Overrides in Python
DESCRIPTION: Unit test implementation showing how to override agent dependencies for testing purposes. Demonstrates creating test-specific dependency implementations and using context managers for dependency injection.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md#2025-04-22_snippet_5

LANGUAGE: python
CODE:
```
from joke_app import MyDeps, application_code, joke_agent


class TestMyDeps(MyDeps):  
    async def system_prompt_factory(self) -> str:
        return 'test prompt'


async def test_application_code():
    test_deps = TestMyDeps('test_key', None)  
    with joke_agent.override(deps=test_deps):  
        joke = await application_code('Tell me a joke.')  
    assert joke.startswith('Did you hear about the toothpaste scandal?')
```

----------------------------------------

TITLE: Programmatic Agent Hand-off Implementation
DESCRIPTION: Demonstrates programmatic agent hand-off pattern where multiple agents are called in sequence with application code controlling the flow. Shows flight search and seat preference handling.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/multi-agent-applications.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from typing import Literal, Union
from pydantic import BaseModel, Field
from rich.prompt import Prompt
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import Usage, UsageLimits

class FlightDetails(BaseModel):
    flight_number: str

class Failed(BaseModel):
    """Unable to find a satisfactory choice."""

flight_search_agent = Agent[None, Union[FlightDetails, Failed]](
    'openai:gpt-4o',
    output_type=Union[FlightDetails, Failed],
    system_prompt=(
        'Use the "flight_search" tool to find a flight '
        'from the given origin to the given destination.'
    ),
)

@flight_search_agent.tool
async def flight_search(
    ctx: RunContext[None], origin: str, destination: str
) -> Union[FlightDetails, None]:
    return FlightDetails(flight_number='AK456')

usage_limits = UsageLimits(request_limit=15)

async def find_flight(usage: Usage) -> Union[FlightDetails, None]:
    message_history: Union[list[ModelMessage], None] = None
    for _ in range(3):
        prompt = Prompt.ask(
            'Where would you like to fly from and to?',
        )
        result = await flight_search_agent.run(
            prompt,
            message_history=message_history,
            usage=usage,
            usage_limits=usage_limits,
        )
        if isinstance(result.output, FlightDetails):
            return result.output
        else:
            message_history = result.all_messages(
                output_tool_return_content='Please try again.'
            )

class SeatPreference(BaseModel):
    row: int = Field(ge=1, le=30)
    seat: Literal['A', 'B', 'C', 'D', 'E', 'F']
```

----------------------------------------

TITLE: Creating and Testing Agents with FunctionModel in Python
DESCRIPTION: Example showing how to create a custom model function to control agent behavior for testing. The code demonstrates setting up a test agent, defining a model function that processes messages and agent info, and writing a unit test using pytest. The function returns a controlled response for predictable testing.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/function.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel, AgentInfo

my_agent = Agent('openai:gpt-4o')


async def model_function(
    messages: list[ModelMessage], info: AgentInfo
) -> ModelResponse:
    print(messages)
    """
    [
        ModelRequest(
            parts=[
                UserPromptPart(
                    content='Testing my agent...',
                    timestamp=datetime.datetime(...),
                    part_kind='user-prompt',
                )
            ],
            instructions=None,
            kind='request',
        )
    ]
    """
    print(info)
    """
    AgentInfo(
        function_tools=[], allow_text_output=True, output_tools=[], model_settings=None
    )
    """
    return ModelResponse(parts=[TextPart('hello world')])


async def test_my_agent():
    """Unit test for my_agent, to be run by pytest."""
    with my_agent.override(model=FunctionModel(model_function)):
        result = await my_agent.run('Testing my agent...')
        assert result.output == 'hello world'
```

----------------------------------------

TITLE: Custom OpenAI Provider Configuration
DESCRIPTION: Configuration of OpenAI model with custom provider settings including API key.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIModel('gpt-4o', provider=OpenAIProvider(api_key='your-api-key'))
agent = Agent(model)
...
```

----------------------------------------

TITLE: Limiting Requests with PydanticAI (Python)
DESCRIPTION: Shows how to prevent excessive tool calling or infinite loops by setting a request_limit using UsageLimits. Includes a custom tool that simulates retries and demonstrates how the limit prevents the loop. Requires pydantic_ai and typing_extensions.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_6

LANGUAGE: python
CODE:
```
from typing_extensions import TypedDict

from pydantic_ai import Agent, ModelRetry
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits


class NeverOutputType(TypedDict):
    """
    Never ever coerce data to this type.
    """

    never_use_this: str


agent = Agent(
    'anthropic:claude-3-5-sonnet-latest',
    retries=3,
    output_type=NeverOutputType,
    system_prompt='Any time you get a response, call the `infinite_retry_tool` to produce another response.',
)


@agent.tool_plain(retries=5)  # (1)!
def infinite_retry_tool() -> int:
    raise ModelRetry('Please try again.')


try:
    result_sync = agent.run_sync(
        'Begin infinite retry loop!', usage_limits=UsageLimits(request_limit=3)  # (2)!
    )
except UsageLimitExceeded as e:
    print(e)
    #> The next request would exceed the request_limit of 3
```

----------------------------------------

TITLE: Main Async Function for Flight Booking
DESCRIPTION: Main application logic that coordinates flight search and seat selection processes. Demonstrates the complete booking flow.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/multi-agent-applications.md#2025-04-22_snippet_5

LANGUAGE: python
CODE:
```
async def main():
    usage: Usage = Usage()

    opt_flight_details = await find_flight(usage)
    if opt_flight_details is not None:
        print(f'Flight found: {opt_flight_details.flight_number}')
        #> Flight found: AK456
        seat_preference = await find_seat(usage)
        print(f'Seat preference: {seat_preference}')
        #> Seat preference: row=1 seat='A'
```

----------------------------------------

TITLE: Configuring Agent Instructions in Pydantic-AI (Python)
DESCRIPTION: This snippet demonstrates how to initialize a pydantic-ai Agent with specific instructions using the `instructions` parameter. These instructions act as the system prompt for the current agent run and are not retained from previous messages in the history.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_13

LANGUAGE: Python
CODE:
```
from pydantic_ai import Agent

agent = Agent(
    'openai:gpt-4o',
    instructions='You are a helpful assistant that can answer questions and help with tasks.',  # (1)!
)

result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris
```

----------------------------------------

TITLE: Implementing Graph-based State Machine with Pydantic Graph
DESCRIPTION: Demonstrates creation of a graph that finds the next number divisible by 5. Uses two node types: DivisibleBy5 checks if current number is divisible by 5, and Increment increments the number. Shows type-safe node definitions and graph execution.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/pydantic_graph/README.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext


@dataclass
class DivisibleBy5(BaseNode[None, None, int]):
    foo: int

    async def run(
        self,
        ctx: GraphRunContext,
    ) -> Increment | End[int]:
        if self.foo % 5 == 0:
            return End(self.foo)
        else:
            return Increment(self.foo)


@dataclass
class Increment(BaseNode):
    foo: int

    async def run(self, ctx: GraphRunContext) -> DivisibleBy5:
        return DivisibleBy5(self.foo + 1)


fives_graph = Graph(nodes=[DivisibleBy5, Increment])
result = fives_graph.run_sync(DivisibleBy5(4))
print(result.output)
#> 5
```

----------------------------------------

TITLE: Ollama Local Usage Example
DESCRIPTION: Example of using Ollama locally with Pydantic-AI for model inference.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_7

LANGUAGE: python
CODE:
```
from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider


class CityLocation(BaseModel):
    city: str
    country: str


ollama_model = OpenAIModel(
    model_name='llama3.2', provider=OpenAIProvider(base_url='http://localhost:11434/v1')
)
agent = Agent(ollama_model, output_type=CityLocation)

result = agent.run_sync('Where were the olympics held in 2012?')
print(result.output)
print(result.usage())
```

----------------------------------------

TITLE: Streaming Text Output with Delta Updates
DESCRIPTION: Demonstrates streaming text responses with delta updates, showing only the new content at each step.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/output.md#2025-04-22_snippet_5

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('google-gla:gemini-1.5-flash')


async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        async for message in result.stream_text(delta=True):
            print(message)
            #> The first known
            #> use of "hello,
            #> world" was in
            #> a 1974 textbook
            #> about the C
            #> programming language.
```

----------------------------------------

TITLE: Agent Delegation with Dependencies in PydanticAI
DESCRIPTION: Shows how to implement agent delegation with shared dependencies between agents. Demonstrates proper dependency initialization and passing between parent and delegate agents.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/multi-agent-applications.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, RunContext

@dataclass
class ClientAndKey:
    http_client: httpx.AsyncClient
    api_key: str

joke_selection_agent = Agent(
    'openai:gpt-4o',
    deps_type=ClientAndKey,
    system_prompt=(
        'Use the `joke_factory` tool to generate some jokes on the given subject, '
        'then choose the best. You must return just a single joke.'
    ),
)
joke_generation_agent = Agent(
    'gemini-1.5-flash',
    deps_type=ClientAndKey,
    output_type=list[str],
    system_prompt=(
        'Use the "get_jokes" tool to get some jokes on the given subject, '
        'then extract each joke into a list.'
    ),
)

@joke_selection_agent.tool
async def joke_factory(ctx: RunContext[ClientAndKey], count: int) -> list[str]:
    r = await joke_generation_agent.run(
        f'Please generate {count} jokes.',
        deps=ctx.deps,
        usage=ctx.usage,
    )
    return r.output

@joke_generation_agent.tool
async def get_jokes(ctx: RunContext[ClientAndKey], count: int) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com',
        params={'count': count},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    return response.text
```

----------------------------------------

TITLE: Providing Document Input via Binary Content with pydantic-ai (Python)
DESCRIPTION: This snippet demonstrates how to send document data directly to a pydantic-ai Agent using the BinaryContent class. It reads the document content from a local file using pathlib.Path's read_bytes() method and sends it with a text query, specifying the 'application/pdf' media type.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/input.md#_snippet_3

LANGUAGE: python
CODE:
```
from pathlib import Path
from pydantic_ai import Agent, BinaryContent

pdf_path = Path('document.pdf')
agent = Agent(model='anthropic:claude-3-sonnet')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        BinaryContent(data=pdf_path.read_bytes(), media_type='application/pdf'),
    ]
)
print(result.output)
```

----------------------------------------

TITLE: Installing PydanticAI with Tavily Search Tool
DESCRIPTION: Command to install pydantic-ai-slim with the Tavily optional group for using the Tavily search tool.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/common-tools.md#2025-04-22_snippet_2

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[tavily]"
```

----------------------------------------

TITLE: Installing Anthropic Dependencies with Package Manager
DESCRIPTION: Command to install Pydantic-AI with Anthropic support using pip or uv package manager.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/anthropic.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[anthropic]"
```

----------------------------------------

TITLE: Direct Groq Model Initialization
DESCRIPTION: Example of directly initializing a Groq model using GroqModel class and creating an agent instance.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/groq.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

model = GroqModel('llama-3.3-70b-versatile')
agent = Agent(model)
...
```

----------------------------------------

TITLE: Installing Pydantic Evals with Logfire dependency
DESCRIPTION: Command to install `pydantic-evals` including the optional `logfire` dependency for OpenTelemetry traces and sending results to Logfire.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip/uv-add 'pydantic-evals[logfire]'
```

----------------------------------------

TITLE: Manual Agent Iteration with .next(...)
DESCRIPTION: This snippet demonstrates how to manually control the iteration of an `AgentRun` using the `.next(...)` method. This allows inspecting or modifying nodes before execution, skipping nodes based on custom logic, and handling errors more easily. The process starts by getting the initial node (`agent_run.next_node`), then repeatedly calling `await agent_run.next(node)` until an `End` node is returned, collecting all nodes in a list. The numbered comments explain specific steps: (1) grabbing the first node, (2) checking for the `End` node to finish, (3) executing the current node and getting the next, and (4) optionally inspecting or mutating the new node.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_graph import End

agent = Agent('openai:gpt-4o')


async def main():
    async with agent.iter('What is the capital of France?') as agent_run:
        node = agent_run.next_node  # (1)!

        all_nodes = [node]

        # Drive the iteration manually:
        while not isinstance(node, End):  # (2)!
            node = await agent_run.next(node)  # (3)!
            all_nodes.append(node)  # (4)!

        print(all_nodes)
        """
        [
            UserPromptNode(
                user_prompt='What is the capital of France?',
                instructions=None,
                instructions_functions=[],
                system_prompts=(),
                system_prompt_functions=[],
                system_prompt_dynamic_functions={},
            ),
            ModelRequestNode(
                request=ModelRequest(
                    parts=[
                        UserPromptPart(
                            content='What is the capital of France?',
                            timestamp=datetime.datetime(...),
                            part_kind='user-prompt',
                        )
                    ],
                    instructions=None,
                    kind='request',
                )
            ),
            CallToolsNode(
                model_response=ModelResponse(
                    parts=[TextPart(content='Paris', part_kind='text')],
                    usage=Usage(
                        requests=1,
                        request_tokens=56,
                        response_tokens=1,
                        total_tokens=57,
                        details=None,
                    ),
                    model_name='gpt-4o',
                    timestamp=datetime.datetime(...),
                    kind='response',
                )
            ),
            End(data=FinalResult(output='Paris', tool_name=None, tool_call_id=None)),
        ]
        """

```

----------------------------------------

TITLE: Making an Asynchronous Model Request with Tool Calling (Python)
DESCRIPTION: This example illustrates how to make an asynchronous model request using `model_request` and include tool definitions. It shows how to define a tool using Pydantic and pass it to the model request parameters, enabling the model to potentially call the tool based on the user prompt.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/direct.md#_snippet_1

LANGUAGE: python
CODE:
```
from pydantic import BaseModel
from typing_extensions import Literal

from pydantic_ai.direct import model_request
from pydantic_ai.messages import ModelRequest
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.tools import ToolDefinition


class Divide(BaseModel):
    """Divide two numbers."""

    numerator: float
    denominator: float
    on_inf: Literal['error', 'infinity'] = 'infinity'


async def main():
    # Make a request to the model with tool access
    model_response = await model_request(
        'openai:gpt-4.1-nano',
        [ModelRequest.user_text_prompt('What is 123 / 456?')],
        model_request_parameters=ModelRequestParameters(
            function_tools=[
                ToolDefinition(
                    name=Divide.__name__.lower(),
                    description=Divide.__doc__ or '',
                    parameters_json_schema=Divide.model_json_schema(),
                )
            ],
            allow_text_output=True,  # Allow model to either use tools or respond directly
        ),
    )
    print(model_response)
    # Example output is commented out but shown in the original text:
    # ModelResponse(
    #     parts=[
    #         ToolCallPart(
    #             tool_name='divide',
    #             args={'numerator': '123', 'denominator': '456'},
    #             tool_call_id='pyd_ai_2e0e396768a14fe482df90a29a78dc7b',
    #             part_kind='tool-call',
    #         )
    #     ],
    #     usage=Usage(
    #         requests=1,
    #         request_tokens=55,
    #         response_tokens=7,
    #         total_tokens=62,
    #         details=None,
    #     ),
    #     model_name='gpt-4.1-nano',
    #     timestamp=datetime.datetime(...),
    #     kind='response',
    # )
```

----------------------------------------

TITLE: Installing and Running the Weather Agent UI with Gradio (Bash)
DESCRIPTION: Commands to install Gradio and run the weather agent UI. Requires Python 3.10+ and installs Gradio version 5.9.0 or higher.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/weather-agent.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
pip install gradio>=5.9.0
python/uv-run -m pydantic_ai_examples.weather_agent_gradio
```

----------------------------------------

TITLE: Defining Stateful Vending Machine Graph - Python
DESCRIPTION: Defines a `pydantic-graph` graph representing a vending machine. It uses a `MachineState` dataclass to track the user's balance and selected product, with nodes (`InsertCoin`, `CoinsInserted`, `SelectProduct`, `Purchase`) that read and modify this state. Demonstrates how to define stateful nodes with specific return types to define graph edges and how to run the graph with an initial state object.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_6

LANGUAGE: python
CODE:
```
from __future__ import annotations

from dataclasses import dataclass

from rich.prompt import Prompt

from pydantic_graph import BaseNode, End, Graph, GraphRunContext


@dataclass
class MachineState:  # (1)!
    user_balance: float = 0.0
    product: str | None = None


@dataclass
class InsertCoin(BaseNode[MachineState]):  # (3)!
    async def run(self, ctx: GraphRunContext[MachineState]) -> CoinsInserted:  # (16)!
        return CoinsInserted(float(Prompt.ask('Insert coins')))  # (4)!


@dataclass
class CoinsInserted(BaseNode[MachineState]):
    amount: float  # (5)!

    async def run(
        self, ctx: GraphRunContext[MachineState]
    ) -> SelectProduct | Purchase:  # (17)!
        ctx.state.user_balance += self.amount  # (6)!
        if ctx.state.product is not None:  # (7)!
            return Purchase(ctx.state.product)
        else:
            return SelectProduct()


@dataclass
class SelectProduct(BaseNode[MachineState]):
    async def run(self, ctx: GraphRunContext[MachineState]) -> Purchase:
        return Purchase(Prompt.ask('Select product'))


PRODUCT_PRICES = {  # (2)!
    'water': 1.25,
    'soda': 1.50,
    'crisps': 1.75,
    'chocolate': 2.00,
}


@dataclass
class Purchase(BaseNode[MachineState, None, None]):  # (18)!
    product: str

    async def run(
        self, ctx: GraphRunContext[MachineState]
    ) -> End | InsertCoin | SelectProduct:
        if price := PRODUCT_PRICES.get(self.product):  # (8)!
            ctx.state.product = self.product  # (9)!
            if ctx.state.user_balance >= price:  # (10)!
                ctx.state.user_balance -= price
                return End(None)
            else:
                diff = price - ctx.state.user_balance
                print(f'Not enough money for {self.product}, need {diff:0.2f} more')
                #> Not enough money for crisps, need 0.75 more
                return InsertCoin()  # (11)!
        else:
            print(f'No such product: {self.product}, try again')
            return SelectProduct()  # (12)!


vending_machine_graph = Graph(  # (13)!
    nodes=[InsertCoin, CoinsInserted, SelectProduct, Purchase]
)


async def main():
    state = MachineState()  # (14)!
    await vending_machine_graph.run(InsertCoin(), state=state)  # (15)!
    print(f'purchase successful item={state.product} change={state.user_balance:0.2f}')
    #> purchase successful item=crisps change=0.25
```

----------------------------------------

TITLE: Creating and Adding a Custom Evaluator (Python)
DESCRIPTION: Shows how to define a custom `Evaluator` by subclassing `Evaluator` and implementing the `evaluate` method. Also demonstrates adding both built-in (`IsInstance`) and custom evaluators to a `Dataset`. The custom evaluator scores based on output matching expected output.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_3

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

from simple_eval_dataset import dataset

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.evaluators.common import IsInstance

dataset.add_evaluator(IsInstance(type_name='str'))  # (1)!


@dataclass
class MyEvaluator(Evaluator):
    async def evaluate(self, ctx: EvaluatorContext[str, str]) -> float:  # (2)!
        if ctx.output == ctx.expected_output:
            return 1.0
        elif (
            isinstance(ctx.output, str)
            and ctx.expected_output.lower() in ctx.output.lower()
        ):
            return 0.8
        else:
            return 0.0

dataset.add_evaluator(MyEvaluator())
```

----------------------------------------

TITLE: Accessing Messages from RunResult (Python)
DESCRIPTION: This snippet demonstrates how to initialize a PydanticAI agent, run it synchronously with `run_sync`, and access the output from the resulting `RunResult` object. It shows a basic example of getting the agent's response.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/message-history.md#_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

result = agent.run_sync('Tell me a joke.')
print(result.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.
```

----------------------------------------

TITLE: Installing Pydantic-AI OpenAI Integration
DESCRIPTION: Command to install Pydantic-AI with OpenAI support using pip or uv package manager.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[openai]"
```

----------------------------------------

TITLE: One-line PydanticAI Example Execution
DESCRIPTION: Complete one-liner command to run a PydanticAI example with API key and dependencies setup using uv.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/index.md#2025-04-22_snippet_5

LANGUAGE: bash
CODE:
```
OPENAI_API_KEY='your-api-key' \
  uv run --with "pydantic-ai[examples]" \
  -m pydantic_ai_examples.pydantic_model
```

----------------------------------------

TITLE: dice_game_tool_kwarg.py
DESCRIPTION: This snippet demonstrates registering function tools (`roll_die`, `get_player_name`) with the Pydantic AI Agent using the `tools` argument in the constructor. It shows two methods: passing a list of functions and passing a list of `Tool` objects for more control. The example simulates a simple dice game where the agent uses the tools to get a dice roll and the player's name.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_2

LANGUAGE: python
CODE:
```
import random\n\nfrom pydantic_ai import Agent, RunContext, Tool\n\nsystem_prompt = \"\"\"\nYou're a dice game, you should roll the die and see if the number\nyou get back matches the user's guess. If so, tell them they're a winner.\nUse the player's name in the response.\n\"\"\"\n\n\ndef roll_die() -> str:\n    \"\"\"Roll a six-sided die and return the result.\"\"\"\n    return str(random.randint(1, 6))\n\n\ndef get_player_name(ctx: RunContext[str]) -> str:\n    \"\"\"Get the player's name.\"\"\"\n    return ctx.deps\n\n\nagent_a = Agent(\n    'google-gla:gemini-1.5-flash',\n    deps_type=str,\n    tools=[roll_die, get_player_name],  # (1)!\n    system_prompt=system_prompt,\n)\nagent_b = Agent(\n    'google-gla:gemini-1.5-flash',\n    deps_type=str,\n    tools=[  # (2)!\n        Tool(roll_die, takes_ctx=False),\n        Tool(get_player_name, takes_ctx=True),\n    ],\n    system_prompt=system_prompt,\n)\n\ndice_result = {}\ndice_result['a'] = agent_a.run_sync('My guess is 6', deps='Yashar')\ndice_result['b'] = agent_b.run_sync('My guess is 4', deps='Anne')\nprint(dice_result['a'].output)\n#> Tough luck, Yashar, you rolled a 4. Better luck next time.\nprint(dice_result['b'].output)\n#> Congratulations Anne, you guessed correctly! You're a winner!\n
```

----------------------------------------

TITLE: Implementing Tool Retry with ModelRetry in Pydantic-AI (Python)
DESCRIPTION: This example shows how to define a tool for a pydantic-ai Agent that uses dependency injection (`deps_type`) and raises `ModelRetry` to prompt the model to retry the tool call with corrected parameters, based on validation logic. The tool is configured to allow up to 2 retries.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_14

LANGUAGE: Python
CODE:
```
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry

from fake_database import DatabaseConn


class ChatResult(BaseModel):
    user_id: int
    message: str


agent = Agent(
    'openai:gpt-4o',
    deps_type=DatabaseConn,
    output_type=ChatResult,
)


@agent.tool(retries=2)
def get_user_by_name(ctx: RunContext[DatabaseConn], name: str) -> int:
    """Get a user's ID from their full name."""
    print(name)
    #> John
    #> John Doe
    user_id = ctx.deps.users.get(name=name)
    if user_id is None:
        raise ModelRetry(
            f'No user found with name {name!r}, remember to provide their full name'
        )
    return user_id


result = agent.run_sync(
    'Send a message to John Doe asking for coffee next week', deps=DatabaseConn()
)
print(result.output)
"""
user_id=123 message='Hello John, would you be free for coffee sometime next week? Let me know what works for you!'
"""
```

----------------------------------------

TITLE: Querying the RAG Search Agent
DESCRIPTION: This command demonstrates how to ask a question to the RAG search agent. It uses the rag module to search for information about configuring logfire with FastAPI.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/rag.md#2025-04-22_snippet_2

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.rag search "How do I configure logfire to work with FastAPI?"
```

----------------------------------------

TITLE: Initializing Seat Preference Agent with GPT-4
DESCRIPTION: Defines an AI agent for extracting user seat preferences using GPT-4. The agent handles window seats (A and F) and rows with extra legroom (1, 14, and 20).
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/multi-agent-applications.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
seat_preference_agent = Agent[None, Union[SeatPreference, Failed]](
    'openai:gpt-4o',
    output_type=Union[SeatPreference, Failed],  # type: ignore
    system_prompt=(
        "Extract the user's seat preference. "
        'Seats A and F are window seats. '
        'Row 1 is the front row and has extra leg room. '
        'Rows 14, and 20 also have extra leg room. '
    ),
)
```

----------------------------------------

TITLE: Handling Fallback Model Failures in Python 3.11+
DESCRIPTION: Shows error handling implementation for FallbackModel when all models fail, using Python 3.11's exception handling syntax. Demonstrates how to catch and process ModelHTTPError exceptions.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/index.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIModel

openai_model = OpenAIModel('gpt-4o')
anthropic_model = AnthropicModel('claude-3-5-sonnet-latest')
fallback_model = FallbackModel(openai_model, anthropic_model)

agent = Agent(fallback_model)
try:
    response = agent.run_sync('What is the capital of France?')
except* ModelHTTPError as exc_group:
    for exc in exc_group.exceptions:
        print(exc)
```

----------------------------------------

TITLE: Building the RAG Search Database
DESCRIPTION: This command builds the search database using the rag module. It requires the OPENAI_API_KEY environment variable to be set, as it will call the OpenAI embedding API multiple times.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/rag.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.rag build
```

----------------------------------------

TITLE: Running the Weather Agent from Command Line (Bash)
DESCRIPTION: Command to run the weather agent example with Python. This requires having the dependencies installed and environment variables set.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/weather-agent.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.weather_agent
```

----------------------------------------

TITLE: Running the Flight Booking Example with Python
DESCRIPTION: A bash command to run the flight booking example using Python. It assumes that dependencies are installed and environment variables are set as per the usage instructions.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/flight-booking.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.flight_booking
```

----------------------------------------

TITLE: agent_model_errors.py
DESCRIPTION: This snippet demonstrates handling UnexpectedModelBehavior when a tool repeatedly raises ModelRetry. It defines an agent and a tool `calc_volume` that retries for any size other than 42. The `capture_run_messages` context manager is used to capture the full message exchange during the agent run, allowing inspection of the interaction when the exception occurs.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_15

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent, ModelRetry, UnexpectedModelBehavior, capture_run_messages

agent = Agent('openai:gpt-4o')


@agent.tool_plain
def calc_volume(size: int) -> int:  # (1)!
    if size == 42:
        return size**3
    else:
        raise ModelRetry('Please try again.')


with capture_run_messages() as messages:  # (2)!
    try:
        result = agent.run_sync('Please get me the volume of a box with size 6.')
    except UnexpectedModelBehavior as e:
        print('An error occurred:', e)
        #> An error occurred: Tool exceeded max retries count of 1
        print('cause:', repr(e.__cause__))
        #> cause: ModelRetry('Please try again.')
        print('messages:', messages)
        """
        messages:
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Please get me the volume of a box with size 6.',
                        timestamp=datetime.datetime(...),
                        part_kind='user-prompt',
                    )
                ],
                instructions=None,
                kind='request',
            ),
            ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name='calc_volume',
                        args={'size': 6},
                        tool_call_id='pyd_ai_tool_call_id',
                        part_kind='tool-call',
                    )
                ],
                usage=Usage(
                    requests=1,
                    request_tokens=62,
                    response_tokens=4,
                    total_tokens=66,
                    details=None,
                ),
                model_name='gpt-4o',
                timestamp=datetime.datetime(...),
                kind='response',
            ),
            ModelRequest(
                parts=[
                    RetryPromptPart(
                        content='Please try again.',
                        tool_name='calc_volume',
                        tool_call_id='pyd_ai_tool_call_id',
                        timestamp=datetime.datetime(...),
                        part_kind='retry-prompt',
                    )
                ],
                instructions=None,
                kind='request',
            ),
            ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name='calc_volume',
                        args={'size': 6},
                        tool_call_id='pyd_ai_tool_call_id',
                        part_kind='tool-call',
                    )
                ],
                usage=Usage(
                    requests=1,
                    request_tokens=72,
                    response_tokens=8,
                    total_tokens=80,
                    details=None,
                ),
                model_name='gpt-4o',
                timestamp=datetime.datetime(...),
                kind='response',
            ),
        ]
        """
    else:
        print(result.output)
```

----------------------------------------

TITLE: Basic Streaming User Profile Implementation with Pydantic-AI
DESCRIPTION: Demonstrates basic streaming of a user profile using Pydantic-AI's Agent with TypedDict. The code shows how to process streaming responses for user profile data including name, date of birth, and biography fields.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/output.md#2025-04-22_snippet_6

LANGUAGE: python
CODE:
```
from datetime import date

from typing_extensions import TypedDict

from pydantic_ai import Agent


class UserProfile(TypedDict, total=False):
    name: str
    dob: date
    bio: str


agent = Agent(
    'openai:gpt-4o',
    output_type=UserProfile,
    system_prompt='Extract a user profile from the input',
)


async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for profile in result.stream():
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
```

----------------------------------------

TITLE: Setting Custom PydanticAI OpenTelemetry Providers (Python)
DESCRIPTION: Illustrates how to provide custom OpenTelemetry `TracerProvider` and `EventLoggerProvider` instances to PydanticAI's instrumentation settings using the `InstrumentationSettings` class.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_11

LANGUAGE: python
CODE:
```
from opentelemetry.sdk._events import EventLoggerProvider
from opentelemetry.sdk.trace import TracerProvider

from pydantic_ai.agent import InstrumentationSettings

instrumentation_settings = InstrumentationSettings(
    tracer_provider=TracerProvider(),
    event_logger_provider=EventLoggerProvider(),
)
```

----------------------------------------

TITLE: Using Synchronous Dependencies in PydanticAI
DESCRIPTION: Example demonstrating how to use synchronous dependencies in PydanticAI. This shows using a synchronous HTTP client and a regular function (not a coroutine) for the system prompt, which will be executed in a thread pool by PydanticAI.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.Client  # (1)!


agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,
)


@agent.system_prompt
def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  # (2)!
    response = ctx.deps.http_client.get(
        'https://example.com', headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    deps = MyDeps('foobar', httpx.Client())
    result = await agent.run(
        'Tell me a joke.',
        deps=deps,
    )
    print(result.output)
    #> Did you hear about the toothpaste scandal? They called it Colgate.
```

----------------------------------------

TITLE: Accessing Dependencies in System Prompt Functions
DESCRIPTION: Example showing how to access dependencies through the RunContext parameter in a system prompt function. The RunContext is typed with the dependency class, enabling type checking and providing access to the dependencies through the .deps attribute.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'openai:gpt-4o',
    deps_type=MyDeps,
)


@agent.system_prompt  # (1)!
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  # (2)!
    response = await ctx.deps.http_client.get(  # (3)!
        'https://example.com',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},  # (4)!
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

----------------------------------------

TITLE: Installing PydanticAI Base Package
DESCRIPTION: Basic installation command for the full PydanticAI package using pip or uv package manager. Requires Python 3.9+.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/install.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add pydantic-ai
```

----------------------------------------

TITLE: Implementing MCP Server with PydanticAI Tool
DESCRIPTION: Creates an MCP server with a poetry generation tool powered by PydanticAI's Agent using Claude 3. The server exposes a 'poet' endpoint that generates rhyming poems based on given themes.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/server.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
from mcp.server.fastmcp import FastMCP

from pydantic_ai import Agent

server = FastMCP('PydanticAI Server')
server_agent = Agent(
    'anthropic:claude-3-5-haiku-latest', system_prompt='always reply in rhyme'
)


@server.tool()
async def poet(theme: str) -> str:
    """Poem generator"""
    r = await server_agent.run(f'write a poem about {theme}')
    return r.output


if __name__ == '__main__':
    server.run()
```

----------------------------------------

TITLE: Setting Anthropic API Key Environment Variable
DESCRIPTION: Command to set the Anthropic API key as an environment variable for authentication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/anthropic.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
export ANTHROPIC_API_KEY='your-api-key'
```

----------------------------------------

TITLE: Setting Cohere API Key Environment Variable
DESCRIPTION: Command to set the Cohere API key as an environment variable for authentication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/cohere.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
export CO_API_KEY='your-api-key'
```

----------------------------------------

TITLE: Configuring Raw OpenTelemetry with PydanticAI (Python)
DESCRIPTION: Demonstrates how to manually configure OpenTelemetry trace providers and exporters, instrument PydanticAI agents, and run a simple agent task to emit traces without using Logfire.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_9

LANGUAGE: python
CODE:
```
import os

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider

from pydantic_ai.agent import Agent

os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'
exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(exporter)
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(span_processor)

set_tracer_provider(tracer_provider)

Agent.instrument_all()
agent = Agent('openai:gpt-4o')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris
```

----------------------------------------

TITLE: Setting Groq API Key Environment Variable
DESCRIPTION: Command to set up the Groq API key as an environment variable for authentication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/groq.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
export GROQ_API_KEY='your-api-key'
```

----------------------------------------

TITLE: Providing Image Input via Binary Content with pydantic-ai (Python)
DESCRIPTION: This snippet shows how to send image data directly to a pydantic-ai Agent using the BinaryContent class. It fetches image data using the httpx library (or reads from a local file) and sends it along with a text query, specifying the 'image/png' media type. This method requires fetching or reading the content yourself.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/input.md#_snippet_1

LANGUAGE: python
CODE:
```
import httpx

from pydantic_ai import Agent, BinaryContent

image_response = httpx.get('https://iili.io/3Hs4FMg.png')  # Pydantic logo

agent = Agent(model='openai:gpt-4o')
result = agent.run_sync(
    [
        'What company is this logo from?',
        BinaryContent(data=image_response.content, media_type='image/png'),  # (1)!
    ]
)
print(result.output)
```

----------------------------------------

TITLE: Using GeminiModelSettings and Handling Errors in PydanticAI (Python)
DESCRIPTION: This example illustrates how to use model-specific settings, such as `GeminiModelSettings`, to configure parameters like temperature and safety settings for a Gemini model via a PydanticAI Agent. It also includes a try-except block to catch and print `UnexpectedModelBehavior` errors, which can occur if safety thresholds are triggered.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_8

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.models.gemini import GeminiModelSettings

agent = Agent('google-gla:gemini-1.5-flash')

try:
    result = agent.run_sync(
        'Write a list of 5 very rude things that I might say to the universe after stubbing my toe in the dark:',
        model_settings=GeminiModelSettings(
            temperature=0.0,  # general model settings can also be specified
            gemini_safety_settings=[
                {
                    'category': 'HARM_CATEGORY_HARASSMENT',
                    'threshold': 'BLOCK_LOW_AND_ABOVE',
                },
                {
                    'category': 'HARM_CATEGORY_HATE_SPEECH',
                    'threshold': 'BLOCK_LOW_AND_ABOVE',
                },
            ],
        ),
    )
except UnexpectedModelBehavior as e:
    print(e)  # (1)!
    """
    Safety settings triggered, body:
    <safety settings details>
    """
```

----------------------------------------

TITLE: customize_name.py
DESCRIPTION: This snippet shows a more complex use of prepare (prepare_greet) to modify the description of a tool parameter (name) based on the deps value in the RunContext. It demonstrates registering the prepare function via the Tool dataclass and tests how the tool definition changes for different deps values ('human' vs 'machine').
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_7

LANGUAGE: python
CODE:
```
from __future__ import annotations

from typing import Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel
from pydantic_ai.tools import Tool, ToolDefinition


def greet(name: str) -> str:
    return f'hello {name}'


async def prepare_greet(
    ctx: RunContext[Literal['human', 'machine']], tool_def: ToolDefinition
) -> ToolDefinition | None:
    d = f'Name of the {ctx.deps} to greet.'
    tool_def.parameters_json_schema['properties']['name']['description'] = d
    return tool_def


greet_tool = Tool(greet, prepare=prepare_greet)
test_model = TestModel()
agent = Agent(test_model, tools=[greet_tool], deps_type=Literal['human', 'machine'])

result = agent.run_sync('testing...', deps='human')
print(result.output)
# {"greet":"hello a"}
print(test_model.last_model_request_parameters.function_tools)
# [
#     ToolDefinition(
#         name='greet',
#         description='',
#         parameters_json_schema={
#             'additionalProperties': False,
#             'properties': {
#                 'name': {'type': 'string', 'description': 'Name of the human to greet.'}
#             },
#             'required': ['name'],
#             'type': 'object',
#         },
#         outer_typed_dict_key=None,
#         strict=None,
#     )
# ]
```

----------------------------------------

TITLE: Initializing Bedrock Model by Name
DESCRIPTION: Example of creating an Agent instance using a Bedrock model identifier
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/bedrock.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('bedrock:anthropic.claude-3-sonnet-20240229-v1:0')
...
```

----------------------------------------

TITLE: Basic Gemini Agent Initialization
DESCRIPTION: Initializes a Gemini agent using the google-gla provider with a specific model.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('google-gla:gemini-2.0-flash')
...
```

----------------------------------------

TITLE: tool_only_if_42.py
DESCRIPTION: This snippet demonstrates how to use a prepare function (only_if_42) to conditionally include a tool (hitchhiker) based on the deps value in the RunContext. The tool is only available if ctx.deps is 42. It shows how to register the prepare function using the @agent.tool decorator and tests the behavior with different deps values.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_6

LANGUAGE: python
CODE:
```
from typing import Union

from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import ToolDefinition

agent = Agent('test')


async def only_if_42(
    ctx: RunContext[int], tool_def: ToolDefinition
) -> Union[ToolDefinition, None]:
    if ctx.deps == 42:
        return tool_def


@agent.tool(prepare=only_if_42)
def hitchhiker(ctx: RunContext[int], answer: str) -> str:
    return f'{ctx.deps} {answer}'


result = agent.run_sync('testing...', deps=41)
print(result.output)
# success (no tool calls)
result = agent.run_sync('testing...', deps=42)
print(result.output)
# {"hitchhiker":"42 a"}
```

----------------------------------------

TITLE: Initializing Cohere Model by Name
DESCRIPTION: Python code demonstrating how to initialize a Cohere model using the simplified name-based approach.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/cohere.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('cohere:command')
...
```

----------------------------------------

TITLE: Reusing messages with a different model
DESCRIPTION: This snippet shows how to initialize a pydantic-ai Agent with one model, run a prompt, capture the resulting message history, and then use that history to continue the conversation with a different model.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/message-history.md#_snippet_7

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)

result2 = agent.run_sync(
    'Explain?',
    model='google-gla:gemini-1.5-pro',
    message_history=result1.new_messages(),
)
print(result2.output)

print(result2.all_messages())
```

----------------------------------------

TITLE: Running Pydantic-Graph Human-in-the-Loop Q&A Graph with State Persistence - Python
DESCRIPTION: This script executes the defined Q&A graph, utilizing FileStatePersistence to save the graph's state between runs. It checks for existing state to resume the graph or starts a new run, feeding command-line input as the answer when resuming at the Evaluate node, demonstrating how to handle human interaction and state saving.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_14

LANGUAGE: python
CODE:
```
import sys
from pathlib import Path

from pydantic_graph import End
from pydantic_graph.persistence.file import FileStatePersistence
from pydantic_ai.messages import ModelMessage  # noqa: F401

from ai_q_and_a_graph import Ask, question_graph, Evaluate, QuestionState, Answer


async def main():
    answer: str | None = sys.argv[1] if len(sys.argv) > 1 else None  # (1)!
    persistence = FileStatePersistence(Path('question_graph.json'))  # (2)!
    persistence.set_graph_types(question_graph)  # (3)!

    if snapshot := await persistence.load_next():  # (4)!
        state = snapshot.state
        assert answer is not None
        node = Evaluate(answer)
    else:
        state = QuestionState()
        node = Ask()  # (5)!

    async with question_graph.iter(node, state=state, persistence=persistence) as run:
        while True:
            node = await run.next()  # (6)!
            if isinstance(node, End):  # (7)!
                print('END:', node.data)
                history = await persistence.load_all()  # (8)!
                print([e.node for e in history])
                break
            elif isinstance(node, Answer):  # (9)!
                print(node.question)
                #> What is the capital of France?
                break
            # otherwise just continue
```

----------------------------------------

TITLE: Asserting Agent-Model Message Exchange (Python)
DESCRIPTION: This Python snippet shows a list of expected messages captured from an agent run using `capture_run_messages`. It defines the sequence of `ModelRequest` and `ModelResponse` objects, including details like tool calls (`ToolCallPart`), tool returns (`ToolReturnPart`), text responses (`TextPart`), and usage statistics (`Usage`). It utilizes assertion helpers like `IsStr` and `IsNow` from `dirty_equals` for flexible comparisons of dynamic values like IDs and timestamps.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/testing.md#_snippet_3

LANGUAGE: python
CODE:
```
[
    ModelRequest(
        parts=[
            ToolCallPart(
                tool_name='weather_forecast',
                args={'location': 'London'},
                tool_call_id=IsStr(),
            )
        ],
        usage=Usage(
            requests=1,
            request_tokens=71,
            response_tokens=7,
            total_tokens=78,
            details=None,
        ),
        model_name='test',
        timestamp=IsNow(tz=timezone.utc),
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='weather_forecast',
                content='Sunny with a chance of rain',
                tool_call_id=IsStr(),
                timestamp=IsNow(tz=timezone.utc),
            ),
        ],
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='{"weather_forecast":"Sunny with a chance of rain"}',
            )
        ],
        usage=Usage(
            requests=1,
            request_tokens=77,
            response_tokens=16,
            total_tokens=93,
            details=None,
        ),
        model_name='test',
        timestamp=IsNow(tz=timezone.utc),
    ),
]
```

----------------------------------------

TITLE: Custom Provider Configuration for Anthropic Model
DESCRIPTION: Example of initializing an AnthropicModel with a custom provider configuration including API key.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/anthropic.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

model = AnthropicModel(
    'claude-3-5-sonnet-latest', provider=AnthropicProvider(api_key='your-api-key')
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Custom Provider Configuration for Gemini
DESCRIPTION: Demonstrates how to configure a custom GoogleGLAProvider with API key.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

model = GeminiModel(
    'gemini-2.0-flash', provider=GoogleGLAProvider(api_key='your-api-key')
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Custom HTTP Client Configuration for Groq
DESCRIPTION: Example of setting up a Groq model with a custom HTTP client configuration including timeout settings.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/groq.md#2025-04-22_snippet_5

LANGUAGE: python
CODE:
```
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

custom_http_client = AsyncClient(timeout=30)
model = GroqModel(
    'llama-3.3-70b-versatile',
    provider=GroqProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Serialize/Deserialize Message History Directly to JSON String (Python)
DESCRIPTION: Illustrates how to use `pydantic_core.to_json` to serialize message history directly into a JSON string and `ModelMessagesTypeAdapter.validate_json` to parse a JSON string back into a message history object, bypassing the intermediate Python object representation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/message-history.md#_snippet_6

LANGUAGE: python
CODE:
```
from pydantic_core import to_json
...
as_json_objects = to_json(history_step_1)
same_history_as_step_1 = ModelMessagesTypeAdapter.validate_json(as_json_objects)
```

----------------------------------------

TITLE: Processing Colors and Sizes with Multiple Tools
DESCRIPTION: Demonstrates using Union types to register multiple tools for handling different types of lists (strings for colors and integers for sizes).
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/output.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from typing import Union

from pydantic_ai import Agent

agent: Agent[None, Union[list[str], list[int]]] = Agent(
    'openai:gpt-4o-mini',
    output_type=Union[list[str], list[int]],  # type: ignore
    system_prompt='Extract either colors or sizes from the shapes provided.',
)

result = agent.run_sync('red square, blue circle, green triangle')
print(result.output)
#> ['red', 'blue', 'green']

result = agent.run_sync('square size 10, circle size 20, triangle size 30')
print(result.output)
#> [10, 20, 30]
```

----------------------------------------

TITLE: Manually Controlling Graph Execution with GraphRun.next (Pydantic-Graph)
DESCRIPTION: Shows how to execute a Pydantic-Graph manually step-by-step using the `GraphRun.next` method within the `Graph.iter` context. It uses the `CountDown` node example, demonstrating how to get the next node, run it explicitly, and potentially break the execution loop early. Also shows how to use `FullStatePersistence` to access the history of executed steps. Requires Pydantic-Graph and `count_down.py` for the node definition.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_11

LANGUAGE: python
CODE:
```
from pydantic_graph import End, FullStatePersistence
from count_down import CountDown, CountDownState, count_down_graph


async def main():
    state = CountDownState(counter=5)
    persistence = FullStatePersistence()  # (7)!
    async with count_down_graph.iter(
        CountDown(), state=state, persistence=persistence
    ) as run:
        node = run.next_node  # (1)!
        while not isinstance(node, End):  # (2)!
            print('Node:', node)
            # > Node: CountDown()
            # > Node: CountDown()
            # > Node: CountDown()
            # > Node: CountDown()
            if state.counter == 2:
                break  # (3)!
            node = await run.next(node)  # (4)!

        print(run.result)  # (5)!
        # > None

        for step in persistence.history:  # (6)!
            print('History Step:', step.state, step.state)
            # > History Step: CountDownState(counter=5) CountDownState(counter=5)
            # > History Step: CountDownState(counter=4) CountDownState(counter=4)
            # > History Step: CountDownState(counter=3) CountDownState(counter=3)
            # > History Step: CountDownState(counter=2) CountDownState(counter=2)

```

----------------------------------------

TITLE: Instrumenting Direct Model Requests with Logfire (Python)
DESCRIPTION: This snippet shows how to integrate Logfire instrumentation with the pydantic-ai direct API. It demonstrates configuring Logfire and instrumenting pydantic-ai to trace model requests, using a synchronous call as an example.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/direct.md#_snippet_2

LANGUAGE: python
CODE:
```
import logfire

from pydantic_ai.direct import model_request_sync
from pydantic_ai.messages import ModelRequest

logfire.configure()
logfire.instrument_pydantic_ai()

# Make a synchronous request to the model
model_response = model_request_sync(
    'anthropic:claude-3-5-haiku-latest',
    [ModelRequest.user_text_prompt('What is the capital of France?')],
)

print(model_response.parts[0].content)
#> Paris
```

----------------------------------------

TITLE: Installing PydanticAI Slim with OpenAI Integration
DESCRIPTION: Installation command for the slim version of PydanticAI with OpenAI model support only.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/install.md#2025-04-22_snippet_3

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[openai]"
```

----------------------------------------

TITLE: Installing Pydantic-AI with Groq Support
DESCRIPTION: Command to install Pydantic-AI with Groq support using pip or uv package manager.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/groq.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[groq]"
```

----------------------------------------

TITLE: Print Agent Conversation Messages (Python)
DESCRIPTION: This snippet imports the `dice_result` object from the previous example and prints the complete list of messages exchanged during the agent's execution. This includes the initial system and user prompts, tool calls made by the model, and the results returned by the tools.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_1

LANGUAGE: python
CODE:
```
from dice_game import dice_result

print(dice_result.all_messages())
"""
[
    ModelRequest(
        parts=[
            SystemPromptPart(
                content="You're a dice game, you should roll the die and see if the number you get back matches the user's guess. If so, tell them they're a winner. Use the player's name in the response.",
                timestamp=datetime.datetime(...),
                dynamic_ref=None,
                part_kind='system-prompt',
            ),
            UserPromptPart(
                content='My guess is 4',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            ),
        ],
        instructions=None,
        kind='request',
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='roll_die',
                args={},
                tool_call_id='pyd_ai_tool_call_id',
                part_kind='tool-call',
            )
        ],
        usage=Usage(
            requests=1,
            request_tokens=90,
            response_tokens=2,
            total_tokens=92,
            details=None,
        ),
        model_name='gemini-1.5-flash',
        timestamp=datetime.datetime(...),
        kind='response',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='roll_die',
                content='4',
                tool_call_id='pyd_ai_tool_call_id',
                timestamp=datetime.datetime(...),
                part_kind='tool-return',
            )
        ],
        instructions=None,
        kind='request',
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='get_player_name',
                args={},
                tool_call_id='pyd_ai_tool_call_id',
                part_kind='tool-call',
            )
        ],
        usage=Usage(
            requests=1,
            request_tokens=91,
            response_tokens=4,
            total_tokens=95,
            details=None,
        ),
        model_name='gemini-1.5-flash',
        timestamp=datetime.datetime(...),
        kind='response',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='get_player_name',
                content='Anne',
                tool_call_id='pyd_ai_tool_call_id',
                timestamp=datetime.datetime(...),
                part_kind='tool-return',
            )
        ],
        instructions=None,
        kind='request',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content="Congratulations Anne, you guessed correctly! You're a winner!",
                part_kind='text',
            )
        ],
        usage=Usage(
            requests=1,
            request_tokens=92,
            response_tokens=12,
            total_tokens=104,
            details=None,
        ),
        model_name='gemini-1.5-flash',
        timestamp=datetime.datetime(...),
        kind='response',
    ),
]
"""
```

----------------------------------------

TITLE: Configuring Together AI Integration with Pydantic
DESCRIPTION: Establishes connection to Together AI platform using Pydantic AI library. Configures the OpenAI-compatible interface for Together's Llama model and requires a Together AI API key.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_10

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIModel(
    'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free',  # model library available at https://www.together.ai/models
    provider=OpenAIProvider(
        base_url='https://api.together.xyz/v1',
        api_key='your-together-api-key',
    ),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Installing clai globally with uv (Bash)
DESCRIPTION: Installs the clai tool globally using uv tool install, making the clai command available system-wide.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/clai/README.md#_snippet_2

LANGUAGE: Bash
CODE:
```
uv tool install clai
```

----------------------------------------

TITLE: Defining a Pydantic Evals Dataset and Case (Python)
DESCRIPTION: Demonstrates how to create a `Case` with inputs, expected output, and metadata, and then include it in a `Dataset`. This forms the basis for evaluation scenarios.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_evals import Case, Dataset

case1 = Case(
    name='simple_case',
    inputs='What is the capital of France?',
    expected_output='Paris',
    metadata={'difficulty': 'easy'},
)

dataset = Dataset(cases=[case1])
```

----------------------------------------

TITLE: Serialize PydanticAI Message History to JSON (Python)
DESCRIPTION: Shows how to use `pydantic_ai.messages.ModelMessagesTypeAdapter` and `pydantic_core.to_jsonable_python` to convert an agent's message history (`result1.all_messages()`) into a Python object structure suitable for JSON serialization. It also shows how to validate this structure back into a message history object.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/message-history.md#_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_core import to_jsonable_python

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessagesTypeAdapter  # (1)!

agent = Agent('openai:gpt-4o', system_prompt='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
history_step_1 = result1.all_messages()
as_python_objects = to_jsonable_python(history_step_1)  # (2)!
same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(as_python_objects)

result2 = agent.run_sync(  # (3)!
    'Tell me a different joke.', message_history=same_history_as_step_1
)
```

----------------------------------------

TITLE: Installing PydanticAI with DuckDuckGo Search Tool
DESCRIPTION: Command to install pydantic-ai-slim with the DuckDuckGo optional group for using the DuckDuckGo search tool.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/common-tools.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[duckduckgo]"
```

----------------------------------------

TITLE: Instrumenting HTTPX with Logfire (Python)
DESCRIPTION: Demonstrates how to use `logfire.instrument_httpx` with `capture_all=True` to monitor raw HTTP requests and responses made by PydanticAI via the HTTPX library. This allows detailed inspection of communication with model providers.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_4

LANGUAGE: python
CODE:
```
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)  # (1)!
agent = Agent('openai:gpt-4o')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris
```

----------------------------------------

TITLE: Installing PydanticAI with Logfire Integration
DESCRIPTION: Installation command for PydanticAI with Logfire integration for viewing and understanding agent runs.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/install.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai[logfire]"
```

----------------------------------------

TITLE: Instrument PydanticAI with Logfire (Python)
DESCRIPTION: Python code demonstrating how to integrate Pydantic Logfire with a PydanticAI agent. It shows the necessary imports, configuration steps (`logfire.configure()`, `logfire.instrument_pydantic_ai()`), and running an agent, which will automatically generate traces and spans visible in Logfire.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_3

LANGUAGE: python
CODE:
```
import logfire

from pydantic_ai import Agent

logfire.configure()  # (1)!
logfire.instrument_pydantic_ai()  # (2)!

agent = Agent('openai:gpt-4o', instructions='Be concise, reply with one sentence.')
result = agent.run_sync('Where does "hello world" come from?')  # (3)!
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

----------------------------------------

TITLE: Making Synchronous Model Request (Python)
DESCRIPTION: This snippet shows how to use `model_request_sync` to send a user text prompt to an Anthropic Claude model. It includes the `instrument=True` flag for potential monitoring and prints the content of the first part of the model's response.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/direct.md#_snippet_3

LANGUAGE: python
CODE:
```
# Make a synchronous request to the model
model_response = model_request_sync(
    'anthropic:claude-3-5-haiku-latest',
    [ModelRequest.user_text_prompt('What is the capital of France?')],
    instrument=True
)

print(model_response.parts[0].content)
#> Paris
```

----------------------------------------

TITLE: Demonstrating Pydantic-Graph Node Dependency Injection - Python
DESCRIPTION: This example showcases how to use dependency injection in Pydantic-Graph nodes by defining GraphDeps to hold a ProcessPoolExecutor. The Increment node accesses this executor via ctx.deps to run a computation in a separate process, demonstrating how services or resources can be provided to graph nodes.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_15

LANGUAGE: python
CODE:
```
from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, FullStatePersistence, Graph, GraphRunContext


@dataclass
class GraphDeps:
    executor: ProcessPoolExecutor


@dataclass
class DivisibleBy5(BaseNode[None, GraphDeps, int]):
    foo: int

    async def run(
        self,
        ctx: GraphRunContext[None, GraphDeps],
    ) -> Increment | End[int]:
        if self.foo % 5 == 0:
            return End(self.foo)
        else:
            return Increment(self.foo)


@dataclass
class Increment(BaseNode[None, GraphDeps]):
    foo: int

    async def run(self, ctx: GraphRunContext[None, GraphDeps]) -> DivisibleBy5:
        loop = asyncio.get_running_loop()
        compute_result = await loop.run_in_executor(
            ctx.deps.executor,
            self.compute,
        )
        return DivisibleBy5(compute_result)

    def compute(self) -> int:
        return self.foo + 1


fives_graph = Graph(nodes=[DivisibleBy5, Increment])


async def main():
    with ProcessPoolExecutor() as executor:
        deps = GraphDeps(executor)
        result = await fives_graph.run(DivisibleBy5(3), deps=deps, persistence=FullStatePersistence())
    print(result.output)
    #> 5
    # the full history is quite verbose (see below), so we'll just print the summary
    print([item.node for item in result.persistence.history])
    """
    [
        DivisibleBy5(foo=3),
        Increment(foo=3),
        DivisibleBy5(foo=4),
        Increment(foo=4),
        DivisibleBy5(foo=5),
        End(data=5),
    ]
    """
```

----------------------------------------

TITLE: Iterating Graph Nodes with async for using Pydantic-Graph
DESCRIPTION: Implements a simple graph with a `CountDown` node using Pydantic-Graph. The node decrements a counter in the state until it reaches zero, then returns an `End` node with the final count. The `main` function shows how to use `Graph.iter` and `async for` to process each node execution step. Requires Pydantic-Graph.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_10

LANGUAGE: python
CODE:
```
from __future__ import annotations as _annotations

from dataclasses import dataclass
from pydantic_graph import Graph, BaseNode, End, GraphRunContext


@dataclass
class CountDownState:
    counter: int


@dataclass
class CountDown(BaseNode[CountDownState, None, int]):
    async def run(self, ctx: GraphRunContext[CountDownState]) -> CountDown | End[int]:
        if ctx.state.counter <= 0:
            return End(ctx.state.counter)
        ctx.state.counter -= 1
        return CountDown()


count_down_graph = Graph(nodes=[CountDown])


async def main():
    state = CountDownState(counter=3)
    async with count_down_graph.iter(CountDown(), state=state) as run:  # (1)!
        async for node in run:  # (2)!
            print('Node:', node)
            # > Node: CountDown()
            # > Node: CountDown()
            # > Node: CountDown()
            # > Node: CountDown()
            # > Node: End(data=0)
    print('Final output:', run.result.output)  # (3)!
    # > Final output: 0

```

----------------------------------------

TITLE: Implementing Pydantic Logfire Instrumentation in Python
DESCRIPTION: Code example showing how to set up Pydantic Logfire instrumentation for monitoring agent behavior. Demonstrates configuration of logfire, asyncpg instrumentation, and agent setup with monitoring enabled.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/index.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
...
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn

import logfire

logfire.configure()  # (1)!
logfire.instrument_asyncpg()  # (2)!

...

support_agent = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    system_prompt=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
    instrument=True,
)
```

----------------------------------------

TITLE: Evaluating Dataset with Controlled Concurrency in pydantic-evals (Python)
DESCRIPTION: This snippet demonstrates how to evaluate a `pydantic-evals` dataset using the `evaluate_sync` method, showing the difference in execution time when running with unlimited concurrency versus limiting concurrency using the `max_concurrency` parameter. It sets up a simple dataset and an async function that simulates work.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_7

LANGUAGE: python
CODE:
```
import asyncio
import time

from pydantic_evals import Case, Dataset

# Create a dataset with multiple test cases
dataset = Dataset(
    cases=[
        Case(
            name=f'case_{i}',
            inputs=i,
            expected_output=i * 2,
        )
        for i in range(5)
    ]
)


async def double_number(input_value: int) -> int:
    """Function that simulates work by sleeping for a second before returning double the input."""
    await asyncio.sleep(0.1)  # Simulate work
    return input_value * 2


# Run evaluation with unlimited concurrency
t0 = time.time()
report_default = dataset.evaluate_sync(double_number)
print(f'Evaluation took less than 0.3s: {time.time() - t0 < 0.3}')
#>
"""
      Evaluation Summary:
         double_number
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ Case ID  ┃ Inputs ┃ Outputs ┃
┡━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ case_0   │ 0      │ 0       │
├──────────┼────────┼─────────┤
│ case_1   │ 1      │ 2       │
├──────────┼────────┼─────────┤
│ case_2   │ 2      │ 4       │
├──────────┼────────┼─────────┤
│ case_3   │ 3      │ 6       │
├──────────┼────────┼─────────┤
│ Averages │        │         │
└──────────┴────────┴─────────┘
"""

# Run evaluation with limited concurrency
t0 = time.time()
report_limited = dataset.evaluate_sync(double_number, max_concurrency=1)
print(f'Evaluation took more than 0.5s: {time.time() - t0 > 0.5}')
#>
"""
      Evaluation Summary:
         double_number
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ Case ID  ┃ Inputs ┃ Outputs ┃
┡━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ case_0   │ 0      │ 0       │
├──────────┼────────┼─────────┤
│ case_1   │ 1      │ 2       │
├──────────┼────────┼─────────┤
│ case_2   │ 2      │ 4       │
├──────────┼────────┼─────────┤
│ case_3   │ 3      │ 6       │
├──────────┼────────┼─────────┤
│ case_4   │ 4      │ 8       │
├──────────┼────────┼─────────┤
│ Averages │        │         │
└──────────┴────────┴─────────┘
"""
```

----------------------------------------

TITLE: Simplifying Tool Schema for Single Object Parameter
DESCRIPTION: This snippet demonstrates how PydanticAI simplifies the tool schema when a function has a single parameter that is an object, such as a Pydantic `BaseModel`. It uses `TestModel.last_model_request_parameters` to inspect the resulting simplified schema, showing the structure when the tool parameter is a `BaseModel`.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/tools.md#_snippet_5

LANGUAGE: python
CODE:
```
from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

agent = Agent()


class Foobar(BaseModel):
    """This is a Foobar"""

    x: int
    y: str
    z: float = 3.14


@agent.tool_plain
def foobar(f: Foobar) -> str:
    return str(f)


test_model = TestModel()
result = agent.run_sync('hello', model=test_model)
print(result.output)
#> {"foobar":"x=0 y='a' z=3.14"}
print(test_model.last_model_request_parameters.function_tools)
"""
[
    ToolDefinition(
        name='foobar',
        description='This is a Foobar',
        parameters_json_schema={
            'properties': {
                'x': {'type': 'integer'},
                'y': {'type': 'string'},
                'z': {'default': 3.14, 'type': 'number'},
            },
            'required': ['x', 'y'],
            'title': 'Foobar',
            'type': 'object',
        },
        outer_typed_dict_key=None,
        strict=None,
    )
]
"""
```

----------------------------------------

TITLE: Implementing Agent Dependencies in Python
DESCRIPTION: Example showing how to create a custom dependency class for a Pydantic-AI agent with HTTP client integration and system prompt factory. Demonstrates dependency injection pattern for agent configuration and runtime behavior.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/dependencies.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient

    async def system_prompt_factory(self) -> str:  
        response = await self.http_client.get('https://example.com')
        response.raise_for_status()
        return f'Prompt: {response.text}'


joke_agent = Agent('openai:gpt-4o', deps_type=MyDeps)


@joke_agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    return await ctx.deps.system_prompt_factory()  


async def application_code(prompt: str) -> str:  
    ...
    ...
    # now deep within application code we call our agent
    async with httpx.AsyncClient() as client:
        app_deps = MyDeps('foobar', client)
        result = await joke_agent.run(prompt, deps=app_deps)  
    return result.output
```

----------------------------------------

TITLE: Installing pydantic-graph using pip/uv Bash
DESCRIPTION: This command installs the `pydantic-graph` library using either the `pip` or `uv` package manager. It is a required dependency for `pydantic-ai` and an optional one for `pydantic-ai-slim`.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add pydantic-graph
```

----------------------------------------

TITLE: Running otel-tui Docker Container (Terminal)
DESCRIPTION: Provides the command to run the `otel-tui` OpenTelemetry backend as a Docker container, exposing the OTLP endpoint on port 4318. This is a prerequisite for sending traces to `otel-tui`.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_6

LANGUAGE: txt
CODE:
```
docker run --rm -it -p 4318:4318 --name otel-tui ymtdzzz/otel-tui:latest
```

----------------------------------------

TITLE: Initializing Pydantic-AI Agent with MistralModel Object
DESCRIPTION: This snippet demonstrates how to explicitly create a MistralModel object and then pass it to the pydantic-ai Agent constructor. This gives more control over the model configuration before initializing the agent.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/mistral.md#_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel

model = MistralModel('mistral-small-latest')
agent = Agent(model)
...
```

----------------------------------------

TITLE: Customizing Bedrock Model Settings
DESCRIPTION: Example of configuring Bedrock model with custom guardrail and performance settings
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/bedrock.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

# Define Bedrock model settings with guardrail and performance configurations
bedrock_model_settings = BedrockModelSettings(
    bedrock_guardrail_config={
        'guardrailIdentifier': 'v1',
        'guardrailVersion': 'v1',
        'trace': 'enabled'
    },
    bedrock_performance_configuration={
        'latency': 'optimized'
    }
)


model = BedrockConverseModel(model_name='us.amazon.nova-pro-v1:0')

agent = Agent(model=model, model_settings=bedrock_model_settings)
```

----------------------------------------

TITLE: Instrumenting a Specific PydanticAI Model (Python)
DESCRIPTION: Demonstrates how to create an `InstrumentedModel` instance with specific instrumentation settings and use it to initialize a PydanticAI `Agent`, allowing fine-grained control over instrumentation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_12

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.instrumented import InstrumentationSettings, InstrumentedModel

settings = InstrumentationSettings()
model = InstrumentedModel('gpt-4o', settings)
agent = Agent(model)
```

----------------------------------------

TITLE: Limiting Response Tokens with PydanticAI (Python)
DESCRIPTION: Demonstrates how to use UsageLimits to restrict the number of response tokens generated by the model. Shows successful execution within the limit and an exception when the limit is exceeded. Requires pydantic_ai.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_5

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

agent = Agent('anthropic:claude-3-5-sonnet-latest')

result_sync = agent.run_sync(
    'What is the capital of Italy? Answer with just the city.',
    usage_limits=UsageLimits(response_tokens_limit=10),
)
print(result_sync.output)
#> Rome
print(result_sync.usage())
"""
Usage(requests=1, request_tokens=62, response_tokens=1, total_tokens=63, details=None)
"""

try:
    result_sync = agent.run_sync(
        'What is the capital of Italy? Answer with a paragraph.',
        usage_limits=UsageLimits(response_tokens_limit=10),
    )
except UsageLimitExceeded as e:
    print(e)
    #> Exceeded the response_tokens_limit of 10 (response_tokens=32)
```

----------------------------------------

TITLE: Setting Temperature in PydanticAI run_sync (Python)
DESCRIPTION: This snippet shows how to initialize a PydanticAI Agent and perform a synchronous run with specific model settings, in this case setting the temperature to 0.0 for deterministic output. It prints the resulting output.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_7

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')

result_sync = agent.run_sync(
    'What is the capital of Italy?', model_settings={'temperature': 0.0}
)
print(result_sync.output)
#> Rome
```

----------------------------------------

TITLE: Making a Basic Synchronous Model Request (Python)
DESCRIPTION: This snippet demonstrates how to use the `model_request_sync` function from the `pydantic_ai.direct` module to send a simple text prompt to a specified LLM model and print the resulting response content and usage statistics.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/direct.md#_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai.direct import model_request_sync
from pydantic_ai.messages import ModelRequest

# Make a synchronous request to the model
model_response = model_request_sync(
    'anthropic:claude-3-5-haiku-latest',
    [ModelRequest.user_text_prompt('What is the capital of France?')]
)

print(model_response.parts[0].content)
# print(model_response.usage)
# Output for usage is commented out but shown in the original text:
# Usage(requests=1, request_tokens=56, response_tokens=1, total_tokens=57, details=None)
```

----------------------------------------

TITLE: Running clai with a Custom Agent (Bash)
DESCRIPTION: Shows how to invoke the `clai` CLI using the `--agent` flag to load and utilize a custom `Agent` instance defined in a Python module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_8

LANGUAGE: bash
CODE:
```
uvx clai --agent custom_agent:agent "What's the weather today?"
```

----------------------------------------

TITLE: Manually Create TypeAdapter for ModelMessage List (Python)
DESCRIPTION: Provides an alternative method to the built-in `ModelMessagesTypeAdapter` by showing how to create a `pydantic.TypeAdapter` specifically for a list of `ModelMessage` objects, which can then be used for validation and serialization.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/message-history.md#_snippet_5

LANGUAGE: python
CODE:
```
from pydantic import TypeAdapter
from pydantic_ai.messages import ModelMessage
ModelMessagesTypeAdapter = TypeAdapter(list[ModelMessage])
```

----------------------------------------

TITLE: OpenAI Responses API Implementation
DESCRIPTION: Implementation of OpenAI's Responses API with web search capabilities.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_6

LANGUAGE: python
CODE:
```
from openai.types.responses import WebSearchToolParam

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model_settings = OpenAIResponsesModelSettings(
    openai_builtin_tools=[WebSearchToolParam(type='web_search_preview')],
)
model = OpenAIResponsesModel('gpt-4o')
agent = Agent(model=model, model_settings=model_settings)

result = agent.run_sync('What is the weather in Tokyo?')
print(result.output)
```

----------------------------------------

TITLE: Custom HTTP Client Configuration for Cohere
DESCRIPTION: Python code showing how to configure a Cohere model with a custom HTTP client including timeout settings.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/cohere.md#2025-04-22_snippet_5

LANGUAGE: python
CODE:
```
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel
from pydantic_ai.providers.cohere import CohereProvider

custom_http_client = AsyncClient(timeout=30)
model = CohereModel(
    'command',
    provider=CohereProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Initializing MistralModel with Custom HTTP Client
DESCRIPTION: This snippet illustrates how to provide a custom httpx.AsyncClient instance to the MistralProvider. This is useful for advanced configuration of the HTTP client, such as setting custom timeouts or proxies, which will be used for API communication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/mistral.md#_snippet_5

LANGUAGE: python
CODE:
```
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

custom_http_client = AsyncClient(timeout=30)
model = MistralModel(
    'mistral-large-latest',
    provider=MistralProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Setting OpenAI API Key (Bash)
DESCRIPTION: Sets the `OPENAI_API_KEY` environment variable, which is required to authenticate and use the OpenAI provider with the `clai` CLI.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_0

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY='your-api-key-here'
```

----------------------------------------

TITLE: Service Account Authentication for VertexAI
DESCRIPTION: Configures VertexAI authentication using a service account JSON file.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_7

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider

model = GeminiModel(
    'gemini-2.0-flash',
    provider=GoogleVertexProvider(service_account_file='path/to/service-account.json'),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Custom HTTP Client for VertexAI
DESCRIPTION: Shows how to configure a custom HTTP client for VertexAI API requests.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_10

LANGUAGE: python
CODE:
```
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider

custom_http_client = AsyncClient(timeout=30)
model = GeminiModel(
    'gemini-2.0-flash',
    provider=GoogleVertexProvider(region='asia-east1', http_client=custom_http_client),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Direct Anthropic Model Initialization
DESCRIPTION: Example of directly initializing an AnthropicModel instance and creating an Agent.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/anthropic.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-3-5-sonnet-latest')
agent = Agent(model)
...
```

----------------------------------------

TITLE: Direct Bedrock Model Initialization
DESCRIPTION: Example of explicitly creating a BedrockConverseModel instance
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/bedrock.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel

model = BedrockConverseModel('anthropic.claude-3-sonnet-20240229-v1:0')
agent = Agent(model)
...
```

----------------------------------------

TITLE: Initializing Pydantic-AI Agent with Mistral by Name (Env Var)
DESCRIPTION: This Python snippet shows how to create a pydantic-ai Agent instance using the Mistral model by providing its name directly. The library will automatically pick up the API key from the MISTRAL_API_KEY environment variable.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/mistral.md#_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('mistral:mistral-large-latest')
...
```

----------------------------------------

TITLE: Setting Mistral API Key Environment Variable
DESCRIPTION: This command sets the MISTRAL_API_KEY environment variable with your actual Mistral API key. This is the recommended way to provide your API key securely to the pydantic-ai library when using the MistralModel.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/mistral.md#_snippet_1

LANGUAGE: bash
CODE:
```
export MISTRAL_API_KEY='your-api-key'
```

----------------------------------------

TITLE: Integrating MCP Run Python with PydanticAI
DESCRIPTION: Example demonstrating how to use the MCP Run Python server with PydanticAI, including server configuration, agent setup, and execution of Python code. Shows integration with logging using logfire.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/mcp-run-python/README.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

import logfire

logfire.configure()
logfire.instrument_mcp()
logfire.instrument_pydantic_ai()

server = MCPServerStdio('deno',
    args=[
        'run',
        '-N',
        '-R=node_modules',
        '-W=node_modules',
        '--node-modules-dir=auto',
        'jsr:@pydantic/mcp-run-python',
        'stdio',
    ])
agent = Agent('claude-3-5-haiku-latest', mcp_servers=[server])


async def main():
    async with agent.run_mcp_servers():
        result = await agent.run('How many days between 2000-01-01 and 2025-03-18?')
    print(result.output)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.w

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

----------------------------------------

TITLE: Configuring Fireworks AI Integration with Pydantic
DESCRIPTION: Implements connection to Fireworks AI using Pydantic AI library. Uses the OpenAI-compatible interface with Fireworks' model library and requires a Fireworks API key.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_9

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIModel(
    'accounts/fireworks/models/qwq-32b',  # model library available at https://fireworks.ai/models
    provider=OpenAIProvider(
        base_url='https://api.fireworks.ai/inference/v1',
        api_key='your-fireworks-api-key',
    ),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Generating YAML Dataset with Pydantic Evals
DESCRIPTION: This Python snippet demonstrates how to define Pydantic models for task inputs, expected outputs, and test case metadata, then use `pydantic_evals.generation.generate_dataset` to create a dataset based on these schemas and save it to a YAML file. It includes comments explaining each step.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_10

LANGUAGE: python
CODE:
```
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from pydantic_evals import Dataset
from pydantic_evals.generation import generate_dataset


class QuestionInputs(BaseModel, use_attribute_docstrings=True):  # (1)!
    """Model for question inputs."""

    question: str
    """A question to answer"""
    context: str | None = None
    """Optional context for the question"""


class AnswerOutput(BaseModel, use_attribute_docstrings=True):  # (2)!
    """Model for expected answer outputs."""

    answer: str
    """The answer to the question"""
    confidence: float = Field(ge=0, le=1)
    """Confidence level (0-1)"""


class MetadataType(BaseModel, use_attribute_docstrings=True):  # (3)!
    """Metadata model for test cases."""

    difficulty: str
    """Difficulty level (easy, medium, hard)"""
    category: str
    """Question category"""


async def main():
    dataset = await generate_dataset(  # (4)!
        dataset_type=Dataset[QuestionInputs, AnswerOutput, MetadataType],
        n_examples=2,
        extra_instructions="""
        Generate question-answer pairs about world capitals and landmarks.
        Make sure to include both easy and challenging questions.
        """,
    )
    output_file = Path('questions_cases.yaml')
    dataset.to_file(output_file)  # (5)!
    print(output_file.read_text())
    """
    # yaml-language-server: $schema=questions_cases_schema.json
    cases:
    - name: Easy Capital Question
      inputs:
        question: What is the capital of France?
      metadata:
        difficulty: easy
        category: Geography
      expected_output:
        answer: Paris
        confidence: 0.95
      evaluators:
      - EqualsExpected
    - name: Challenging Landmark Question
      inputs:
        question: Which world-famous landmark is located on the banks of the Seine River?
      metadata:
        difficulty: hard
        category: Landmarks
      expected_output:
        answer: Eiffel Tower
        confidence: 0.9
      evaluators:
      - EqualsExpected
    """
```

----------------------------------------

TITLE: Launching clai from Agent Instance (Sync) (Python)
DESCRIPTION: Demonstrates how to directly start a synchronous `clai` interactive session from an existing `Agent` instance using the `to_cli_sync()` method.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_9

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', instructions='You always respond in Italian.')
agent.to_cli_sync()
```

----------------------------------------

TITLE: Basic VertexAI Model Initialization
DESCRIPTION: Initializes a Gemini model using the VertexAI provider with default credentials.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_6

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel

model = GeminiModel('gemini-2.0-flash', provider='google-vertex')
agent = Agent(model)
...
```

----------------------------------------

TITLE: Generating JSON Dataset with Pydantic Evals
DESCRIPTION: This Python snippet demonstrates generating a test dataset using `pydantic_evals.generation.generate_dataset` and saving it to a JSON file. It reuses the Pydantic models defined in the previous example and shows the resulting JSON structure.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_11

LANGUAGE: python
CODE:
```
from pathlib import Path

from generate_dataset_example import AnswerOutput, MetadataType, QuestionInputs

from pydantic_evals import Dataset
from pydantic_evals.generation import generate_dataset


async def main():
    dataset = await generate_dataset(  # (1)!
        dataset_type=Dataset[QuestionInputs, AnswerOutput, MetadataType],
        n_examples=2,
        extra_instructions="""
        Generate question-answer pairs about world capitals and landmarks.
        Make sure to include both easy and challenging questions.
        """,
    )
    output_file = Path('questions_cases.json')
    dataset.to_file(output_file)  # (2)!
    print(output_file.read_text())
    """
    {
      "$schema": "questions_cases_schema.json",
      "cases": [
        {
          "name": "Easy Capital Question",
          "inputs": {
            "question": "What is the capital of France?"
          },
          "metadata": {
            "difficulty": "easy",
            "category": "Geography"
          },
          "expected_output": {
            "answer": "Paris",
            "confidence": 0.95
          },
          "evaluators": [
            "EqualsExpected"
          ]
        },
        {
          "name": "Challenging Landmark Question",
          "inputs": {
            "question": "Which world-famous landmark is located on the banks of the Seine River?"
          },
          "metadata": {
            "difficulty": "hard",
            "category": "Landmarks"
          },
          "expected_output": {
            "answer": "Eiffel Tower",

```

----------------------------------------

TITLE: Generating Mermaid Diagram Code - Python
DESCRIPTION: Demonstrates how to generate the Mermaid diagram code string for a defined `pydantic-graph` graph. It imports the graph object and a starting node, then calls the `mermaid_code` method, which uses the node return types to determine the graph structure.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_7

LANGUAGE: python
CODE:
```
from vending_machine import InsertCoin, vending_machine_graph

vending_machine_graph.mermaid_code(start_node=InsertCoin)
```

----------------------------------------

TITLE: Azure OpenAI Client Configuration
DESCRIPTION: Setup for using Azure OpenAI API with custom client configuration.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_5

LANGUAGE: python
CODE:
```
from openai import AsyncAzureOpenAI

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

client = AsyncAzureOpenAI(
    azure_endpoint='...',
    api_version='2024-07-01-preview',
    api_key='your-api-key',
)

model = OpenAIModel(
    'gpt-4o',
    provider=OpenAIProvider(openai_client=client),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Providing Document Input via URL with pydantic-ai (Python)
DESCRIPTION: This snippet illustrates how to provide a document to a pydantic-ai Agent using a direct URL. It initializes an agent with a model supporting document input ('anthropic:claude-3-sonnet') and sends a list containing a text query and a DocumentUrl object pointing to the PDF file's URL.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/input.md#_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent, DocumentUrl

agent = Agent(model='anthropic:claude-3-sonnet')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        DocumentUrl(url='https://storage.googleapis.com/cloud-samples-data/generative-ai/pdf/2403.05530.pdf'),
    ]
)
print(result.output)
```

----------------------------------------

TITLE: Direct Gemini Model Initialization
DESCRIPTION: Creates a Gemini model instance directly with explicit provider specification.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel

model = GeminiModel('gemini-2.0-flash', provider='google-gla')
agent = Agent(model)
...
```

----------------------------------------

TITLE: Analyzing OpenTelemetry Spans in Pydantic Evals Evaluator (Python)
DESCRIPTION: This snippet demonstrates how to create a custom Pydantic Evals `Evaluator` that accesses and analyzes the OpenTelemetry span tree generated during the execution of an evaluation task. It shows how to find specific spans, calculate durations, check for errors, and use this information to return evaluation metrics.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_8

LANGUAGE: python
CODE:
```
import asyncio
from typing import Any

import logfire

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator
from pydantic_evals.evaluators.context import EvaluatorContext
from pydantic_evals.otel.span_tree import SpanQuery

logfire.configure(  # ensure that an OpenTelemetry tracer is configured
    send_to_logfire='if-token-present'
)


class SpanTracingEvaluator(Evaluator[str, str]):
    """Evaluator that analyzes the span tree generated during function execution."""

    def evaluate(self, ctx: EvaluatorContext[str, str]) -> dict[str, Any]:
        # Get the span tree from the context
        span_tree = ctx.span_tree
        if span_tree is None:
            return {'has_spans': False, 'performance_score': 0.0}

        # Find all spans with "processing" in the name
        processing_spans = span_tree.find(lambda node: 'processing' in node.name)

        # Calculate total processing time
        total_processing_time = sum(
            (span.duration.total_seconds() for span in processing_spans), 0.0
        )

        # Check for error spans
        error_query: SpanQuery = {'name_contains': 'error'}
        has_errors = span_tree.any(error_query)

        # Calculate a performance score (lower is better)
        performance_score = 1.0 if total_processing_time < 0.5 else 0.5

        return {
            'has_spans': True,
            'has_errors': has_errors,
            'performance_score': 0 if has_errors else performance_score,
        }


async def process_text(text: str) -> str:
    """Function that processes text with OpenTelemetry instrumentation."""
    with logfire.span('process_text'):
        # Simulate initial processing
        with logfire.span('text_processing'):
            await asyncio.sleep(0.1)
            processed = text.strip().lower()

        # Simulate additional processing
        with logfire.span('additional_processing'):
            if 'error' in processed:
                with logfire.span('error_handling'):
                    logfire.error(f'Error detected in text: {text}')
                    return f'Error processing: {text}'
            await asyncio.sleep(0.2)
            processed = processed.replace(' ', '_')

        return f'Processed: {processed}'


# Create test cases
dataset = Dataset(
    cases=[
        Case(
            name='normal_text',
            inputs='Hello World',
            expected_output='Processed: hello_world',
        ),
        Case(
            name='text_with_error',
            inputs='Contains error marker',
            expected_output='Error processing: Contains error marker',
        ),
    ],
    evaluators=[SpanTracingEvaluator()],
)

# Run evaluation - spans are automatically captured since logfire is configured
report = dataset.evaluate_sync(process_text)
```

----------------------------------------

TITLE: Implementing MCP SSE Client
DESCRIPTION: Python implementation of an MCP client using HTTP SSE transport to connect to an MCP server. Demonstrates how to create an agent and execute commands through the MCP server.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/client.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

server = MCPServerHTTP(url='http://localhost:3001/sse')
agent = Agent('openai:gpt-4o', mcp_servers=[server])


async def main():
    async with agent.run_mcp_servers():
        result = await agent.run('How many days between 2000-01-01 and 2025-03-18?')
    print(result.output)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.
```

----------------------------------------

TITLE: Iterating PydanticAI Agent Graph (Async For)
DESCRIPTION: Shows how to use `agent.iter()` as an async context manager to obtain an `AgentRun` object, which can then be iterated over asynchronously using `async for`. This allows capturing each node (step) in the agent's underlying execution graph.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o')


async def main():
    nodes = []
    # Begin an AgentRun, which is an async-iterable over the nodes of the agent's graph
    async with agent.iter('What is the capital of France?') as agent_run:
        async for node in agent_run:
            # Each node represents a step in the agent's execution
            nodes.append(node)
    print(nodes)
    """
    [
        UserPromptNode(
            user_prompt='What is the capital of France?',
            instructions=None,
            instructions_functions=[],
            system_prompts=(),
            system_prompt_functions=[],
            system_prompt_dynamic_functions={},
        ),
        ModelRequestNode(
            request=ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the capital of France?',
                        timestamp=datetime.datetime(...),
                        part_kind='user-prompt',
                    )
                ],
                instructions=None,
                kind='request',
            )
        ),
        CallToolsNode(
            model_response=ModelResponse(
                parts=[TextPart(content='Paris', part_kind='text')],
                usage=Usage(
                    requests=1,
                    request_tokens=56,
                    response_tokens=1,
                    total_tokens=57,
                    details=None,
                ),
                model_name='gpt-4o',
                timestamp=datetime.datetime(...),
                kind='response',
            )
        ),
        End(data=FinalResult(output='Paris', tool_name=None, tool_call_id=None)),
    ]
    """
    print(agent_run.result.output)
    #/> Paris
```

----------------------------------------

TITLE: Configuring Perplexity AI Integration with Pydantic
DESCRIPTION: Sets up a connection to the Perplexity AI API using Pydantic AI library. Requires a Perplexity API key and uses the 'sonar-pro' model through the OpenAI-compatible interface.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_8

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIModel(
    'sonar-pro',
    provider=OpenAIProvider(
        base_url='https://api.perplexity.ai',
        api_key='your-perplexity-api-key',
    ),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Initializing MistralModel with Custom Provider
DESCRIPTION: This example shows how to instantiate the MistralModel with a custom MistralProvider instance. This allows for specifying parameters like the API key directly or overriding the base URL for the Mistral API.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/mistral.md#_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

model = MistralModel(
    'mistral-large-latest', provider=MistralProvider(api_key='your-api-key', base_url='https://<mistral-provider-endpoint>')
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Generating Mermaid Code for Graph in pydantic-graph Python
DESCRIPTION: This Python snippet shows how to generate the Mermaid syntax string representing the structure of a defined `pydantic-graph`. The `mermaid_code` method is called on the graph instance, specifying the starting node for visualization.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_4

LANGUAGE: python
CODE:
```
from graph_example import DivisibleBy5, fives_graph

fives_graph.mermaid_code(start_node=DivisibleBy5)
```

----------------------------------------

TITLE: Custom Provider Configuration for Cohere
DESCRIPTION: Python code demonstrating how to initialize a Cohere model with a custom provider configuration.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/cohere.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel
from pydantic_ai.providers.cohere import CohereProvider

model = CohereModel('command', provider=CohereProvider(api_key='your-api-key'))
agent = Agent(model)
...
```

----------------------------------------

TITLE: Custom Groq Provider Configuration
DESCRIPTION: Example of initializing a Groq model with a custom provider and API key.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/groq.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

model = GroqModel(
    'llama-3.3-70b-versatile', provider=GroqProvider(api_key='your-api-key')
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Configuring Logfire for Alternative OTel Backend (Python)
DESCRIPTION: Illustrates how to configure the Logfire SDK to send OpenTelemetry traces to an alternative backend like `otel-tui` by setting the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable and disabling sending data to the default Logfire backend.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_7

LANGUAGE: python
CODE:
```
import os

import logfire

from pydantic_ai import Agent

os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'  # (1)!
logfire.configure(send_to_logfire=False)  # (2)!
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

agent = Agent('openai:gpt-4o')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris
```

----------------------------------------

TITLE: Configuring Logfire Integration for Pydantic Evals
DESCRIPTION: Shows how to set up Logfire integration with Pydantic Evals for trace recording and monitoring of evaluation results.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/pydantic_evals/README.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
import logfire

logfire.configure(
    send_to_logfire='if-token-present',
    environment='development',
    service_name='evals',
)

...

my_dataset.evaluate_sync(my_task)
```

----------------------------------------

TITLE: Setting PydanticAI OpenTelemetry Event Mode (Python)
DESCRIPTION: Shows how to configure PydanticAI's instrumentation settings to change the OpenTelemetry event mode from the default 'events' attribute to individual 'logs' using `InstrumentationSettings`.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_10

LANGUAGE: python
CODE:
```
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai(event_mode='logs')
agent = Agent('openai:gpt-4o')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris
```

----------------------------------------

TITLE: Defining a Custom Agent (Python)
DESCRIPTION: Provides a Python example demonstrating how to create a custom `Agent` instance with specific instructions, which can then be used with the `clai` CLI.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_7

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', instructions='You always respond in Italian.')
```

----------------------------------------

TITLE: Direct OpenAI Model Initialization
DESCRIPTION: Explicit initialization of an OpenAI model using the OpenAIModel class.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

model = OpenAIModel('gpt-4o')
agent = Agent(model)
...
```

----------------------------------------

TITLE: Initializing Anthropic Model Using Agent String Reference
DESCRIPTION: Example of creating an Agent instance using a string reference to an Anthropic model.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/anthropic.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('anthropic:claude-3-5-sonnet-latest')
...
```

----------------------------------------

TITLE: Save and Load Pydantic Evals Dataset (Python)
DESCRIPTION: This snippet demonstrates how to save a `pydantic-evals` Dataset object to a file (YAML in this case) and then load it back. It uses the dataset defined in the `judge_recipes.py` example to show the serialization and deserialization process.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_6

LANGUAGE: python
CODE:
```
from pathlib import Path

from judge_recipes import CustomerOrder, Recipe, recipe_dataset

from pydantic_evals import Dataset

recipe_transforms_file = Path('recipe_transform_tests.yaml')
recipe_dataset.to_file(recipe_transforms_file)  # (1)!
print(recipe_transforms_file.read_text())

# Load dataset from file
loaded_dataset = Dataset[CustomerOrder, Recipe, dict].from_file(recipe_transforms_file)

print(f'Loaded dataset with {len(loaded_dataset.cases)} cases')

```

----------------------------------------

TITLE: Implementing MCP stdio Client
DESCRIPTION: Python implementation of an MCP client using stdio transport to connect to an MCP server running as a subprocess. Shows server configuration and command execution.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/client.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(
    'deno',
    args=[
        'run',
        '-N',
        '-R=node_modules',
        '-W=node_modules',
        '--node-modules-dir=auto',
        'jsr:@pydantic/mcp-run-python',
        'stdio',
    ]
)
agent = Agent('openai:gpt-4o', mcp_servers=[server])


async def main():
    async with agent.run_mcp_servers():
        result = await agent.run('How many days between 2000-01-01 and 2025-03-18?')
    print(result.output)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.
```

----------------------------------------

TITLE: MCP Client Implementation for PydanticAI Server
DESCRIPTION: Demonstrates how to create an MCP client that connects to the poetry server using stdio communication. The client initializes a session, calls the 'poet' tool with a theme, and prints the generated poem.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/server.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def client():
    server_params = StdioServerParameters(
        command='uv', args=['run', 'mcp_server.py', 'server'], env=os.environ
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool('poet', {'theme': 'socks'})
            print(result.content[0].text)
            """
            Oh, socks, those garments soft and sweet,
            That nestle softly 'round our feet,
            From cotton, wool, or blended thread,
            They keep our toes from feeling dread.
            """


if __name__ == '__main__':
    asyncio.run(client())
```

----------------------------------------

TITLE: Install FastA2A Library
DESCRIPTION: Installs the FastA2A library from PyPI using either `pip` or `uv add`. This provides the core components for building A2A servers.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/a2a.md#_snippet_1

LANGUAGE: bash
CODE:
```
pip/uv-add fasta2a
```

----------------------------------------

TITLE: Customizing Mermaid Diagram Generation with Pydantic Graph Python
DESCRIPTION: Illustrates how to modify a Pydantic Graph definition to influence the generated Mermaid diagram. It shows adding labels to edges using `Annotated` and `Edge`, enabling notes from docstrings with `docstring_notes`, highlighting nodes using the `highlighted_nodes` parameter, and saving the output image using the `mermaid_save` method.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_16

LANGUAGE: python
CODE:
```
...\nfrom typing import Annotated\n\nfrom pydantic_graph import BaseNode, End, Graph, GraphRunContext, Edge\n\n...\n\n@dataclass\nclass Ask(BaseNode[QuestionState]):\n    """Generate question using GPT-4o."""\n    docstring_notes = True\n    async def run(\n        self, ctx: GraphRunContext[QuestionState]\n    ) -> Annotated[Answer, Edge(label='Ask the question')]:\n        ...\n\n...\n\n@dataclass\nclass Evaluate(BaseNode[QuestionState]):\n    answer: str\n\n    async def run(\n            self,\n            ctx: GraphRunContext[QuestionState],\n    ) -> Annotated[End[str], Edge(label='success')] | Reprimand:\n        ...\n\n...\n\nquestion_graph.mermaid_save('image.png', highlighted_nodes=[Answer])\n
```

----------------------------------------

TITLE: Initializing Groq Model Using Agent
DESCRIPTION: Example of initializing a Groq model using the Agent class with a model string identifier.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/groq.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('groq:llama-3.3-70b-versatile')
...
```

----------------------------------------

TITLE: Adding Logfire Instrumentation
DESCRIPTION: Code snippet showing how to add Logfire instrumentation to visualize MCP interactions and debug the execution flow.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/client.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()
```

----------------------------------------

TITLE: Creating and Running Graph in pydantic-graph Python
DESCRIPTION: This complete Python example defines two nodes (`DivisibleBy5` and `Increment`), creates a `Graph` instance from them, and runs the graph synchronously starting from the `DivisibleBy5(4)` node. It demonstrates basic graph definition and execution.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_3

LANGUAGE: python
CODE:
```
from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, Graph, GraphRunContext


@dataclass
class DivisibleBy5(BaseNode[None, None, int]):  # (1)!
    foo: int

    async def run(
        self,
        ctx: GraphRunContext,
    ) -> Increment | End[int]:
        if self.foo % 5 == 0:
            return End(self.foo)
        else:
            return Increment(self.foo)


@dataclass
class Increment(BaseNode):  # (2)!
    foo: int

    async def run(self, ctx: GraphRunContext) -> DivisibleBy5:
        return DivisibleBy5(self.foo + 1)


fives_graph = Graph(nodes=[DivisibleBy5, Increment])  # (3)!
result = fives_graph.run_sync(DivisibleBy5(4))  # (4)!
print(result.output)
#> 5
```

----------------------------------------

TITLE: Direct Cohere Model Initialization
DESCRIPTION: Python code showing direct initialization of a Cohere model using CohereModel class.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/cohere.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel

model = CohereModel('command')
agent = Agent(model)
...
```

----------------------------------------

TITLE: Handling Box Dimensions with Union Types
DESCRIPTION: Shows how to handle both structured data and text responses using Union types. The agent extracts box dimensions or returns an error message if information is incomplete.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/output.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from typing import Union

from pydantic import BaseModel

from pydantic_ai import Agent


class Box(BaseModel):
    width: int
    height: int
    depth: int
    units: str


agent: Agent[None, Union[Box, str]] = Agent(
    'openai:gpt-4o-mini',
    output_type=Union[Box, str],  # type: ignore
    system_prompt=(
        "Extract me the dimensions of a box, "
        "if you can't extract all data, ask the user to try again."
    ),
)

result = agent.run_sync('The box is 10x20x30')
print(result.output)
#> Please provide the units for the dimensions (e.g., cm, in, m).

result = agent.run_sync('The box is 10x20x30 cm')
print(result.output)
#> width=10 height=20 depth=30 units='cm'
```

----------------------------------------

TITLE: Printing Evaluation Report (Python)
DESCRIPTION: Prints the evaluation report summary to the console. The `include_input` and `include_output` parameters are set to `True` to show the inputs and outputs for each case, while `include_durations` is set to `False` to omit timing information.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_9

LANGUAGE: Python
CODE:
```
report.print(include_input=True, include_output=True, include_durations=False)
```

----------------------------------------

TITLE: Installing PydanticAI with MCP Support
DESCRIPTION: Command to install pydantic-ai-slim with MCP optional dependencies using pip or uv package manager.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/client.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[mcp]"
```

----------------------------------------

TITLE: Setting Mermaid Diagram Direction with Pydantic Graph Python
DESCRIPTION: Illustrates how to control the layout direction of the generated Mermaid state diagram by passing the `direction` parameter (e.g., 'LR' for Left to Right) to the `mermaid_code` method of a Pydantic Graph instance. This allows customizing the visual flow of the diagram.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_18

LANGUAGE: python
CODE:
```
from vending_machine import InsertCoin, vending_machine_graph\n\nvending_machine_graph.mermaid_code(start_node=InsertCoin, direction='LR')\n
```

----------------------------------------

TITLE: Launching clai from Agent Instance (Async) (Python)
DESCRIPTION: Demonstrates how to start an asynchronous `clai` interactive session from an existing `Agent` instance using the `to_cli()` method, suitable for use within an async context.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_10

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', instructions='You always respond in Italian.')

async def main():
    await agent.to_cli()
```

----------------------------------------

TITLE: Specifying Model with clai (Bash)
DESCRIPTION: Shows how to use the `--model` flag to explicitly select a specific AI model for the current `clai` session.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_6

LANGUAGE: bash
CODE:
```
uvx clai --model anthropic:claude-3-7-sonnet-latest
```

----------------------------------------

TITLE: Setting OpenAI API Key Environment Variable
DESCRIPTION: Command to set the OpenAI API key as an environment variable for authentication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/openai.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY='your-api-key'
```

----------------------------------------

TITLE: Using Custom BedrockProvider with Boto3 Client
DESCRIPTION: Example of creating a BedrockProvider using a pre-configured boto3 client
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/bedrock.md#2025-04-22_snippet_6

LANGUAGE: python
CODE:
```
import boto3

from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

# Using a pre-configured boto3 client
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
model = BedrockConverseModel(
    'anthropic.claude-3-sonnet-20240229-v1:0',
    provider=BedrockProvider(bedrock_client=bedrock_client),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Setting OpenAI API Environment Variable
DESCRIPTION: Command to set up the OpenAI API key as an environment variable for authentication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/index.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
export OPENAI_API_KEY=your-api-key
```

----------------------------------------

TITLE: Setting Gemini API Key Environment Variable
DESCRIPTION: Sets up the environment variable for Gemini API key authentication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
export GEMINI_API_KEY=your-api-key
```

----------------------------------------

TITLE: Setting Gemini API Environment Variable
DESCRIPTION: Command to set up the Google Gemini API key as an environment variable for authentication.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/index.md#2025-04-22_snippet_2

LANGUAGE: bash
CODE:
```
export GEMINI_API_KEY=your-api-key
```

----------------------------------------

TITLE: Streaming Text Output with Complete Response
DESCRIPTION: Shows how to stream text responses with complete text updates at each step using the Gemini model.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/output.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent

agent = Agent('google-gla:gemini-1.5-flash')


async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        async for message in result.stream_text():
            print(message)
            #> The first known
            #> The first known use of "hello,
            #> The first known use of "hello, world" was in
            #> The first known use of "hello, world" was in a 1974 textbook
            #> The first known use of "hello, world" was in a 1974 textbook about the C
            #> The first known use of "hello, world" was in a 1974 textbook about the C programming language.
```

----------------------------------------

TITLE: Setting OpenAI API Key (Bash)
DESCRIPTION: Sets the OPENAI_API_KEY environment variable required to authenticate with the OpenAI API when using clai. Replace 'your-api-key-here' with your actual API key.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/clai/README.md#_snippet_0

LANGUAGE: Bash
CODE:
```
export OPENAI_API_KEY='your-api-key-here'
```

----------------------------------------

TITLE: Custom HTTP Client Configuration for Anthropic Provider
DESCRIPTION: Example of setting up an AnthropicModel with a custom HTTP client configuration including timeout settings.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/anthropic.md#2025-04-22_snippet_5

LANGUAGE: python
CODE:
```
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

custom_http_client = AsyncClient(timeout=30)
model = AnthropicModel(
    'claude-3-5-sonnet-latest',
    provider=AnthropicProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: In-Memory Service Account Configuration
DESCRIPTION: Sets up VertexAI authentication using service account information stored in memory.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_8

LANGUAGE: python
CODE:
```
import json

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider

service_account_info = json.loads(
    '{"type": "service_account", "project_id": "my-project-id"}'
)
model = GeminiModel(
    'gemini-2.0-flash',
    provider=GoogleVertexProvider(service_account_info=service_account_info),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Defining Optional End Node in pydantic-graph Python
DESCRIPTION: This Python class extends the previous `MyNode` example, allowing the node to optionally end the graph run. It parameterizes `BaseNode` with the return type (`int`) and includes `End[int]` in the `run` method's return type union.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_2

LANGUAGE: python
CODE:
```
from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphRunContext


@dataclass
class MyNode(BaseNode[MyState, None, int]):  # (1)!
    foo: int

    async def run(
        self,
        ctx: GraphRunContext[MyState],
    ) -> AnotherNode | End[int]:  # (2)!
        if self.foo % 5 == 0:
            return End(self.foo)
        else:
            return AnotherNode()
```

----------------------------------------

TITLE: Using Custom BedrockProvider with Credentials
DESCRIPTION: Example of creating a BedrockProvider with direct AWS credentials
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/bedrock.md#2025-04-22_snippet_5

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

# Using AWS credentials directly
model = BedrockConverseModel(
    'anthropic.claude-3-sonnet-20240229-v1:0',
    provider=BedrockProvider(
        region_name='us-east-1',
        aws_access_key_id='your-access-key',
        aws_secret_access_key='your-secret-key',
    ),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Regional Configuration for VertexAI
DESCRIPTION: Demonstrates how to specify a regional endpoint for VertexAI requests.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_9

LANGUAGE: python
CODE:
```
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider

model = GeminiModel(
    'gemini-2.0-flash', provider=GoogleVertexProvider(region='asia-east1')
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Running PydanticAI Example with Gemini Model
DESCRIPTION: Command to run the Pydantic model example using Google's Gemini 1.5 Pro model instead of the default. This demonstrates the flexibility to switch between different AI models.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/pydantic-model.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
PYDANTIC_AI_MODEL=gemini-1.5-pro python/uv-run -m pydantic_ai_examples.pydantic_model
```

----------------------------------------

TITLE: Running MCP SSE Server
DESCRIPTION: Command to start the MCP SSE server using Deno with necessary permissions and configurations.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/client.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
deno run \
  -N -R=node_modules -W=node_modules --node-modules-dir=auto \
  jsr:@pydantic/mcp-run-python sse
```

----------------------------------------

TITLE: Async Seat Finding Function
DESCRIPTION: Implements an async function to handle user seat selection. It continuously prompts for input until a valid seat preference is obtained.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/multi-agent-applications.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
async def find_seat(usage: Usage) -> SeatPreference:
    message_history: Union[list[ModelMessage], None] = None
    while True:
        answer = Prompt.ask('What seat would you like?')

        result = await seat_preference_agent.run(
            answer,
            message_history=message_history,
            usage=usage,
            usage_limits=usage_limits,
        )
        if isinstance(result.output, SeatPreference):
            return result.output
        else:
            print('Could not understand seat preference. Please try again.')
            message_history = result.all_messages()
```

----------------------------------------

TITLE: Setting AWS Environment Variables
DESCRIPTION: Configuration of AWS credentials and region using environment variables
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/bedrock.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
export AWS_ACCESS_KEY_ID='your-access-key'
export AWS_SECRET_ACCESS_KEY='your-secret-key'
export AWS_DEFAULT_REGION='us-east-1'  # or your preferred region
```

----------------------------------------

TITLE: Custom HTTP Client Configuration for Gemini
DESCRIPTION: Shows how to customize the HTTP client settings for Gemini API requests.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_4

LANGUAGE: python
CODE:
```
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

custom_http_client = AsyncClient(timeout=30)
model = GeminiModel(
    'gemini-2.0-flash',
    provider=GoogleGLAProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```

----------------------------------------

TITLE: Installing Pydantic-AI with Bedrock Support
DESCRIPTION: Command to install pydantic-ai-slim with Bedrock integration support
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/bedrock.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[bedrock]"
```

----------------------------------------

TITLE: Installing VertexAI Dependencies
DESCRIPTION: Command to install PydanticAI with VertexAI support.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/gemini.md#2025-04-22_snippet_5

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[vertexai]"
```

----------------------------------------

TITLE: Create New Logfire Project via CLI (Bash)
DESCRIPTION: Command to create a new project in Logfire using the `py-cli` tool. This configures the local environment to send data to the new project, typically writing configuration to a `.logfire` directory.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_2

LANGUAGE: bash
CODE:
```
py-cli logfire projects new
```

----------------------------------------

TITLE: Installing Pydantic-AI with Mistral Support
DESCRIPTION: This command installs the pydantic-ai-slim package along with the optional 'mistral' dependencies, which are required to use the MistralModel within pydantic-ai. You can use either pip or uv for installation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/mistral.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[mistral]"
```

----------------------------------------

TITLE: Running PydanticAI Raw OTel Example (Terminal)
DESCRIPTION: Provides the command to run the Python script that demonstrates direct OpenTelemetry integration with PydanticAI, including necessary dependencies for the example.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_8

LANGUAGE: txt
CODE:
```
uv run \
  --with 'pydantic-ai-slim[openai]' \
  --with opentelemetry-sdk \
  --with opentelemetry-exporter-otlp \
  raw_otel.py
```

----------------------------------------

TITLE: Authenticate Logfire CLI (Bash)
DESCRIPTION: Command to authenticate the local environment with the Logfire service using the `py-cli` tool. This step is necessary before sending data to Logfire.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_1

LANGUAGE: bash
CODE:
```
py-cli logfire auth
```

----------------------------------------

TITLE: Running PydanticAI without HTTPX Instrumentation (Python)
DESCRIPTION: Shows the standard execution of a PydanticAI agent using Logfire without specific HTTPX instrumentation enabled. This highlights the difference in captured data compared to the instrumented version.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_5

LANGUAGE: python
CODE:
```
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai()

agent = Agent('openai:gpt-4o')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris
```

----------------------------------------

TITLE: Running PydanticAI Bank Support Example
DESCRIPTION: This bash command demonstrates how to run the bank support example using Python or uv-run. It also shows an alternative command using the PYDANTIC_AI_MODEL environment variable.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/bank-support.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.bank_support
```

----------------------------------------

TITLE: Running the Streaming Whales Example with Python/UV
DESCRIPTION: Command to run the whale information streaming example using Python/UV package manager, assuming dependencies are installed and environment variables are set.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/stream-whales.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.stream_whales
```

----------------------------------------

TITLE: Direct MCP Client Usage Example
DESCRIPTION: Example showing how to use the MCP Run Python server directly with the Python MCP client to execute NumPy operations.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/run-python.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

code = """
import numpy
a = numpy.array([1, 2, 3])
print(a)
a
"""
server_params = StdioServerParameters(
    command='deno',
    args=[
        'run',
        '-N',
        '-R=node_modules',
        '-W=node_modules',
        '--node-modules-dir=auto',
        'jsr:@pydantic/mcp-run-python',
        'stdio',
    ],
)


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(len(tools.tools))
            #> 1
            print(repr(tools.tools[0].name))
            #> 'run_python_code'
            print(repr(tools.tools[0].inputSchema))
            """
            {'type': 'object', 'properties': {'python_code': {'type': 'string', 'description': 'Python code to run'}}, 'required': ['python_code'], 'additionalProperties': False, '$schema': 'http://json-schema.org/draft-07/schema#'}
            """
            result = await session.call_tool('run_python_code', {'python_code': code})
            print(result.content[0].text)
            """
            <status>success</status>
            <dependencies>[\"numpy\"]</dependencies>
            <output>
            [1 2 3]
            </output>
            <return_value>
            [
              1,
              2,
              3
            ]
            </return_value>
            """
```

----------------------------------------

TITLE: Running Stream Markdown Example via Command Line
DESCRIPTION: Command to execute the markdown streaming example using Python or uv package manager
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/stream-markdown.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.stream_markdown
```

----------------------------------------

TITLE: Running PostgreSQL with pgvector using Docker
DESCRIPTION: This bash command sets up a Docker container running PostgreSQL with pgvector extension. It mounts a local directory for data persistence and exposes the database on port 54320.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/rag.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
mkdir postgres-data
docker run --rm \
  -e POSTGRES_PASSWORD=postgres \
  -p 54320:5432 \
  -v `pwd`/postgres-data:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
```

----------------------------------------

TITLE: Running the Chat App Example using Python
DESCRIPTION: Command to run the chat application example using Python or uv-run. This assumes dependencies are installed and environment variables are set.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/chat-app.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.chat_app
```

----------------------------------------

TITLE: Installing PydanticAI Examples Package
DESCRIPTION: Installation command for PydanticAI examples package to access and run example code.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/install.md#2025-04-22_snippet_2

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai[examples]"
```

----------------------------------------

TITLE: Installing PydanticAI Examples Dependencies
DESCRIPTION: Command to install PydanticAI with examples dependencies using pip or uv package managers.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/index.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai[examples]"
```

----------------------------------------

TITLE: Displaying Mermaid Diagram in Jupyter Notebook Python
DESCRIPTION: This Python code demonstrates how to display a Mermaid graph diagram as an image within a Jupyter notebook or IPython environment. It uses the `mermaid_image` method of the graph and `IPython.display` utilities.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_5

LANGUAGE: python
CODE:
```
from graph_example import DivisibleBy5, fives_graph
from IPython.display import Image, display

display(Image(fives_graph.mermaid_image(start_node=DivisibleBy5)))
```

----------------------------------------

TITLE: Defining Pydantic Graph Exception Classes in Python
DESCRIPTION: This code defines the exception hierarchy for the pydantic-graph package. It includes a base exception `PydanticGraphError` and several specialized exceptions for handling different error conditions in graph operations.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_graph/exceptions.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
class PydanticGraphError(Exception):
    """Base exception for pydantic-graph."""


class CycleError(PydanticGraphError):
    """Exception raised when a cycle is detected in a graph."""


class InvalidModelReferenceError(PydanticGraphError):
    """Exception raised when a model reference is invalid."""


class NotFoundError(PydanticGraphError):
    """Exception raised when a model is not found."""


class ValidationError(PydanticGraphError):
    """Exception raised when validation fails."""


class RenderError(PydanticGraphError):
    """Exception raised when rendering fails."""


class ExporterError(PydanticGraphError):
    """Exception raised when export fails."""
```

----------------------------------------

TITLE: Running clai with uvx (Bash)
DESCRIPTION: Demonstrates how to execute the `clai` CLI using `uvx`, which allows running the tool without a global installation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_1

LANGUAGE: bash
CODE:
```
uvx clai
```

----------------------------------------

TITLE: Installing Pydantic Evals with pip/uv (Basic)
DESCRIPTION: Command to install the core `pydantic-evals` package using pip or uv.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/evals.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add pydantic-evals
```

----------------------------------------

TITLE: Installing clai with pip (Bash)
DESCRIPTION: Shows the standard command for installing the `clai` tool using the `pip` package manager.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_3

LANGUAGE: bash
CODE:
```
pip install clai
```

----------------------------------------

TITLE: Installing clai with pip (Bash)
DESCRIPTION: Installs the clai package globally using pip, making the clai command available system-wide.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/clai/README.md#_snippet_3

LANGUAGE: Bash
CODE:
```
pip install clai
```

----------------------------------------

TITLE: Run A2A Server with Uvicorn
DESCRIPTION: Runs the A2A server ASGI application (`app`) using the Uvicorn server. Specifies the host and port for accessing the server.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/a2a.md#_snippet_3

LANGUAGE: bash
CODE:
```
uvicorn agent_to_a2a:app --host 0.0.0.0 --port 8000
```

----------------------------------------

TITLE: Running clai interactive session (Bash)
DESCRIPTION: Starts the interactive chat session with the AI model after clai has been installed globally using uv or pip.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/clai/README.md#_snippet_4

LANGUAGE: Bash
CODE:
```
clai
```

----------------------------------------

TITLE: Running the SQL Generation Example with Custom Prompt
DESCRIPTION: Command to run the SQL generation example with a custom prompt provided as an argument.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/sql-gen.md#2025-04-22_snippet_2

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.sql_gen "find me errors"
```

----------------------------------------

TITLE: Running the SQL Generation Example
DESCRIPTION: Command to run the SQL generation example module with dependencies installed and environment variables set.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/sql-gen.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.sql_gen
```

----------------------------------------

TITLE: Running the Question Graph Example with UV
DESCRIPTION: Command to run the question graph example using uv-run.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/question-graph.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.question_graph
```

----------------------------------------

TITLE: Getting clai Help (Bash)
DESCRIPTION: Displays the help message for the `clai` command-line interface, listing available options and usage information.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_5

LANGUAGE: bash
CODE:
```
uvx clai --help
```

----------------------------------------

TITLE: Installing MCP Run Python with Deno
DESCRIPTION: Command to install and run the MCP Run Python server using Deno with necessary permissions for network access and module management.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/run-python.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
deno run \
  -N -R=node_modules -W=node_modules --node-modules-dir=auto \
  jsr:@pydantic/mcp-run-python [stdio|sse|warmup]
```

----------------------------------------

TITLE: clai Command Line Help (Command Line)
DESCRIPTION: Displays the usage information, positional arguments, and options available for the clai command-line tool, including special prompts for interactive mode.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/clai/README.md#_snippet_5

LANGUAGE: Command Line
CODE:
```
usage: clai [-h] [-m [MODEL]] [-a AGENT] [-l] [-t [CODE_THEME]] [--no-stream] [--version] [prompt]

PydanticAI CLI v...

Special prompts:
* `/exit` - exit the interactive mode (ctrl-c and ctrl-d also work)
* `/markdown` - show the last markdown output of the last question
* `/multiline` - toggle multiline mode

positional arguments:
  prompt                AI Prompt, if omitted fall into interactive mode

options:
  -h, --help            show this help message and exit
  -m [MODEL], --model [MODEL]
                        Model to use, in format "<provider>:<model>" e.g. "openai:gpt-4o" or "anthropic:claude-3-7-sonnet-latest". Defaults to "openai:gpt-4o".
  -a AGENT, --agent AGENT
                        Custom Agent to use, in format "module:variable", e.g. "mymodule.submodule:my_agent"
  -l, --list-models     List all available models and exit
  -t [CODE_THEME], --code-theme [CODE_THEME]
                        Which colors to use for code, can be "dark", "light" or any theme from pygments.org/styles/. Defaults to "dark" which works well on dark terminals.
  --no-stream           Disable streaming from the model
  --version             Show version and exit
```

----------------------------------------

TITLE: Running MCP Server with Deno
DESCRIPTION: Command to run the MCP server using Deno with necessary permissions for network access and node_modules management. Supports different transport modes including stdio, sse, and warmup.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/mcp-run-python/README.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
deno run \
  -N -R=node_modules -W=node_modules --node-modules-dir=auto \
  jsr:@pydantic/mcp-run-python [stdio|sse|warmup]
```

----------------------------------------

TITLE: Dependency Version Specification Example
DESCRIPTION: Shows how to specify package versions using inline script metadata in Python code.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/run-python.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
# /// script
# dependencies = [\"rich<13\"]
# ///
```

----------------------------------------

TITLE: Serving documentation locally with mkdocs
DESCRIPTION: Command to run the documentation website locally using mkdocs through the uv runner.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/contributing.md#2025-04-22_snippet_6

LANGUAGE: bash
CODE:
```
uv run mkdocs serve
```

----------------------------------------

TITLE: Installing Deno runtime
DESCRIPTION: Command to install the Deno JavaScript runtime using their official shell script installer.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/contributing.md#2025-04-22_snippet_2

LANGUAGE: bash
CODE:
```
curl -fsSL https://deno.land/install.sh | sh
```

----------------------------------------

TITLE: Inline Script Metadata Example
DESCRIPTION: Demonstrates using inline script metadata for declaring dependencies in Python code executed through MCP Run Python.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/mcp/run-python.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from mcp import ClientSession
from mcp.client.stdio import stdio_client

# using `server_params` from the above example.
from mcp_run_python import server_params

code = """\
# /// script
# dependencies = [\"pydantic\", \"email-validator\"]
# ///
import pydantic

class Model(pydantic.BaseModel):
    email: pydantic.EmailStr

print(Model(email='hello@pydantic.dev'))
"""


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool('run_python_code', {'python_code': code})
            print(result.content[0].text)
            """
            <status>success</status>
            <dependencies>[\"pydantic\",\"email-validator\"]</dependencies>
            <output>
            email='hello@pydantic.dev'
            </output>
            """
```

----------------------------------------

TITLE: Running PostgreSQL with Docker for SQL Validation
DESCRIPTION: Command to run PostgreSQL in a Docker container for validating the generated SQL queries. It runs on port 54320 to avoid conflicts with other PostgreSQL instances.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/sql-gen.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
docker run --rm -e POSTGRES_PASSWORD=postgres -p 54320:5432 postgres
```

----------------------------------------

TITLE: Vending Machine Graph Visualization - Mermaid
DESCRIPTION: A Mermaid state diagram visualizing the workflow of the vending machine graph. It shows the transitions between nodes (InsertCoin, CoinsInserted, SelectProduct, Purchase) and indicates the start and potential end points of the graph execution.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_8

LANGUAGE: mermaid
CODE:
```
---
```

LANGUAGE: mermaid
CODE:
```
title: vending_machine_graph
```

LANGUAGE: mermaid
CODE:
```
---
```

LANGUAGE: mermaid
CODE:
```
stateDiagram-v2
```

LANGUAGE: mermaid
CODE:
```
  [*] --> InsertCoin
```

LANGUAGE: mermaid
CODE:
```
  InsertCoin --> CoinsInserted
```

LANGUAGE: mermaid
CODE:
```
  CoinsInserted --> SelectProduct
```

LANGUAGE: mermaid
CODE:
```
  CoinsInserted --> Purchase
```

LANGUAGE: mermaid
CODE:
```
  SelectProduct --> Purchase
```

LANGUAGE: mermaid
CODE:
```
  Purchase --> InsertCoin
```

LANGUAGE: mermaid
CODE:
```
  Purchase --> SelectProduct
```

LANGUAGE: mermaid
CODE:
```
  Purchase --> [*]
```

----------------------------------------

TITLE: Importing and Rendering Pydantic Graph Visualization using Mermaid in Markdown
DESCRIPTION: This snippet demonstrates how to include a Pydantic graph visualization using Mermaid syntax in a markdown document. The triple colon syntax indicates a custom rendering directive that would import and display the graph from the pydantic_graph.mermaid module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_graph/mermaid.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_graph.mermaid
```

----------------------------------------

TITLE: Running PydanticAI Examples
DESCRIPTION: Command to run specific example modules from the PydanticAI package.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/index.md#2025-04-22_snippet_3

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.<example_module_name>
```

----------------------------------------

TITLE: Example Mermaid State Diagram with Left-to-Right Direction
DESCRIPTION: Provides the Mermaid syntax for a state diagram demonstrating the effect of the `direction LR` setting. This results in a left-to-right flow of states and transitions, showcasing an alternative layout compared to the default top-to-bottom.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_19

LANGUAGE: mermaid
CODE:
```
---
title: vending_machine_graph
---\nstateDiagram-v2\n  direction LR\n  [*] --> InsertCoin\n  InsertCoin --> CoinsInserted\n  CoinsInserted --> SelectProduct\n  CoinsInserted --> Purchase\n  SelectProduct --> Purchase\n  Purchase --> InsertCoin\n  Purchase --> SelectProduct\n  Purchase --> [*]\n
```

----------------------------------------

TITLE: Visualizing Multi-Agent Workflow with Mermaid
DESCRIPTION: A Mermaid graph illustrating the control flow of the multi-agent flight booking system. It shows the sequence of interactions between different agents and human interventions in the booking process.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/flight-booking.md#2025-04-22_snippet_0

LANGUAGE: mermaid
CODE:
```
graph TD
  START --> search_agent("search agent")
  search_agent --> extraction_agent("extraction agent")
  extraction_agent --> search_agent
  search_agent --> human_confirm("human confirm")
  human_confirm --> search_agent
  search_agent --> FAILED
  human_confirm --> find_seat_function("find seat function")
  find_seat_function --> human_seat_choice("human seat choice")
  human_seat_choice --> find_seat_agent("find seat agent")
  find_seat_agent --> find_seat_function
  find_seat_function --> buy_flights("buy flights")
  buy_flights --> SUCCESS
```

----------------------------------------

TITLE: Copying PydanticAI Examples
DESCRIPTION: Command to copy PydanticAI examples to a local directory for editing.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/index.md#2025-04-22_snippet_6

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples --copy-to examples/
```

----------------------------------------

TITLE: Running PydanticAI Example with Default Model
DESCRIPTION: Command to run the Pydantic model example using the default OpenAI GPT-4o model. Requires dependencies to be installed and environment variables to be set beforehand.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/pydantic-model.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.pydantic_model
```

----------------------------------------

TITLE: Handling Fallback Model Failures in Python <3.11
DESCRIPTION: Demonstrates fallback model error handling for Python versions before 3.11 using the exceptiongroup backport package. Shows implementation of custom error handlers for ModelHTTPError exceptions.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/index.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
from exceptiongroup import catch

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIModel


def model_status_error_handler(exc_group: BaseExceptionGroup) -> None:
    for exc in exc_group.exceptions:
        print(exc)


openai_model = OpenAIModel('gpt-4o')
anthropic_model = AnthropicModel('claude-3-5-sonnet-latest')
fallback_model = FallbackModel(openai_model, anthropic_model)

agent = Agent(fallback_model)
with catch({ModelHTTPError: model_status_error_handler}):
    response = agent.run_sync('What is the capital of France?')
```

----------------------------------------

TITLE: Running clai with uvx (Bash)
DESCRIPTION: Executes the clai command directly using uvx, which runs the command in a temporary environment without global installation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/clai/README.md#_snippet_1

LANGUAGE: Bash
CODE:
```
uvx clai
```

----------------------------------------

TITLE: Install PydanticAI with Logfire Support (Bash)
DESCRIPTION: Command to install the `pydantic-ai` package including the optional `logfire` dependency using `pip` or `uv`. This is the first step to enable Logfire integration.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/logfire.md#_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai[logfire]"
```

----------------------------------------

TITLE: Running Pydantic Model Example
DESCRIPTION: Specific command to run the pydantic_model example module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/index.md#2025-04-22_snippet_4

LANGUAGE: bash
CODE:
```
python/uv-run -m pydantic_ai_examples.pydantic_model
```

----------------------------------------

TITLE: Install PydanticAI with A2A Extra
DESCRIPTION: Installs the PydanticAI library along with the optional `a2a` extra, which includes the FastA2A dependency. This is necessary to use the `agent.to_a2a()` method.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/a2a.md#_snippet_2

LANGUAGE: bash
CODE:
```
pip/uv-add 'pydantic-ai[a2a]'
```

----------------------------------------

TITLE: Example Mermaid State Diagram Generated from Pydantic Graph
DESCRIPTION: Provides the Mermaid syntax for a state diagram, illustrating the output from a Pydantic Graph configured with edge labels, a node note derived from a docstring, and node highlighting. It shows states, transitions with labels, a note block, and a class definition for styling.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/graph.md#_snippet_17

LANGUAGE: mermaid
CODE:
```
---
title: question_graph
---\nstateDiagram-v2\n  Ask --> Answer: Ask the question\n  note right of Ask\n    Judge the answer.\n    Decide on next step.\n  end note\n  Answer --> Evaluate\n  Evaluate --> Reprimand\n  Evaluate --> [*]: success\n  Reprimand --> Ask\n\nclassDef highlighted fill:#fdff32\nclass Answer highlighted\n
```

----------------------------------------

TITLE: Importing format_as_xml in Python
DESCRIPTION: This snippet shows the updated import path for the `format_as_xml` function, which was moved to the package root in v0.1.0 for easier access.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/changelog.md#_snippet_0

LANGUAGE: python
CODE:
```
from pydantic_ai import format_as_xml
```

----------------------------------------

TITLE: Installing Pydantic-AI with Cohere Support
DESCRIPTION: Command to install Pydantic-AI with Cohere integration using pip or uv package manager.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/models/cohere.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
pip/uv-add "pydantic-ai-slim[cohere]"
```

----------------------------------------

TITLE: Visualizing ModelMessage Structure with Mermaid
DESCRIPTION: A graph diagram showing the hierarchical structure of ModelMessage class and its relationships with different message part types including SystemPromptPart, UserPromptPart, ToolReturnPart, RetryPromptPart, TextPart, and ToolCallPart.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/messages.md#2025-04-22_snippet_0

LANGUAGE: mermaid
CODE:
```
graph RL
    SystemPromptPart(SystemPromptPart) --- ModelRequestPart
    UserPromptPart(UserPromptPart) --- ModelRequestPart
    ToolReturnPart(ToolReturnPart) --- ModelRequestPart
    RetryPromptPart(RetryPromptPart) --- ModelRequestPart
    TextPart(TextPart) --- ModelResponsePart
    ToolCallPart(ToolCallPart) --- ModelResponsePart
    ModelRequestPart("ModelRequestPart<br>(Union)") --- ModelRequest
    ModelRequest("ModelRequest(parts=list[...])") --- ModelMessage
    ModelResponsePart("ModelResponsePart<br>(Union)") --- ModelResponse
    ModelResponse("ModelResponse(parts=list[...])") --- ModelMessage("ModelMessage<br>(Union)")
```

----------------------------------------

TITLE: Starting Interactive clai Session (Bash)
DESCRIPTION: Executes the `clai` command to initiate an interactive chat session with the configured AI model in the terminal.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_4

LANGUAGE: bash
CODE:
```
clai
```

----------------------------------------

TITLE: Mypy Output for PydanticAI Type Errors (Bash)
DESCRIPTION: This snippet shows the output generated by running the `mypy` static type checker on the `type_mistakes.py` code, highlighting the specific type errors related to incompatible argument types for the system prompt decorator and a subsequent function call.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/agents.md#_snippet_11

LANGUAGE: bash
CODE:
```
➤ uv run mypy type_mistakes.py
type_mistakes.py:18: error: Argument 1 to "system_prompt" of "Agent" has incompatible type "Callable[[RunContext[str]], str]"; expected "Callable[[RunContext[User]], str]"  [arg-type]
type_mistakes.py:28: error: Argument 1 to "foobar" has incompatible type "bool"; expected "bytes"  [arg-type]
Found 2 errors in 1 file (checked 1 source file)
```

----------------------------------------

TITLE: Installing clai globally with uv (Bash)
DESCRIPTION: Provides the command to install the `clai` tool globally using the `uv` package manager.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/cli.md#_snippet_2

LANGUAGE: bash
CODE:
```
uv tool install clai
```

----------------------------------------

TITLE: Defining Pydantic AI Exceptions in Python
DESCRIPTION: This code snippet represents the exceptions module in the Pydantic AI project. It contains custom exception classes used throughout the library for error handling and reporting specific issues related to Pydantic AI operations.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/exceptions.md#2025-04-22_snippet_0

LANGUAGE: Python
CODE:
```
::: pydantic_ai.exceptions
```

----------------------------------------

TITLE: Running all code quality checks
DESCRIPTION: Command to run code formatting, linting, static type checks, and tests with coverage report generation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/contributing.md#2025-04-22_snippet_5

LANGUAGE: bash
CODE:
```
make
```

----------------------------------------

TITLE: Installing PydanticAI and dependencies using make
DESCRIPTION: Command to install PydanticAI, all its dependencies, and pre-commit hooks using the make command.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/contributing.md#2025-04-22_snippet_3

LANGUAGE: bash
CODE:
```
make install
```

----------------------------------------

TITLE: Documenting Pydantic AI Settings Module Structure
DESCRIPTION: MkDocs documentation configuration for pydantic_ai.settings module, specifying options for inherited members and target classes ModelSettings and UsageLimits.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/settings.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_ai.settings
    options:
      inherited_members: true
      members:
        - ModelSettings
        - UsageLimits
```

----------------------------------------

TITLE: Documenting format_as_xml Module Reference
DESCRIPTION: Module reference documentation using triple-colon syntax to import and display the format_as_xml module documentation
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/format_as_xml.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_ai.format_as_xml
```

----------------------------------------

TITLE: Installing pre-commit tool using uv
DESCRIPTION: Command to install the pre-commit tool using the uv package manager.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/contributing.md#2025-04-22_snippet_1

LANGUAGE: bash
CODE:
```
uv tool install pre-commit
```

----------------------------------------

TITLE: Visualizing Question Graph Flow with Mermaid
DESCRIPTION: Mermaid diagram showing the flow of the question graph, including states for asking a question, answering, evaluating the response, and congratulating or castigating based on the evaluation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/question-graph.md#2025-04-22_snippet_2

LANGUAGE: mermaid
CODE:
```
---
title: question_graph
---
stateDiagram-v2
  [*] --> Ask
  Ask --> Answer: ask the question
  Answer --> Evaluate: answer the question
  Evaluate --> Congratulate
  Evaluate --> Castigate
  Congratulate --> [*]: success
  Castigate --> Ask: try again
```

----------------------------------------

TITLE: Importing Groq Model in Pydantic AI
DESCRIPTION: This code snippet demonstrates how to import the Groq model module in Pydantic AI. It uses a special import syntax to include all contents of the groq module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/groq.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_ai.models.groq
```

----------------------------------------

TITLE: Documenting the pydantic_ai.result Module with MkDocs
DESCRIPTION: This code block defines documentation for the pydantic_ai.result module. It uses MkDocs syntax to import and display documentation for specific members of the module, including OutputDataT and StreamedRunResult.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/result.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
# `pydantic_ai.result`

::: pydantic_ai.result
    options:
        inherited_members: true
        members:
            - OutputDataT
            - StreamedRunResult
```

----------------------------------------

TITLE: Handling Chat App Client-side Logic with TypeScript
DESCRIPTION: TypeScript code for client-side rendering of messages in the chat application. This code is passed to the browser as plain text and transpiled in the browser for simplicity.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/chat-app.md#2025-04-22_snippet_3

LANGUAGE: typescript
CODE:
```
#! examples/pydantic_ai_examples/chat_app.ts
```

----------------------------------------

TITLE: Importing pydantic_ai.usage Module in Python
DESCRIPTION: This code snippet demonstrates how to import the usage module from the pydantic_ai package. It uses Python's import statement to make the module's contents available for use in the current script or module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/usage.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
::: pydantic_ai.usage
```

----------------------------------------

TITLE: Importing Mistral Model in Pydantic AI
DESCRIPTION: This code snippet demonstrates how to import the Mistral model module in Pydantic AI. It uses a special documentation syntax to reference the module contents.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/mistral.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
::: pydantic_ai.models.mistral
```

----------------------------------------

TITLE: Documenting Pydantic AI Models Module Structure
DESCRIPTION: Module documentation structure showing the key components and classes exposed in the pydantic_ai.models module, including model definitions, request parameters, tool definitions, and response handling utilities.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/base.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
# `pydantic_ai.models`

::: pydantic_ai.models
    options:
      members:
        - KnownModelName
        - ModelRequestParameters
        - Model
        - AbstractToolDefinition
        - StreamedResponse
        - ALLOW_MODEL_REQUESTS
        - check_allow_model_requests
        - override_allow_model_requests
```

----------------------------------------

TITLE: Importing Pydantic Evals Reporting Module Reference
DESCRIPTION: Markdown directive to include documentation for the pydantic_evals.reporting module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_evals/reporting.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_evals.reporting
```

----------------------------------------

TITLE: Python Module Path Reference
DESCRIPTION: File path reference for the example implementation showing where the streaming markdown code is located
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/stream-markdown.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/stream_markdown.py
```

----------------------------------------

TITLE: Rendering Chat App Frontend with HTML
DESCRIPTION: HTML code for the chat application's frontend. This simple page provides the structure for rendering the chat interface in the browser.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/chat-app.md#2025-04-22_snippet_2

LANGUAGE: html
CODE:
```
#! examples/pydantic_ai_examples/chat_app.html
```

----------------------------------------

TITLE: Module Reference for Common Tools
DESCRIPTION: Documentation reference structure for DuckDuckGo and Tavily integration tools in the pydantic-ai common_tools package.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/common_tools.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
# `pydantic_ai.common_tools`

::: pydantic_ai.common_tools.duckduckgo

::: pydantic_ai.common_tools.tavily
```

----------------------------------------

TITLE: Example Pydantic Model Implementation File Reference
DESCRIPTION: Reference to the example Python file that demonstrates how to use PydanticAI to create Pydantic models from text input. The actual code is not shown but is referenced by its path.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/pydantic-model.md#2025-04-22_snippet_2

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/pydantic_model.py
```

----------------------------------------

TITLE: Python Question Graph Implementation Reference
DESCRIPTION: Reference to the Python file containing the question graph implementation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/question-graph.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/question_graph.py
```

----------------------------------------

TITLE: Cloning and navigating to the PydanticAI repository
DESCRIPTION: Commands to clone your fork of the PydanticAI repository and navigate into the project directory.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/contributing.md#2025-04-22_snippet_0

LANGUAGE: bash
CODE:
```
git clone git@github.com:<your username>/pydantic-ai.git
cd pydantic-ai
```

----------------------------------------

TITLE: Module Import Reference Declaration in Markdown
DESCRIPTION: Markdown documentation structure specifying the module components to be documented including Agent classes, run-related types, and instrumentation settings.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/agent.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_ai.agent
    options:
        members:
            - Agent
            - AgentRun
            - AgentRunResult
            - EndStrategy
            - RunOutputDataT
            - capture_run_messages
            - InstrumentationSettings
```

----------------------------------------

TITLE: Markdown Documentation for Cohere Integration
DESCRIPTION: Documentation segment explaining the Cohere model module location and linking to authentication setup instructions.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/cohere.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
# `pydantic_ai.models.cohere`

## Setup

For details on how to set up authentication with this model, see [model configuration for Cohere](../../models/cohere.md).

::: pydantic_ai.models.cohere
```

----------------------------------------

TITLE: Importing Pydantic AI Gemini Module in Python
DESCRIPTION: This code snippet demonstrates how to import the pydantic_ai.models.gemini module. It's part of the documentation explaining how to use the custom Gemini API interface.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/gemini.md#2025-04-22_snippet_0

LANGUAGE: Python
CODE:
```
::: pydantic_ai.models.gemini
```

----------------------------------------

TITLE: Referencing Pydantic Graph Module in Documentation
DESCRIPTION: This code snippet uses a specific documentation syntax to reference and include the contents of the pydantic_graph.graph module. It's likely used to generate API documentation for the module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_graph/graph.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_graph.graph
```

----------------------------------------

TITLE: Exporting Members from pydantic_graph.nodes Module in Python
DESCRIPTION: This code block lists the exported members from the pydantic_graph.nodes module, including type definitions and classes. The members include state types, context handlers, node definitions, and edge connections for building graph structures.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_graph/nodes.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
::: pydantic_graph.nodes
    options:
        members:
            - StateT
            - GraphRunContext
            - BaseNode
            - End
            - Edge
            - DepsT
            - RunEndT
            - NodeRunEndT
```

----------------------------------------

TITLE: Control Flow Diagram
DESCRIPTION: Mermaid diagram showing the control flow between flight search and seat selection processes.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/multi-agent-applications.md#2025-04-22_snippet_6

LANGUAGE: mermaid
CODE:
```
graph TB
  START --> ask_user_flight["ask user for flight"]

  subgraph find_flight
    flight_search_agent --> ask_user_flight
    ask_user_flight --> flight_search_agent
  end

  flight_search_agent --> ask_user_seat["ask user for seat"]
  flight_search_agent --> END

  subgraph find_seat
    seat_preference_agent --> ask_user_seat
    ask_user_seat --> seat_preference_agent
  end

  seat_preference_agent --> END
```

----------------------------------------

TITLE: Reference to the Stream Whales Python Example File
DESCRIPTION: Reference link to the stream_whales.py example file that demonstrates streaming structured output from GPT-4 with validation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/stream-whales.md#2025-04-22_snippet_1

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/stream_whales.py
```

----------------------------------------

TITLE: Bedrock Model Documentation Link
DESCRIPTION: Markdown code block showing a reference link to detailed Bedrock model configuration documentation.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/bedrock.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
# `pydantic_ai.models.bedrock`

## Setup

For details on how to set up authentication with this model, see [model configuration for Bedrock](../../models/bedrock.md).

::: pydantic_ai.models.bedrock
```

----------------------------------------

TITLE: Referencing Pydantic Evals Dataset Module in Documentation
DESCRIPTION: This snippet uses a specialized documentation directive (likely for MkDocs or a similar documentation generator) to include or reference the documentation for the pydantic_evals.dataset module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_evals/dataset.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_evals.dataset
```

----------------------------------------

TITLE: SQL Generation Example Code Reference
DESCRIPTION: Reference to the main Python file that contains the SQL generation example code. The actual code is not included in the snippet, only the file path.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/examples/sql-gen.md#2025-04-22_snippet_3

LANGUAGE: python
CODE:
```
#! examples/pydantic_ai_examples/sql_gen.py
```

----------------------------------------

TITLE: Fetch and Display Changelog in JavaScript
DESCRIPTION: This JavaScript code fetches the full changelog from a specified HTML file and injects its content into a div element on the page, providing a dynamic display of release notes.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/changelog.md#_snippet_1

LANGUAGE: javascript
CODE:
```
fetch('/changelog.html').then(r => {
  if (r.ok) {
    r.text().then(t => {
      document.getElementById('display-changelog').innerHTML = t;
    });
  }
});
```

----------------------------------------

TITLE: Referencing OpenAI Module in Pydantic-AI Documentation
DESCRIPTION: This code snippet is a Markdown directive that includes the documentation for the pydantic_ai.models.openai module. It's used to embed the module's documentation within the current page.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/models/openai.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_ai.models.openai
```

----------------------------------------

TITLE: Importing pydantic_evals.generation Module in MkDocs
DESCRIPTION: This markdown snippet shows how to include auto-documentation for the pydantic_evals.generation module in MkDocs documentation. The ::: syntax is used to automatically import and render documentation for the specified module.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_evals/generation.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_evals.generation
```

----------------------------------------

TITLE: Importing Pydantic Graph Persistence Module
DESCRIPTION: This code snippet shows how to import the pydantic_graph.persistence module and its submodules (in-memory and file-based persistence) in documentation format.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_graph/persistence.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
# `pydantic_graph.persistence`

::: pydantic_graph.persistence

::: pydantic_graph.persistence.in_mem

::: pydantic_graph.persistence.file
```

----------------------------------------

TITLE: Documenting Pydantic AI Provider Modules
DESCRIPTION: Index of provider modules showing the package structure for various AI service integrations in pydantic-ai.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/providers.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
# `pydantic_ai.providers`

::: pydantic_ai.providers.Provider

::: pydantic_ai.providers.google_vertex

::: pydantic_ai.providers.openai

::: pydantic_ai.providers.deepseek

::: pydantic_ai.providers.bedrock

::: pydantic_ai.providers.groq

::: pydantic_ai.providers.azure

::: pydantic_ai.providers.cohere

::: pydantic_ai.providers.mistral
```

----------------------------------------

TITLE: Importing and Documenting pydantic_ai.tools Module in Markdown
DESCRIPTION: This code snippet uses a documentation syntax to import and display the contents of the pydantic_ai.tools module. It's likely part of a larger documentation system that automatically generates API documentation from code.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/tools.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
::: pydantic_ai.tools
```

----------------------------------------

TITLE: Listing available make commands
DESCRIPTION: Command to display help information showing all available make commands for the project.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/contributing.md#2025-04-22_snippet_4

LANGUAGE: bash
CODE:
```
make help
```

----------------------------------------

TITLE: Markdown Module Reference for pydantic_evals.otel
DESCRIPTION: Module reference documentation marker using markdown code block to identify the pydantic_evals.otel module path.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/docs/api/pydantic_evals/otel.md#2025-04-22_snippet_0

LANGUAGE: markdown
CODE:
```
# `pydantic_evals.otel`

::: pydantic_evals.otel
```

----------------------------------------

TITLE: Configuring Path for Pydantic AI Documentation Examples
DESCRIPTION: Documentation note indicating that this directory is added to sys.path during test execution to support example code testing.
SOURCE: https://github.com/pydantic/pydantic-ai/blob/main/tests/example_modules/README.md#2025-04-22_snippet_0

LANGUAGE: python
CODE:
```
# docs examples imports
```
