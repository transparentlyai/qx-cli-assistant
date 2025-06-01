TITLE: Installing the OpenAI Python library with pip
DESCRIPTION: Command to install the OpenAI Python library from PyPI using pip. This is the standard way to add the library to your Python environment.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_0

LANGUAGE: sh
CODE:
```
# install from PyPI
pip install openai
```

----------------------------------------

TITLE: Function Tool Calls with Pydantic Models
DESCRIPTION: Shows how to use Pydantic models for automatic parsing of function tool calls. The example implements a database query builder with strict schema validation.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_1

LANGUAGE: python
CODE:
```
from enum import Enum
from typing import List, Union
from pydantic import BaseModel
import openai

class Table(str, Enum):
    orders = "orders"
    customers = "customers"
    products = "products"

class Column(str, Enum):
    id = "id"
    status = "status"
    expected_delivery_date = "expected_delivery_date"
    delivered_at = "delivered_at"
    shipped_at = "shipped_at"
    ordered_at = "ordered_at"
    canceled_at = "canceled_at"

class Operator(str, Enum):
    eq = "="
    gt = ">"
    lt = "<"
    le = "<="
    ge = ">="
    ne = "!="

class OrderBy(str, Enum):
    asc = "asc"
    desc = "desc"

class DynamicValue(BaseModel):
    column_name: str

class Condition(BaseModel):
    column: str
    operator: Operator
    value: Union[str, int, DynamicValue]

class Query(BaseModel):
    table_name: Table
    columns: List[Column]
    conditions: List[Condition]
    order_by: OrderBy

client = openai.OpenAI()
completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant. The current date is August 6, 2024. You help users query for the data they are looking for by calling the query function.",
        },
        {
            "role": "user",
            "content": "look up all my orders in may of last year that were fulfilled but not delivered on time",
        },
    ],
    tools=[
        openai.pydantic_function_tool(Query),
    ],
)

tool_call = (completion.choices[0].message.tool_calls or [])[0]
print(tool_call.function)
assert isinstance(tool_call.function.parsed_arguments, Query)
print(tool_call.function.parsed_arguments.table_name)
```

----------------------------------------

TITLE: Using the Responses API with OpenAI
DESCRIPTION: Example of using the Responses API to generate text from an OpenAI model. It creates a client, sets the API key, and sends a request to generate text based on instructions and input.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_1

LANGUAGE: python
CODE:
```
import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

response = client.responses.create(
    model="gpt-4o",
    instructions="You are a coding assistant that talks like a pirate.",
    input="How do I check if a Python object is an instance of a class?",
)

print(response.output_text)
```

----------------------------------------

TITLE: Using the Chat Completions API with OpenAI
DESCRIPTION: Example of using the traditional Chat Completions API to generate text from an OpenAI model. It creates a client and sends a chat completion request with role-based messages.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_2

LANGUAGE: python
CODE:
```
from openai import OpenAI

client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "developer", "content": "Talk like a pirate."},
        {
            "role": "user",
            "content": "How do I check if a Python object is an instance of a class?",
        },
    ],
)

print(completion.choices[0].message.content)
```

----------------------------------------

TITLE: Create Chat Completion (Python)
DESCRIPTION: Calls the OpenAI Chat Completions API to generate messages based on a conversation history and parameters. Returns a ChatCompletion object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_5

LANGUAGE: python
CODE:
```
client.chat.completions.create(**params)
```

----------------------------------------

TITLE: Pydantic Model Parsing with OpenAI Chat Completions
DESCRIPTION: Demonstrates how to use Pydantic models to automatically parse structured outputs from OpenAI chat completions. The example shows parsing a math problem solution into a defined data structure.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_0

LANGUAGE: python
CODE:
```
from typing import List
from pydantic import BaseModel
from openai import OpenAI

class Step(BaseModel):
    explanation: str
    output: str

class MathResponse(BaseModel):
    steps: List[Step]
    final_answer: str

client = OpenAI()
completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "You are a helpful math tutor."},
        {"role": "user", "content": "solve 8x + 31 = 2"},
    ],
    response_format=MathResponse,
)

message = completion.choices[0].message
if message.parsed:
    print(message.parsed.steps)
    print("answer: ", message.parsed.final_answer)
else:
    print(message.refusal)
```

----------------------------------------

TITLE: Handling Errors in OpenAI Python SDK
DESCRIPTION: Demonstrates error handling with try-except blocks for various API errors including connection issues and different status codes returned by the OpenAI API.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_16

LANGUAGE: python
CODE:
```
import openai
from openai import OpenAI

client = OpenAI()

try:
    client.fine_tuning.jobs.create(
        model="gpt-4o",
        training_file="file-abc123",
    )
except openai.APIConnectionError as e:
    print("The server could not be reached")
    print(e.__cause__)  # an underlying Exception, likely raised within httpx.
except openai.RateLimitError as e:
    print("A 429 status code was received; we should back off a bit.")
except openai.APIStatusError as e:
    print("Another non-200-range status code was received")
    print(e.status_code)
    print(e.response)
```

----------------------------------------

TITLE: Create Embedding (Python)
DESCRIPTION: Calls the OpenAI Embeddings API to generate vector embeddings for input text. Returns a CreateEmbeddingResponse object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_12

LANGUAGE: python
CODE:
```
client.embeddings.create(**params)
```

----------------------------------------

TITLE: Async Streaming with OpenAI Chat Completions
DESCRIPTION: Demonstrates how to use the async streaming API for chat completions. Shows usage of the context manager and event handling for streamed responses.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_2

LANGUAGE: python
CODE:
```
from openai import AsyncOpenAI

client = AsyncOpenAI()

async with client.beta.chat.completions.stream(
    model='gpt-4o-2024-08-06',
    messages=[...],
) as stream:
    async for event in stream:
        if event.type == 'content.delta':
            print(event.content, flush=True, end='')
```

----------------------------------------

TITLE: Using the AsyncOpenAI client for asynchronous operations
DESCRIPTION: Example of using the AsyncOpenAI client for asynchronous operations. It imports the AsyncOpenAI class, creates an async client, and demonstrates how to use it with async/await syntax.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_5

LANGUAGE: python
CODE:
```
import os
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)


async def main() -> None:
    response = await client.responses.create(
        model="gpt-4o", input="Explain disestablishmentarianism to a smart five year old."
    )
    print(response.output_text)


asyncio.run(main())
```

----------------------------------------

TITLE: Determining Installed OpenAI Library Version
DESCRIPTION: Shows how to check which version of the OpenAI Python library is currently installed and being used at runtime, which is useful for debugging and ensuring compatibility.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_28

LANGUAGE: python
CODE:
```
import openai
print(openai.__version__)
```

----------------------------------------

TITLE: Streaming responses with OpenAI
DESCRIPTION: Example of streaming responses using Server Side Events (SSE). The code creates a stream and iterates through events as they arrive, providing real-time access to model outputs.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_6

LANGUAGE: python
CODE:
```
from openai import OpenAI

client = OpenAI()

stream = client.responses.create(
    model="gpt-4o",
    input="Write a one-sentence bedtime story about a unicorn.",
    stream=True,
)

for event in stream:
    print(event)
```

----------------------------------------

TITLE: Asynchronous pagination with the OpenAI API
DESCRIPTION: Example of using asynchronous auto-pagination with the OpenAI API. It demonstrates how to iterate through paginated results asynchronously using async for, automatically fetching more pages as needed.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_11

LANGUAGE: python
CODE:
```
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()


async def main() -> None:
    all_jobs = []
    # Iterate through items across all pages, issuing requests as needed.
    async for job in client.fine_tuning.jobs.list(
        limit=20,
    ):
        all_jobs.append(job)
    print(all_jobs)


asyncio.run(main())
```

----------------------------------------

TITLE: Iterating Over Events in OpenAI Assistant API Stream
DESCRIPTION: This example shows how to iterate over all streamed events from an Assistant run, specifically printing text from text delta events.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_4

LANGUAGE: python
CODE:
```
with client.beta.threads.runs.stream(
  thread_id=thread.id,
  assistant_id=assistant.id
) as stream:
    for event in stream:
        # Print the text from text delta events
        if event.event == "thread.message.delta" and event.data.delta.content:
            print(event.data.delta.content[0].text)
```

----------------------------------------

TITLE: Pagination with the OpenAI API using auto-pagination
DESCRIPTION: Example of using auto-pagination with the OpenAI API. The code iterates through all items across multiple pages, automatically fetching more pages as needed without manual pagination handling.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_10

LANGUAGE: python
CODE:
```
from openai import OpenAI

client = OpenAI()

all_jobs = []
# Automatically fetches more pages as needed.
for job in client.fine_tuning.jobs.list(
    limit=20,
):
    # Do something with job here
    all_jobs.append(job)
print(all_jobs)
```

----------------------------------------

TITLE: Accessing Request IDs in OpenAI Python SDK
DESCRIPTION: Shows how to access request IDs from successful responses and from API error objects for debugging and reporting issues to OpenAI.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_17

LANGUAGE: python
CODE:
```
response = await client.responses.create(
    model="gpt-4o-mini",
    input="Say 'this is a test'.",
)
print(response._request_id)  # req_123
```

LANGUAGE: python
CODE:
```
import openai

try:
    completion = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Say this is a test"}], model="gpt-4"
    )
except openai.APIStatusError as exc:
    print(exc.request_id)  # req_123
    raise exc
```

----------------------------------------

TITLE: Configuring Azure OpenAI Client for API Interaction
DESCRIPTION: Demonstrates how to set up and use the AzureOpenAI client to interact with Azure's OpenAI service. Includes setting the API version, endpoint, and creating a chat completion with a deployment model.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_27

LANGUAGE: python
CODE:
```
from openai import AzureOpenAI

# gets the API Key from environment variable AZURE_OPENAI_API_KEY
client = AzureOpenAI(
    # https://learn.microsoft.com/azure/ai-services/openai/reference#rest-api-versioning
    api_version="2023-07-01-preview",
    # https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
    azure_endpoint="https://example-endpoint.openai.azure.com",
)

completion = client.chat.completions.create(
    model="deployment-name",  # e.g. gpt-35-instant
    messages=[
        {
            "role": "user",
            "content": "How do I output all files in a directory using Python?",
        },
    ],
)
print(completion.to_json())
```

----------------------------------------

TITLE: Search a Vector Store (Python)
DESCRIPTION: Method signature for performing a search within a specific Vector Store by its ID using the OpenAI Python client. It takes search parameters and returns a SyncPage containing VectorStoreSearchResponse objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_62

LANGUAGE: python
CODE:
```
client.vector_stores.search(vector_store_id, **params) -> SyncPage[VectorStoreSearchResponse]
```

----------------------------------------

TITLE: Creating a Run and Subscribing to Events with Python OpenAI SDK
DESCRIPTION: This snippet demonstrates how to create an event handler class and use it to stream responses from an Assistant run. It shows how to handle different types of events such as text creation, text delta, and tool calls.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_3

LANGUAGE: python
CODE:
```
from typing_extensions import override
from openai import AssistantEventHandler, OpenAI
from openai.types.beta.threads import Text, TextDelta
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta

client = openai.OpenAI()

# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.

class EventHandler(AssistantEventHandler):
  @override
  def on_text_created(self, text: Text) -> None:
    print(f"\nassistant > ", end="", flush=True)

  @override
  def on_text_delta(self, delta: TextDelta, snapshot: Text):
    print(delta.value, end="", flush=True)

  @override
  def on_tool_call_created(self, tool_call: ToolCall):
    print(f"\nassistant > {tool_call.type}\n", flush=True)

  @override
  def on_tool_call_delta(self, delta: ToolCallDelta, snapshot: ToolCall):
    if delta.type == "code_interpreter" and delta.code_interpreter:
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)

# Then, we use the `stream` SDK helper
# with the `EventHandler` class to create the Run
# and stream the response.

with client.beta.threads.runs.stream(
  thread_id="thread_id",
  assistant_id="assistant_id",
  event_handler=EventHandler(),
) as stream:
  stream.until_done()
```

----------------------------------------

TITLE: Setting Timeouts in OpenAI Python SDK
DESCRIPTION: Shows how to configure request timeouts globally or per-request, including examples of simple timeout values and more granular timeout control.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_19

LANGUAGE: python
CODE:
```
from openai import OpenAI

# Configure the default for all requests:
client = OpenAI(
    # 20 seconds (default is 10 minutes)
    timeout=20.0,
)

# More granular control:
client = OpenAI(
    timeout=httpx.Timeout(60.0, read=5.0, write=10.0, connect=2.0),
)

# Override per-request:
client.with_options(timeout=5.0).chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "How can I list all files in a directory using Python?",
        }
    ],
    model="gpt-4o",
)
```

----------------------------------------

TITLE: Import Chat Model Type (Python)
DESCRIPTION: Imports the ChatModel type definition, used to specify the model for chat completions.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_3

LANGUAGE: python
CODE:
```
from openai.types import ChatModel
```

----------------------------------------

TITLE: Uploading Files with OpenAI Python SDK
DESCRIPTION: Shows how to upload files to the OpenAI API using Path objects, bytes, or tuples of filename, contents, and media type.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_15

LANGUAGE: python
CODE:
```
from pathlib import Path
from openai import OpenAI

client = OpenAI()

client.files.create(
    file=Path("input.jsonl"),
    purpose="fine-tune",
)
```

----------------------------------------

TITLE: Creating Streams with OpenAI Python SDK
DESCRIPTION: This section shows three helper methods for creating streams: streaming an existing run, creating a thread with a message and streaming the run, and submitting tool outputs to a run and streaming the response.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_6

LANGUAGE: python
CODE:
```
client.beta.threads.runs.stream()
```

LANGUAGE: python
CODE:
```
client.beta.threads.create_and_run_stream()
```

LANGUAGE: python
CODE:
```
client.beta.threads.runs.submit_tool_outputs_stream()
```

----------------------------------------

TITLE: Configuring Retries in OpenAI Python SDK
DESCRIPTION: Demonstrates how to configure retry behavior globally or per-request, either disabling retries or increasing the maximum number of retries.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_18

LANGUAGE: python
CODE:
```
from openai import OpenAI

# Configure the default for all requests:
client = OpenAI(
    # default is 2
    max_retries=0,
)

# Or, configure per-request:
client.with_options(max_retries=5).chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "How can I get the name of the current day in JavaScript?",
        }
    ],
    model="gpt-4o",
)
```

----------------------------------------

TITLE: Managing HTTP Resources with Context Manager in OpenAI Python Client
DESCRIPTION: Shows how to properly manage HTTP resources in the OpenAI client using Python's context manager pattern. This ensures connections are properly closed when operations are completed.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_26

LANGUAGE: python
CODE:
```
from openai import OpenAI

with OpenAI() as client:
  # make requests here
  ...

# HTTP client is now closed
```

----------------------------------------

TITLE: Create a Vector Store (Python)
DESCRIPTION: Method signature for creating a Vector Store using the OpenAI Python client. It takes parameters and returns a VectorStore object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_57

LANGUAGE: python
CODE:
```
client.vector_stores.create(**params) -> VectorStore
```

----------------------------------------

TITLE: Polling Helpers in OpenAI Python SDK
DESCRIPTION: This section lists polling helper methods available in the SDK for handling asynchronous actions like starting a Run or adding files to vector stores. These methods poll the status until it reaches a terminal state and return the resulting object.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_9

LANGUAGE: python
CODE:
```
client.beta.threads.create_and_run_poll(...)
client.beta.threads.runs.create_and_poll(...)
client.beta.threads.runs.submit_tool_outputs_and_poll(...)
client.beta.vector_stores.files.upload_and_poll(...)
client.beta.vector_stores.files.create_and_poll(...)
client.beta.vector_stores.file_batches.create_and_poll(...)
client.beta.vector_stores.file_batches.upload_and_poll(...)
```

----------------------------------------

TITLE: Streaming responses with AsyncOpenAI
DESCRIPTION: Example of streaming responses using the asynchronous client. It demonstrates how to create an async stream and process events in an asynchronous context.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_7

LANGUAGE: python
CODE:
```
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI()


async def main():
    stream = client.responses.create(
        model="gpt-4o",
        input="Write a one-sentence bedtime story about a unicorn.",
        stream=True,
    )

    for event in stream:
        print(event)


asyncio.run(main())
```

----------------------------------------

TITLE: Retrieve a Vector Store (Python)
DESCRIPTION: Method signature for retrieving a specific Vector Store by its ID using the OpenAI Python client. It returns a VectorStore object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_58

LANGUAGE: python
CODE:
```
client.vector_stores.retrieve(vector_store_id) -> VectorStore
```

----------------------------------------

TITLE: Working directly with paginated data in OpenAI API
DESCRIPTION: Example of working directly with paginated data in the OpenAI API. It shows how to access the cursor for the next page and iterate through the current page's data items.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_13

LANGUAGE: python
CODE:
```
first_page = await client.fine_tuning.jobs.list(
    limit=20,
)

print(f"next page cursor: {first_page.after}")  # => "next page cursor: ..."
for job in first_page.data:
    print(job.id)

# Remove `await` for non-async usage.
```

----------------------------------------

TITLE: Assistant Events in OpenAI Python SDK
DESCRIPTION: This section lists various event handlers available in the Assistant API, including general events, run step events, message events, text events, image file events, tool call events, and special events like stream end, timeout, and exceptions.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_7

LANGUAGE: python
CODE:
```
def on_event(self, event: AssistantStreamEvent)
```

LANGUAGE: python
CODE:
```
def on_run_step_created(self, run_step: RunStep)
def on_run_step_delta(self, delta: RunStepDelta, snapshot: RunStep)
def on_run_step_done(self, run_step: RunStep)
```

LANGUAGE: python
CODE:
```
def on_message_created(self, message: Message)
def on_message_delta(self, delta: MessageDelta, snapshot: Message)
def on_message_done(self, message: Message)
```

LANGUAGE: python
CODE:
```
def on_text_created(self, text: Text)
def on_text_delta(self, delta: TextDelta, snapshot: Text)
def on_text_done(self, text: Text)
```

LANGUAGE: python
CODE:
```
def on_image_file_done(self, image_file: ImageFile)
```

LANGUAGE: python
CODE:
```
def on_tool_call_created(self, tool_call: ToolCall)
def on_tool_call_delta(self, delta: ToolCallDelta, snapshot: ToolCall)
def on_tool_call_done(self, tool_call: ToolCall)
```

LANGUAGE: python
CODE:
```
def on_end(self)
```

LANGUAGE: python
CODE:
```
def on_timeout(self)
```

LANGUAGE: python
CODE:
```
def on_exception(self, exception: Exception)
```

----------------------------------------

TITLE: Streaming Responses in OpenAI Python SDK
DESCRIPTION: Shows how to stream response data using the with_streaming_response method in a context manager to efficiently process large responses.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_22

LANGUAGE: python
CODE:
```
with client.chat.completions.with_streaming_response.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="gpt-4o",
) as response:
    print(response.headers.get("X-My-Header"))

    for line in response.iter_lines():
        print(line)
```

----------------------------------------

TITLE: Assistant Methods in OpenAI Python SDK
DESCRIPTION: This section lists convenience methods provided by the assistant streaming object, including methods to access current context and methods to get final run information.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_8

LANGUAGE: python
CODE:
```
def current_event() -> AssistantStreamEvent | None
def current_run() -> Run | None
def current_message_snapshot() -> Message | None
def current_run_step_snapshot() -> RunStep | None
```

LANGUAGE: python
CODE:
```
def get_final_run(self) -> Run
def get_final_run_steps(self) -> List[RunStep]
def get_final_messages(self) -> List[Message]
```

----------------------------------------

TITLE: Uploading Vector Store File (Python)
DESCRIPTION: Shows the method for uploading a file to a vector store.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_72

LANGUAGE: python
CODE:
```
client.vector_stores.files.upload(*args) -> VectorStoreFile
```

----------------------------------------

TITLE: Processing images with Vision API using URL
DESCRIPTION: Example of using the Vision capabilities to analyze an image from a URL. The code sends both text prompt and image URL to the model to get a description of the image content.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_3

LANGUAGE: python
CODE:
```
prompt = "What is in this image?"
img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/2023_06_08_Raccoon1.jpg/1599px-2023_06_08_Raccoon1.jpg"

response = client.responses.create(
    model="gpt-4o-mini",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"{img_url}"},
            ],
        }
    ],
)
```

----------------------------------------

TITLE: Listing Vector Store Files (Python)
DESCRIPTION: Provides the method call to list files associated with a specific vector store, allowing for pagination and filtering via parameters.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_67

LANGUAGE: python
CODE:
```
client.vector_stores.files.list(vector_store_id, **params) -> SyncCursorPage[VectorStoreFile]
```

----------------------------------------

TITLE: Uploading and Polling Vector Store File (Python)
DESCRIPTION: Provides a convenience method to upload a file and automatically poll its status until processing is complete.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_73

LANGUAGE: python
CODE:
```
client.vector_stores.files.upload_and_poll(*args) -> VectorStoreFile
```

----------------------------------------

TITLE: Iterating Over Text Deltas in OpenAI Assistant API Stream
DESCRIPTION: This snippet demonstrates how to iterate specifically over text deltas received from an Assistant run stream.
SOURCE: https://github.com/openai/openai-python/blob/main/helpers.md#2025-04-23_snippet_5

LANGUAGE: python
CODE:
```
with client.beta.threads.runs.stream(
  thread_id=thread.id,
  assistant_id=assistant.id
) as stream:
    for text in stream.text_deltas:
        print(text)
```

----------------------------------------

TITLE: Creating and Polling Vector Store File (Python)
DESCRIPTION: Shows a convenience method to create a file and automatically poll its status until processing is complete.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_70

LANGUAGE: python
CODE:
```
client.vector_stores.files.create_and_poll(*args) -> VectorStoreFile
```

----------------------------------------

TITLE: Processing images with Vision API using base64 encoding
DESCRIPTION: Example of using the Vision capabilities with a locally stored image. The code reads an image file, converts it to a base64 encoded string, and sends it to the model along with a text prompt.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_4

LANGUAGE: python
CODE:
```
import base64
from openai import OpenAI

client = OpenAI()

prompt = "What is in this image?"
with open("path/to/image.png", "rb") as image_file:
    b64_image = base64.b64encode(image_file.read()).decode("utf-8")

response = client.responses.create(
    model="gpt-4o-mini",
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:image/png;base64,{b64_image}"},
            ],
        }
    ],
)
```

----------------------------------------

TITLE: Retrieving Vector Store File (Python)
DESCRIPTION: Shows the method call to retrieve details of a specific file from a vector store using its file ID and the vector store ID.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_65

LANGUAGE: python
CODE:
```
client.vector_stores.files.retrieve(file_id, *, vector_store_id) -> VectorStoreFile
```

----------------------------------------

TITLE: Polling Vector Store File Status (Python)
DESCRIPTION: Provides the method to poll the status of a vector store file operation until it reaches a terminal state.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_71

LANGUAGE: python
CODE:
```
client.vector_stores.files.poll(*args) -> VectorStoreFile
```

----------------------------------------

TITLE: Creating Vector Store File (Python)
DESCRIPTION: Demonstrates the method call to create a new file within a specific vector store using the OpenAI Python client. Requires the vector store ID and creation parameters.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_64

LANGUAGE: python
CODE:
```
client.vector_stores.files.create(vector_store_id, **params) -> VectorStoreFile
```

----------------------------------------

TITLE: Creating Audio Speech (OpenAI Python)
DESCRIPTION: Synthesizes text into audio speech using the client's audio.speech interface. Requires parameters defining the text, voice, and model. Returns HttpxBinaryResponseContent.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_30

LANGUAGE: python
CODE:
```
client.audio.speech.create(**params) -> HttpxBinaryResponseContent
```

----------------------------------------

TITLE: Retrieving Vector Store File Content (Python)
DESCRIPTION: Demonstrates the method call to retrieve the content of a specific file stored within a vector store using its file ID and the vector store ID.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_69

LANGUAGE: python
CODE:
```
client.vector_stores.files.content(file_id, *, vector_store_id) -> SyncPage[FileContentResponse]
```

----------------------------------------

TITLE: Creating and Polling Vector Store File Batch (Python)
DESCRIPTION: Shows a convenience method to create a file batch and automatically poll its status until processing is complete.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_79

LANGUAGE: python
CODE:
```
client.vector_stores.file_batches.create_and_poll(*args) -> VectorStoreFileBatch
```

----------------------------------------

TITLE: Generating Image (OpenAI Python)
DESCRIPTION: Generates a new image from a text prompt using the client's images interface. Requires parameters defining the prompt and generation options. Returns an ImagesResponse.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_24

LANGUAGE: python
CODE:
```
client.images.generate(**params) -> ImagesResponse
```

----------------------------------------

TITLE: Detecting Null vs Missing Fields in OpenAI Python SDK
DESCRIPTION: Shows how to differentiate between explicit null values and missing fields in API responses using the model_fields_set property.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_20

LANGUAGE: python
CODE:
```
if response.my_field is None:
  if 'my_field' not in response.model_fields_set:
    print('Got json like {}, without a "my_field" key present at all.')
  else:
    print('Got json like {"my_field": null}.')
```

----------------------------------------

TITLE: Creating Fine-Tuning Job (Python)
DESCRIPTION: Demonstrates the Python client method call to create a new fine-tuning job using the `client.fine_tuning.jobs.create` method, accepting parameters and returning a `FineTuningJob` object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_39

LANGUAGE: python
CODE:
```
client.fine_tuning.jobs.create(**params) -> FineTuningJob
```

----------------------------------------

TITLE: Creating Upload - OpenAI Python
DESCRIPTION: Calls the `create` method on the `client.uploads` object to initiate a file upload. It accepts parameters (`params`) and returns an `Upload` object. Corresponds to the `POST /uploads` API endpoint.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_92

LANGUAGE: python
CODE:
```
client.uploads.create(**params) -> Upload
```

----------------------------------------

TITLE: Creating File (OpenAI Python)
DESCRIPTION: Creates a new file resource on the OpenAI platform using the client's files interface. Requires parameters defining the file content and purpose. Returns a FileObject.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_14

LANGUAGE: python
CODE:
```
client.files.create(**params) -> FileObject
```

----------------------------------------

TITLE: Using the Realtime API for text-based conversations
DESCRIPTION: Example of using the beta Realtime API for text-based conversations. It establishes a WebSocket connection, updates the session to use text modality, and processes events in real-time as they arrive from the server.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_8

LANGUAGE: python
CODE:
```
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI()

    async with client.beta.realtime.connect(model="gpt-4o-realtime-preview") as connection:
        await connection.session.update(session={'modalities': ['text']})

        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Say hello!"}],
            }
        )
        await connection.response.create()

        async for event in connection:
            if event.type == 'response.text.delta':
                print(event.delta, flush=True, end="")

            elif event.type == 'response.text.done':
                print()

            elif event.type == "response.done":
                break

asyncio.run(main())
```

----------------------------------------

TITLE: Retrieving File Content (String) (OpenAI Python)
DESCRIPTION: Retrieves the content of a specific file resource by its ID as a string using the client's files interface. Returns a string.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_19

LANGUAGE: python
CODE:
```
client.files.retrieve_content(file_id) -> str
```

----------------------------------------

TITLE: Uploading and Polling Vector Store File Batch (Python)
DESCRIPTION: Provides a convenience method to upload files in a batch and automatically poll the batch status until processing is complete.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_81

LANGUAGE: python
CODE:
```
client.vector_stores.file_batches.upload_and_poll(*args) -> VectorStoreFileBatch
```

----------------------------------------

TITLE: Listing Files (OpenAI Python)
DESCRIPTION: Lists all file resources available to the client using the files interface. Accepts optional parameters for filtering. Returns a paginated list of FileObject.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_16

LANGUAGE: python
CODE:
```
client.files.list(**params) -> SyncCursorPage[FileObject]
```

----------------------------------------

TITLE: Listing Models (OpenAI Python)
DESCRIPTION: Lists all models available to the client using the models interface. Returns a paginated list of Model objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_35

LANGUAGE: python
CODE:
```
client.models.list() -> SyncPage[Model]
```

----------------------------------------

TITLE: Retrieving File (OpenAI Python)
DESCRIPTION: Retrieves a specific file resource by its ID using the client's files interface. Returns a FileObject.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_15

LANGUAGE: python
CODE:
```
client.files.retrieve(file_id) -> FileObject
```

----------------------------------------

TITLE: Deleting Vector Store File (Python)
DESCRIPTION: Shows the method call to delete a specific file from a vector store using its file ID and the vector store ID.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_68

LANGUAGE: python
CODE:
```
client.vector_stores.files.delete(file_id, *, vector_store_id) -> VectorStoreFileDeleted
```

----------------------------------------

TITLE: Manual pagination control with the OpenAI API
DESCRIPTION: Example of manual pagination control with the OpenAI API. It demonstrates how to check if more pages exist, get information about the next page, and fetch the next page explicitly.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_12

LANGUAGE: python
CODE:
```
first_page = await client.fine_tuning.jobs.list(
    limit=20,
)
if first_page.has_next_page():
    print(f"will fetch next page using these details: {first_page.next_page_info()}")
    next_page = await first_page.get_next_page()
    print(f"number of items we just fetched: {len(next_page.data)}")

# Remove `await` for non-async usage.
```

----------------------------------------

TITLE: Delete a Vector Store (Python)
DESCRIPTION: Method signature for deleting a specific Vector Store by its ID using the OpenAI Python client. It returns a VectorStoreDeleted object indicating the deletion status.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_61

LANGUAGE: python
CODE:
```
client.vector_stores.delete(vector_store_id) -> VectorStoreDeleted
```

----------------------------------------

TITLE: Update a Vector Store (Python)
DESCRIPTION: Method signature for updating a specific Vector Store by its ID using the OpenAI Python client. It takes parameters for the update and returns the updated VectorStore object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_59

LANGUAGE: python
CODE:
```
client.vector_stores.update(vector_store_id, **params) -> VectorStore
```

----------------------------------------

TITLE: Deleting File (OpenAI Python)
DESCRIPTION: Deletes a specific file resource by its ID using the client's files interface. Returns a FileDeleted object indicating success.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_17

LANGUAGE: python
CODE:
```
client.files.delete(file_id) -> FileDeleted
```

----------------------------------------

TITLE: List Vector Stores (Python)
DESCRIPTION: Method signature for listing Vector Stores using the OpenAI Python client. It takes optional parameters for filtering/pagination and returns a SyncCursorPage containing VectorStore objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_60

LANGUAGE: python
CODE:
```
client.vector_stores.list(**params) -> SyncCursorPage[VectorStore]
```

----------------------------------------

TITLE: Completing Upload - OpenAI Python
DESCRIPTION: Calls the `complete` method on the `client.uploads` object to finalize a specific file upload identified by `upload_id`. It accepts additional parameters (`params`) and returns the completed `Upload` object. Corresponds to the `POST /uploads/{upload_id}/complete` API endpoint.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_94

LANGUAGE: python
CODE:
```
client.uploads.complete(upload_id, **params) -> Upload
```

----------------------------------------

TITLE: Accessing Raw Response Data in OpenAI Python SDK
DESCRIPTION: Demonstrates how to access raw HTTP response data including headers by using the with_raw_response method prefix.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_21

LANGUAGE: python
CODE:
```
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.with_raw_response.create(
    messages=[{
        "role": "user",
        "content": "Say this is a test",
    }],
    model="gpt-4o",
)
print(response.headers.get('X-My-Header'))

completion = response.parse()  # get the object that `chat.completions.create()` would have returned
print(completion)
```

----------------------------------------

TITLE: Retrieving Vector Store File Batch (Python)
DESCRIPTION: Shows the method call to retrieve details of a specific file batch from a vector store using its batch ID and the vector store ID.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_76

LANGUAGE: python
CODE:
```
client.vector_stores.file_batches.retrieve(batch_id, *, vector_store_id) -> VectorStoreFileBatch
```

----------------------------------------

TITLE: Polling Vector Store File Batch Status (Python)
DESCRIPTION: Provides the method to poll the status of a vector store file batch operation until it reaches a terminal state.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_80

LANGUAGE: python
CODE:
```
client.vector_stores.file_batches.poll(*args) -> VectorStoreFileBatch
```

----------------------------------------

TITLE: Listing Files in Vector Store Batch (Python)
DESCRIPTION: Provides the method call to list files associated with a specific vector store file batch, allowing for pagination and filtering via parameters.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_78

LANGUAGE: python
CODE:
```
client.vector_stores.file_batches.list_files(batch_id, *, vector_store_id, **params) -> SyncCursorPage[VectorStoreFile]
```

----------------------------------------

TITLE: Customizing OpenAI HTTP Client on a Per-Request Basis
DESCRIPTION: Demonstrates how to customize the OpenAI client's HTTP settings for a specific request using the with_options() method, allowing for temporary configuration changes without modifying the base client.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_25

LANGUAGE: python
CODE:
```
client.with_options(http_client=DefaultHttpxClient(...))
```

----------------------------------------

TITLE: Cancelling Vector Store File Batch (Python)
DESCRIPTION: Illustrates the method call to cancel a file batch operation within a vector store using its batch ID and the vector store ID.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_77

LANGUAGE: python
CODE:
```
client.vector_stores.file_batches.cancel(batch_id, *, vector_store_id) -> VectorStoreFileBatch
```

----------------------------------------

TITLE: Using Nested Parameters with OpenAI Python SDK
DESCRIPTION: Demonstrates how to use nested dictionary parameters with TypedDict in the OpenAI Python SDK to create a chat response with JSON formatting.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_14

LANGUAGE: python
CODE:
```
from openai import OpenAI

client = OpenAI()

response = client.chat.responses.create(
    input=[
        {
            "role": "user",
            "content": "How much ?",
        }
    ],
    model="gpt-4o",
    response_format={"type": "json_object"},
)
```

----------------------------------------

TITLE: Handling errors in the Realtime API
DESCRIPTION: Example of error handling with the Realtime API. It shows how to check for error events in the connection stream and extract error details such as type, code, event ID, and message.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_9

LANGUAGE: python
CODE:
```
client = AsyncOpenAI()

async with client.beta.realtime.connect(model="gpt-4o-realtime-preview") as connection:
    ...
    async for event in connection:
        if event.type == 'error':
            print(event.error.type)
            print(event.error.code)
            print(event.error.event_id)
            print(event.error.message)
```

----------------------------------------

TITLE: Importing Audio Speech Types (OpenAI Python)
DESCRIPTION: Imports specific type definitions related to audio speech synthesis from the openai.types.audio module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_29

LANGUAGE: python
CODE:
```
from openai.types.audio import SpeechModel
```

----------------------------------------

TITLE: Configuring HTTP Client with Custom Proxy and Transport in OpenAI Python Client
DESCRIPTION: Shows how to configure the OpenAI client with a custom HTTP client using httpx. This example demonstrates setting a custom base URL, proxy, and transport configuration for specialized networking requirements.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_24

LANGUAGE: python
CODE:
```
import httpx
from openai import OpenAI, DefaultHttpxClient

client = OpenAI(
    # Or use the `OPENAI_BASE_URL` env var
    base_url="http://my.test.server.example.com:8083/v1",
    http_client=DefaultHttpxClient(
        proxy="http://my.test.proxy.example.com",
        transport=httpx.HTTPTransport(local_address="0.0.0.0"),
    ),
)
```

----------------------------------------

TITLE: Cancelling Upload - OpenAI Python
DESCRIPTION: Calls the `cancel` method on the `client.uploads` object to cancel a specific file upload identified by `upload_id`. Returns the updated `Upload` object. Corresponds to the `POST /uploads/{upload_id}/cancel` API endpoint.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_93

LANGUAGE: python
CODE:
```
client.uploads.cancel(upload_id) -> Upload
```

----------------------------------------

TITLE: Importing Message Types from OpenAI Python
DESCRIPTION: Imports various type definitions related to Messages, including annotations (File Citation, File Path), content blocks (Image File, Image URL, Refusal, Text), and message events/deltas, from the `openai.types.beta.threads` module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_89

LANGUAGE: python
CODE:
```
from openai.types.beta.threads import (
    Annotation,
    AnnotationDelta,
    FileCitationAnnotation,
    FileCitationDeltaAnnotation,
    FilePathAnnotation,
    FilePathDeltaAnnotation,
    ImageFile,
    ImageFileContentBlock,
    ImageFileDelta,
    ImageFileDeltaBlock,
    ImageURL,
    ImageURLContentBlock,
    ImageURLDelta,
    ImageURLDeltaBlock,
    Message,
    MessageContent,
    MessageContentDelta,
    MessageContentPartParam,
    MessageDeleted,
    MessageDelta,
    MessageDeltaEvent,
    RefusalContentBlock,
    RefusalDeltaBlock,
    Text,
    TextContentBlock,
    TextContentBlockParam,
    TextDelta,
    TextDeltaBlock,
)
```

----------------------------------------

TITLE: Creating Audio Transcription (OpenAI Python)
DESCRIPTION: Transcribes audio into text using the client's audio.transcriptions interface. Requires parameters defining the audio file and transcription options. Returns a TranscriptionCreateResponse.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_26

LANGUAGE: python
CODE:
```
client.audio.transcriptions.create(**params) -> TranscriptionCreateResponse
```

----------------------------------------

TITLE: Creating Image Variation (OpenAI Python)
DESCRIPTION: Creates a variation of an existing image using the client's images interface. Requires parameters defining the source image and desired variations. Returns an ImagesResponse.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_22

LANGUAGE: python
CODE:
```
client.images.create_variation(**params) -> ImagesResponse
```

----------------------------------------

TITLE: Creating Audio Translation (OpenAI Python)
DESCRIPTION: Translates audio into English text using the client's audio.translations interface. Requires parameters defining the audio file and translation options. Returns a TranslationCreateResponse.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_28

LANGUAGE: python
CODE:
```
client.audio.translations.create(**params) -> TranslationCreateResponse
```

----------------------------------------

TITLE: Import Thread Types - Python
DESCRIPTION: Imports necessary type definitions for working with Thread objects and related options from the OpenAI beta API.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_86

LANGUAGE: python
CODE:
```
from openai.types.beta import (
    AssistantResponseFormatOption,
    AssistantToolChoice,
    AssistantToolChoiceFunction,
    AssistantToolChoiceOption,
    Thread,
    ThreadDeleted,
)
```

----------------------------------------

TITLE: Canceling Fine-Tuning Job (Python)
DESCRIPTION: Shows how to cancel a running fine-tuning job using its ID via the `client.fine_tuning.jobs.cancel` method, which returns the updated `FineTuningJob` object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_42

LANGUAGE: python
CODE:
```
client.fine_tuning.jobs.cancel(fine_tuning_job_id) -> FineTuningJob
```

----------------------------------------

TITLE: Editing Image (OpenAI Python)
DESCRIPTION: Edits an existing image based on a prompt and mask using the client's images interface. Requires parameters defining the source image, prompt, and mask. Returns an ImagesResponse.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_23

LANGUAGE: python
CODE:
```
client.images.edit(**params) -> ImagesResponse
```

----------------------------------------

TITLE: Retrieving Response - OpenAI Python
DESCRIPTION: Calls the `retrieve` method on the `client.responses` object to fetch details of a specific API response identified by `response_id`. It accepts optional parameters (`params`) and returns a `Response` object. Corresponds to the `GET /responses/{response_id}` API endpoint.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_99

LANGUAGE: python
CODE:
```
client.responses.retrieve(response_id, **params) -> Response
```

----------------------------------------

TITLE: Retrieving File Content (Binary) (OpenAI Python)
DESCRIPTION: Retrieves the content of a specific file resource by its ID as binary data using the client's files interface. Returns HttpxBinaryResponseContent.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_18

LANGUAGE: python
CODE:
```
client.files.content(file_id) -> HttpxBinaryResponseContent
```

----------------------------------------

TITLE: Creating Moderation (OpenAI Python)
DESCRIPTION: Classifies if content violates OpenAI's usage policies using the client's moderations interface. Requires parameters defining the input content. Returns a ModerationCreateResponse.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_32

LANGUAGE: python
CODE:
```
client.moderations.create(**params) -> ModerationCreateResponse
```

----------------------------------------

TITLE: Waiting for File Processing (OpenAI Python)
DESCRIPTION: Waits for a file resource to finish processing on the OpenAI platform. Accepts arguments to specify the file and potentially polling options. Returns the processed FileObject.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_20

LANGUAGE: python
CODE:
```
client.files.wait_for_processing(*args) -> FileObject
```

----------------------------------------

TITLE: Listing Fine-Tuning Jobs (Python)
DESCRIPTION: Illustrates listing fine-tuning jobs using the `client.fine_tuning.jobs.list` method, which supports pagination parameters and returns a `SyncCursorPage` of `FineTuningJob` objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_41

LANGUAGE: python
CODE:
```
client.fine_tuning.jobs.list(**params) -> SyncCursorPage[FineTuningJob]
```

----------------------------------------

TITLE: Importing Vector Store File Types (Python)
DESCRIPTION: Imports the necessary type definitions for representing vector store files, deleted files, and file content responses from the OpenAI Python library.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_63

LANGUAGE: python
CODE:
```
from openai.types.vector_stores import VectorStoreFile, VectorStoreFileDeleted, FileContentResponse
```

----------------------------------------

TITLE: Listing Fine-Tuning Job Events (Python)
DESCRIPTION: Demonstrates listing events for a specific fine-tuning job by its ID using the `client.fine_tuning.jobs.list_events` method, supporting pagination and returning a `SyncCursorPage` of `FineTuningJobEvent` objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_43

LANGUAGE: python
CODE:
```
client.fine_tuning.jobs.list_events(fine_tuning_job_id, **params) -> SyncCursorPage[FineTuningJobEvent]
```

----------------------------------------

TITLE: Updating Vector Store File (Python)
DESCRIPTION: Illustrates the method call to update an existing file within a vector store using its file ID, the vector store ID, and update parameters.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_66

LANGUAGE: python
CODE:
```
client.vector_stores.files.update(file_id, *, vector_store_id, **params) -> VectorStoreFile
```

----------------------------------------

TITLE: List Chat Completion Messages (Python)
DESCRIPTION: Lists messages associated with a specific chat completion ID, potentially filtered by parameters. Returns a paginated list of ChatCompletionStoreMessage objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_10

LANGUAGE: python
CODE:
```
client.chat.completions.messages.list(completion_id, **params)
```

----------------------------------------

TITLE: Validate a Grader (Python)
DESCRIPTION: Method signature for validating a Grader using the OpenAI Python client. It takes parameters and returns a GraderValidateResponse object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_56

LANGUAGE: python
CODE:
```
client.fine_tuning.alpha.graders.validate(**params) -> GraderValidateResponse
```

----------------------------------------

TITLE: Retrieving Fine-Tuning Job (Python)
DESCRIPTION: Shows how to retrieve a specific fine-tuning job by its ID using the `client.fine_tuning.jobs.retrieve` method, which returns a `FineTuningJob` object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_40

LANGUAGE: python
CODE:
```
client.fine_tuning.jobs.retrieve(fine_tuning_job_id) -> FineTuningJob
```

----------------------------------------

TITLE: Importing Step Types from OpenAI Python
DESCRIPTION: Imports various type definitions related to Run Steps, including details for different tool calls (Code Interpreter, File Search, Function) and step details (Message Creation, Tool Calls), from the `openai.types.beta.threads.runs` module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_88

LANGUAGE: python
CODE:
```
from openai.types.beta.threads.runs import (
    CodeInterpreterLogs,
    CodeInterpreterOutputImage,
    CodeInterpreterToolCall,
    CodeInterpreterToolCallDelta,
    FileSearchToolCall,
    FileSearchToolCallDelta,
    FunctionToolCall,
    FunctionToolCallDelta,
    MessageCreationStepDetails,
    RunStep,
    RunStepDelta,
    RunStepDeltaEvent,
    RunStepDeltaMessageDelta,
    RunStepInclude,
    ToolCall,
    ToolCallDelta,
    ToolCallDeltaObject,
    ToolCallsStepDetails,
)
```

----------------------------------------

TITLE: Resuming Fine-Tuning Job (Python)
DESCRIPTION: Shows how to resume a paused fine-tuning job using its ID via the `client.fine_tuning.jobs.resume` method, which returns the updated `FineTuningJob` object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_45

LANGUAGE: python
CODE:
```
client.fine_tuning.jobs.resume(fine_tuning_job_id) -> FineTuningJob
```

----------------------------------------

TITLE: Pausing Fine-Tuning Job (Python)
DESCRIPTION: Shows how to pause a fine-tuning job using its ID via the `client.fine_tuning.jobs.pause` method, which returns the updated `FineTuningJob` object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_44

LANGUAGE: python
CODE:
```
client.fine_tuning.jobs.pause(fine_tuning_job_id) -> FineTuningJob
```

----------------------------------------

TITLE: Importing Fine-Tuning Method Types (Python)
DESCRIPTION: Imports various type definitions for different fine-tuning methods (DPO, Reinforcement, Supervised) used in the OpenAI Python library.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_37

LANGUAGE: python
CODE:
```
from openai.types.fine_tuning import (
    DpoHyperparameters,
    DpoMethod,
    ReinforcementHyperparameters,
    ReinforcementMethod,
    SupervisedHyperparameters,
    SupervisedMethod,
)
```

----------------------------------------

TITLE: Listing Fine-Tuning Job Checkpoints (Python)
DESCRIPTION: Demonstrates listing checkpoints for a specific fine-tuning job by its ID using the `client.fine_tuning.jobs.checkpoints.list` method, supporting pagination and returning a `SyncCursorPage` of `FineTuningJobCheckpoint` objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_47

LANGUAGE: python
CODE:
```
client.fine_tuning.jobs.checkpoints.list(fine_tuning_job_id, **params) -> SyncCursorPage[FineTuningJobCheckpoint]
```

----------------------------------------

TITLE: Creating Upload Part - OpenAI Python
DESCRIPTION: Calls the `create` method on the `client.uploads.parts` object to create a part for a specific file upload identified by `upload_id`. It accepts parameters (`params`) and returns an `UploadPart` object. Corresponds to the `POST /uploads/{upload_id}/parts` API endpoint.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_96

LANGUAGE: python
CODE:
```
client.uploads.parts.create(upload_id, **params) -> UploadPart
```

----------------------------------------

TITLE: Retrieve Chat Completion (Python)
DESCRIPTION: Retrieves a specific chat completion by its ID. Returns a ChatCompletion object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_6

LANGUAGE: python
CODE:
```
client.chat.completions.retrieve(completion_id)
```

----------------------------------------

TITLE: Import Vector Store and Chunking Types (Python)
DESCRIPTION: Imports type definitions related to Vector Stores, file chunking strategies, and associated response objects from the OpenAI Python library.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_54

LANGUAGE: python
CODE:
```
from openai.types import (
    AutoFileChunkingStrategyParam,
    FileChunkingStrategy,
    FileChunkingStrategyParam,
    OtherFileChunkingStrategyObject,
    StaticFileChunkingStrategy,
    StaticFileChunkingStrategyObject,
    StaticFileChunkingStrategyObjectParam,
    VectorStore,
    VectorStoreDeleted,
    VectorStoreSearchResponse,
)
```

----------------------------------------

TITLE: Importing Upload Type - OpenAI Python
DESCRIPTION: Imports the `Upload` type from the `openai.types` module, used for representing file upload objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_91

LANGUAGE: python
CODE:
```
from openai.types import Upload
```

----------------------------------------

TITLE: Run a Grader (Python)
DESCRIPTION: Method signature for running a Grader using the OpenAI Python client. It takes parameters and returns a GraderRunResponse object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_55

LANGUAGE: python
CODE:
```
client.fine_tuning.alpha.graders.run(**params) -> GraderRunResponse
```

----------------------------------------

TITLE: Retrieving Model (OpenAI Python)
DESCRIPTION: Retrieves information about a specific model by its ID using the client's models interface. Returns a Model object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_34

LANGUAGE: python
CODE:
```
client.models.retrieve(model) -> Model
```

----------------------------------------

TITLE: Importing Fine-Tuning Job Types (Python)
DESCRIPTION: Imports various type definitions related to fine-tuning jobs, including the job object, events, and W&B integration types.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_38

LANGUAGE: python
CODE:
```
from openai.types.fine_tuning import (
    FineTuningJob,
    FineTuningJobEvent,
    FineTuningJobWandbIntegration,
    FineTuningJobWandbIntegrationObject,
    FineTuningJobIntegration,
)
```

----------------------------------------

TITLE: Importing Realtime Types in Python
DESCRIPTION: Imports various type definitions related to the OpenAI Beta Realtime API, including events for conversations, items, audio processing, and responses.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_82

LANGUAGE: python
CODE:
```
from openai.types.beta.realtime import (
    ConversationCreatedEvent,
    ConversationItem,
    ConversationItemContent,
    ConversationItemCreateEvent,
    ConversationItemCreatedEvent,
    ConversationItemDeleteEvent,
    ConversationItemDeletedEvent,
    ConversationItemInputAudioTranscriptionCompletedEvent,
    ConversationItemInputAudioTranscriptionDeltaEvent,
    ConversationItemInputAudioTranscriptionFailedEvent,
    ConversationItemRetrieveEvent,
    ConversationItemTruncateEvent,
    ConversationItemTruncatedEvent,
    ConversationItemWithReference,
    ErrorEvent,
    InputAudioBufferAppendEvent,
    InputAudioBufferClearEvent,
    InputAudioBufferClearedEvent,
    InputAudioBufferCommitEvent,
    InputAudioBufferCommittedEvent,
    InputAudioBufferSpeechStartedEvent,
    InputAudioBufferSpeechStoppedEvent,
    RateLimitsUpdatedEvent,
    RealtimeClientEvent,
    RealtimeResponse,
    RealtimeResponseStatus,
    RealtimeResponseUsage,
    RealtimeServerEvent,
    ResponseAudioDeltaEvent,
    ResponseAudioDoneEvent,
    ResponseAudioTranscriptDeltaEvent,
    ResponseAudioTranscriptDoneEvent,
    ResponseCancelEvent,
    ResponseContentPartAddedEvent,
    ResponseContentPartDoneEvent,
    ResponseCreateEvent,
    ResponseCreatedEvent,
    ResponseDoneEvent,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
    SessionCreatedEvent,
    SessionUpdateEvent,
    SessionUpdatedEvent,
    TranscriptionSessionUpdate,
    TranscriptionSessionUpdatedEvent,
)
```

----------------------------------------

TITLE: Importing Realtime Session Types in Python
DESCRIPTION: Imports specific type definitions for Realtime Sessions, including the Session object and the response type for session creation.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_83

LANGUAGE: python
CODE:
```
from openai.types.beta.realtime import Session, SessionCreateResponse
```

----------------------------------------

TITLE: Import Chat Completions Types (Python)
DESCRIPTION: Imports numerous type definitions specific to the Chat Completions API, covering messages, content parts, tools, roles, and response structures.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_4

LANGUAGE: python
CODE:
```
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionAudio,
    ChatCompletionAudioParam,
    ChatCompletionChunk,
    ChatCompletionContentPart,
    ChatCompletionContentPartImage,
    ChatCompletionContentPartInputAudio,
    ChatCompletionContentPartRefusal,
    ChatCompletionContentPartText,
    ChatCompletionDeleted,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionFunctionCallOption,
    ChatCompletionFunctionMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionModality,
    ChatCompletionNamedToolChoice,
    ChatCompletionPredictionContent,
    ChatCompletionRole,
    ChatCompletionStoreMessage,
    ChatCompletionStreamOptions,
    ChatCompletionSystemMessageParam,
    ChatCompletionTokenLogprob,
    ChatCompletionTool,
    ChatCompletionToolChoiceOption,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionReasoningEffort,
)
```

----------------------------------------

TITLE: Importing Beta Assistant Types in Python
DESCRIPTION: Imports various type definitions related to the OpenAI Beta Assistants API, including types for Assistants, deleted assistants, stream events, and tools.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_85

LANGUAGE: python
CODE:
```
from openai.types.beta import (
    Assistant,
    AssistantDeleted,
    AssistantStreamEvent,
    AssistantTool,
    CodeInterpreterTool,
    FileSearchTool,
    FunctionTool,
    MessageStreamEvent,
    RunStepStreamEvent,
    RunStreamEvent,
    ThreadStreamEvent,
)
```

----------------------------------------

TITLE: Retrieving Fine-Tuning Checkpoint Permissions (Python)
DESCRIPTION: Demonstrates retrieving permissions for a fine-tuning checkpoint by its ID using the `client.fine_tuning.checkpoints.permissions.retrieve` method, accepting parameters and returning a `PermissionRetrieveResponse` object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_50

LANGUAGE: python
CODE:
```
client.fine_tuning.checkpoints.permissions.retrieve(fine_tuned_model_checkpoint, **params) -> PermissionRetrieveResponse
```

----------------------------------------

TITLE: Making Custom API Requests in OpenAI Python SDK
DESCRIPTION: Demonstrates how to make requests to undocumented endpoints using HTTP verbs directly and how to send extra parameters that might not be covered in the SDK's typed interface.
SOURCE: https://github.com/openai/openai-python/blob/main/README.md#2025-04-23_snippet_23

LANGUAGE: python
CODE:
```
import httpx

response = client.post(
    "/foo",
    cast_to=httpx.Response,
    body={"my_param": True},
)

print(response.headers.get("x-foo"))
```

----------------------------------------

TITLE: Creating Fine-Tuning Checkpoint Permissions (Python)
DESCRIPTION: Shows how to create permissions for a fine-tuning checkpoint using its ID via the `client.fine_tuning.checkpoints.permissions.create` method, accepting parameters and returning a `SyncPage` of `PermissionCreateResponse` objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_49

LANGUAGE: python
CODE:
```
client.fine_tuning.checkpoints.permissions.create(fine_tuned_model_checkpoint, **params) -> SyncPage[PermissionCreateResponse]
```

----------------------------------------

TITLE: Deleting Fine-Tuning Checkpoint Permissions (Python)
DESCRIPTION: Shows how to delete a specific permission for a fine-tuning checkpoint using its ID and the checkpoint ID via the `client.fine_tuning.checkpoints.permissions.delete` method, returning a `PermissionDeleteResponse` object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_51

LANGUAGE: python
CODE:
```
client.fine_tuning.checkpoints.permissions.delete(permission_id, *, fine_tuned_model_checkpoint) -> PermissionDeleteResponse
```

----------------------------------------

TITLE: Import Embeddings Types (Python)
DESCRIPTION: Imports type definitions specific to the Embeddings API, including the response structure, individual embedding objects, and model types.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_11

LANGUAGE: python
CODE:
```
from openai.types import CreateEmbeddingResponse, Embedding, EmbeddingModel
```

----------------------------------------

TITLE: Importing File Types (OpenAI Python)
DESCRIPTION: Imports specific type definitions related to file objects and operations from the openai.types module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_13

LANGUAGE: python
CODE:
```
from openai.types import FileContent, FileDeleted, FileObject, FilePurpose
```

----------------------------------------

TITLE: Importing Vector Store File Batch Type (Python)
DESCRIPTION: Imports the necessary type definition for representing vector store file batches from the OpenAI Python library.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_74

LANGUAGE: python
CODE:
```
from openai.types.vector_stores import VectorStoreFileBatch
```

----------------------------------------

TITLE: Listing Response Input Items - OpenAI Python
DESCRIPTION: Calls the `list` method on the `client.responses.input_items` object to retrieve a paginated list of input items associated with a specific response identified by `response_id`. It accepts parameters (`params`) and returns a `SyncCursorPage` containing `ResponseItem` objects. Corresponds to the `GET /responses/{response_id}/input_items` API endpoint.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_102

LANGUAGE: python
CODE:
```
client.responses.input_items.list(response_id, **params) -> SyncCursorPage[ResponseItem]
```

----------------------------------------

TITLE: Importing Evals Runs Types - Python
DESCRIPTION: Imports type definitions specific to the OpenAI Evals Runs API resource, covering data source configurations for creating runs, API error types, and response types for run operations like create, retrieve, list, delete, and cancel.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_104

LANGUAGE: python
CODE:
```
from openai.types.evals import (
    CreateEvalCompletionsRunDataSource,
    CreateEvalJSONLRunDataSource,
    EvalAPIError,
    RunCreateResponse,
    RunRetrieveResponse,
    RunListResponse,
    RunDeleteResponse,
    RunCancelResponse,
)
```

----------------------------------------

TITLE: Deleting Model (OpenAI Python)
DESCRIPTION: Deletes a fine-tuned model by its ID using the client's models interface. Returns a ModelDeleted object indicating success.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_36

LANGUAGE: python
CODE:
```
client.models.delete(model) -> ModelDeleted
```

----------------------------------------

TITLE: Importing Audio Transcription Types (OpenAI Python)
DESCRIPTION: Imports specific type definitions related to audio transcriptions from the openai.types.audio module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_25

LANGUAGE: python
CODE:
```
from openai.types.audio import (
    Transcription,
    TranscriptionInclude,
    TranscriptionSegment,
    TranscriptionStreamEvent,
    TranscriptionTextDeltaEvent,
    TranscriptionTextDoneEvent,
    TranscriptionVerbose,
    TranscriptionWord,
    TranscriptionCreateResponse,
)
```

----------------------------------------

TITLE: Importing Fine-Tuning Job Checkpoint Type (Python)
DESCRIPTION: Imports the `FineTuningJobCheckpoint` type definition specifically for fine-tuning job checkpoints.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_46

LANGUAGE: python
CODE:
```
from openai.types.fine_tuning.jobs import FineTuningJobCheckpoint
```

----------------------------------------

TITLE: Importing Audio Translation Types (OpenAI Python)
DESCRIPTION: Imports specific type definitions related to audio translations from the openai.types.audio module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_27

LANGUAGE: python
CODE:
```
from openai.types.audio import Translation, TranslationVerbose, TranslationCreateResponse
```

----------------------------------------

TITLE: Importing Evals Types - Python
DESCRIPTION: Imports the necessary type definitions for interacting with the OpenAI Evals API resource, including configurations for data sources and response types for various operations like create, retrieve, update, list, and delete.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_103

LANGUAGE: python
CODE:
```
from openai.types import (
    EvalCustomDataSourceConfig,
    EvalStoredCompletionsDataSourceConfig,
    EvalCreateResponse,
    EvalRetrieveResponse,
    EvalUpdateResponse,
    EvalListResponse,
    EvalDeleteResponse,
)
```

----------------------------------------

TITLE: Importing Batch Types from OpenAI Python
DESCRIPTION: Imports core type definitions for Batches, including `Batch`, `BatchError`, and `BatchRequestCounts`, from the top-level `openai.types` module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_90

LANGUAGE: python
CODE:
```
from openai.types import Batch, BatchError, BatchRequestCounts
```

----------------------------------------

TITLE: Importing UploadPart Type - OpenAI Python
DESCRIPTION: Imports the `UploadPart` type from the `openai.types.uploads` module, used for representing parts of a file upload.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_95

LANGUAGE: python
CODE:
```
from openai.types.uploads import UploadPart
```

----------------------------------------

TITLE: Importing Evals Runs OutputItems Types - Python
DESCRIPTION: Imports type definitions for the output items within OpenAI Evals Runs, specifically for retrieving a single output item or listing multiple output items.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_105

LANGUAGE: python
CODE:
```
from openai.types.evals.runs import OutputItemRetrieveResponse, OutputItemListResponse
```

----------------------------------------

TITLE: Import Grader Model Types (Python)
DESCRIPTION: Imports various type definitions representing different Grader models available in the OpenAI Python library.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_53

LANGUAGE: python
CODE:
```
from openai.types.graders import (
    LabelModelGrader,
    MultiGrader,
    PythonGrader,
    ScoreModelGrader,
    StringCheckGrader,
    TextSimilarityGrader,
)
```

----------------------------------------

TITLE: Delete Chat Completion (Python)
DESCRIPTION: Deletes a specific chat completion by its ID. Returns a ChatCompletionDeleted object indicating success.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_9

LANGUAGE: python
CODE:
```
client.chat.completions.delete(completion_id)
```

----------------------------------------

TITLE: Create Completion (Python)
DESCRIPTION: Calls the OpenAI Completions API to generate text based on provided parameters. Returns a Completion object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_2

LANGUAGE: python
CODE:
```
client.completions.create(**params)
```

----------------------------------------

TITLE: Import Completions Types (Python)
DESCRIPTION: Imports type definitions specific to the Completions API, including the main Completion object, individual choices, and usage statistics.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_1

LANGUAGE: python
CODE:
```
from openai.types import Completion, CompletionChoice, CompletionUsage
```

----------------------------------------

TITLE: Building OpenAI Python SDK from Source
DESCRIPTION: Builds distribution packages (.tar.gz and .whl) for the OpenAI Python SDK. This command uses Rye or Python's build module to create installable packages.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_7

LANGUAGE: sh
CODE:
```
$ rye build
# or
$ python -m build
```

----------------------------------------

TITLE: Deleting Response - OpenAI Python
DESCRIPTION: Calls the `delete` method on the `client.responses` object to remove a specific API response identified by `response_id`. Returns `None` upon successful deletion. Corresponds to the `DELETE /responses/{response_id}` API endpoint.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_100

LANGUAGE: python
CODE:
```
client.responses.delete(response_id) -> None
```

----------------------------------------

TITLE: Installing SDK from Git Repository
DESCRIPTION: Installs the OpenAI Python SDK directly from the Git repository using pip. This is useful for accessing the latest unreleased changes.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_6

LANGUAGE: sh
CODE:
```
$ pip install git+ssh://git@github.com/openai/openai-python.git
```

----------------------------------------

TITLE: Creating Vector Store File Batch (Python)
DESCRIPTION: Demonstrates the method call to create a new batch of files within a specific vector store using the OpenAI Python client. Requires the vector store ID and batch creation parameters.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_75

LANGUAGE: python
CODE:
```
client.vector_stores.file_batches.create(vector_store_id, **params) -> VectorStoreFileBatch
```

----------------------------------------

TITLE: Installing OpenAI Python SDK from Wheel File
DESCRIPTION: Installs the OpenAI Python SDK from a locally built wheel file. This is useful for testing local changes before publishing.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_8

LANGUAGE: sh
CODE:
```
$ pip install ./path-to-wheel-file.whl
```

----------------------------------------

TITLE: Import Shared OpenAI Types (Python)
DESCRIPTION: Imports common type definitions used across various OpenAI API functionalities, such as models, filters, errors, functions, metadata, and response formats.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_0

LANGUAGE: python
CODE:
```
from openai.types import (
    AllModels,
    ChatModel,
    ComparisonFilter,
    CompoundFilter,
    ErrorObject,
    FunctionDefinition,
    FunctionParameters,
    Metadata,
    Reasoning,
    ReasoningEffort,
    ResponseFormatJSONObject,
    ResponseFormatJSONSchema,
    ResponseFormatText,
    ResponsesModel,
)
```

----------------------------------------

TITLE: Running Example Scripts in OpenAI Python SDK
DESCRIPTION: Commands to make examples executable and run them against your API. This requires first setting the file as executable using chmod.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_5

LANGUAGE: sh
CODE:
```
$ chmod +x examples/<your-example>.py
# run the example against your api
$ ./examples/<your-example>.py
```

----------------------------------------

TITLE: Import Run Types - Python
DESCRIPTION: Imports necessary type definitions for working with Run objects and related components within Threads from the OpenAI beta API.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_87

LANGUAGE: python
CODE:
```
from openai.types.beta.threads import RequiredActionFunctionToolCall, Run, RunStatus
```

----------------------------------------

TITLE: Importing Realtime Transcription Session Type in Python
DESCRIPTION: Imports the type definition for Realtime Transcription Sessions from the OpenAI Beta Realtime API.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_84

LANGUAGE: python
CODE:
```
from openai.types.beta.realtime import TranscriptionSession
```

----------------------------------------

TITLE: Importing Response Types - OpenAI Python
DESCRIPTION: Imports various types related to API responses from the `openai.types.responses` module, including the main `Response` type and numerous event and tool-related types.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_97

LANGUAGE: python
CODE:
```
from openai.types.responses import (
    ComputerTool,
    EasyInputMessage,
    FileSearchTool,
    FunctionTool,
    Response,
    ResponseAudioDeltaEvent,
    ResponseAudioDoneEvent,
    ResponseAudioTranscriptDeltaEvent,
    ResponseAudioTranscriptDoneEvent,
    ResponseCodeInterpreterCallCodeDeltaEvent,
    ResponseCodeInterpreterCallCodeDoneEvent,
    ResponseCodeInterpreterCallCompletedEvent,
    ResponseCodeInterpreterCallInProgressEvent,
    ResponseCodeInterpreterCallInterpretingEvent,
    ResponseCodeInterpreterToolCall,
    ResponseCompletedEvent,
    ResponseComputerToolCall,
    ResponseComputerToolCallOutputItem,
    ResponseComputerToolCallOutputScreenshot,
    ResponseContent,
    ResponseContentPartAddedEvent,
    ResponseContentPartDoneEvent,
    ResponseCreatedEvent,
    ResponseError,
    ResponseErrorEvent,
    ResponseFailedEvent,
    ResponseFileSearchCallCompletedEvent,
    ResponseFileSearchCallInProgressEvent,
    ResponseFileSearchCallSearchingEvent,
    ResponseFileSearchToolCall,
    ResponseFormatTextConfig,
    ResponseFormatTextJSONSchemaConfig,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseFunctionToolCall,
    ResponseFunctionToolCallItem,
    ResponseFunctionToolCallOutputItem,
    ResponseFunctionWebSearch,
    ResponseInProgressEvent,
    ResponseIncludable,
    ResponseIncompleteEvent,
    ResponseInput,
    ResponseInputAudio,
    ResponseInputContent,
    ResponseInputFile,
    ResponseInputImage,
    ResponseInputItem,
    ResponseInputMessageContentList,
    ResponseInputMessageItem,
    ResponseInputText,
    ResponseItem,
    ResponseOutputAudio,
    ResponseOutputItem,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseOutputMessage,
    ResponseOutputRefusal,
    ResponseOutputText,
    ResponseReasoningItem,
    ResponseReasoningSummaryPartAddedEvent,
    ResponseReasoningSummaryPartDoneEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseReasoningSummaryTextDoneEvent,
    ResponseRefusalDeltaEvent,
    ResponseRefusalDoneEvent,
    ResponseStatus,
    ResponseStreamEvent,
    ResponseTextAnnotationDeltaEvent,
    ResponseTextConfig,
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
    ResponseUsage,
    ResponseWebSearchCallCompletedEvent,
    ResponseWebSearchCallInProgressEvent,
    ResponseWebSearchCallSearchingEvent,
    Tool,
    ToolChoiceFunction,
    ToolChoiceOptions,
    ToolChoiceTypes,
    WebSearchTool
)
```

----------------------------------------

TITLE: Activating Virtual Environment with Rye in OpenAI Python SDK
DESCRIPTION: Shows how to enter a Rye shell or manually activate the virtual environment. This allows running Python scripts without prefixing commands with 'rye run'.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_2

LANGUAGE: sh
CODE:
```
$ rye shell
# or manually activate - https://docs.python.org/3/library/venv.html#how-venvs-work
$ source .venv/bin/activate

# now you can omit the `rye run` prefix
$ python script.py
```

----------------------------------------

TITLE: Importing Fine-Tuning Checkpoint Permission Types (Python)
DESCRIPTION: Imports type definitions for responses related to creating, retrieving, and deleting permissions for fine-tuning checkpoints.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_48

LANGUAGE: python
CODE:
```
from openai.types.fine_tuning.checkpoints import (
    PermissionCreateResponse,
    PermissionRetrieveResponse,
    PermissionDeleteResponse,
)
```

----------------------------------------

TITLE: Importing Image Types (OpenAI Python)
DESCRIPTION: Imports specific type definitions related to image objects and responses from the openai.types module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_21

LANGUAGE: python
CODE:
```
from openai.types import Image, ImageModel, ImagesResponse
```

----------------------------------------

TITLE: Importing Model Types (OpenAI Python)
DESCRIPTION: Imports specific type definitions related to model objects from the openai.types module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_33

LANGUAGE: python
CODE:
```
from openai.types import Model, ModelDeleted
```

----------------------------------------

TITLE: Importing ResponseItemList Type - OpenAI Python
DESCRIPTION: Imports the `ResponseItemList` type from the `openai.types.responses` module, likely used for representing a list of response items.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_101

LANGUAGE: python
CODE:
```
from openai.types.responses import ResponseItemList
```

----------------------------------------

TITLE: Importing Moderation Types (OpenAI Python)
DESCRIPTION: Imports specific type definitions related to content moderation from the openai.types module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_31

LANGUAGE: python
CODE:
```
from openai.types import (
    Moderation,
    ModerationImageURLInput,
    ModerationModel,
    ModerationMultiModalInput,
    ModerationTextInput,
    ModerationCreateResponse,
)
```

----------------------------------------

TITLE: Linting OpenAI Python SDK Code
DESCRIPTION: Checks the codebase for style issues using ruff and black linters. This helps maintain code quality and consistency.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_11

LANGUAGE: sh
CODE:
```
$ ./scripts/lint
```

----------------------------------------

TITLE: Setting Up Mock Server for OpenAI Python SDK Tests
DESCRIPTION: Runs a Prism mock server against the OpenAPI specification for testing. This is required for most tests to function correctly.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_9

LANGUAGE: sh
CODE:
```
# you will need npm installed
$ npx prism mock path/to/your/openapi.yml
```

----------------------------------------

TITLE: Import Grader Run and Validate Types (Python)
DESCRIPTION: Imports the necessary type definitions for Grader run and validation responses from the OpenAI Python library's fine-tuning alpha module.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_52

LANGUAGE: python
CODE:
```
from openai.types.fine_tuning.alpha import GraderRunResponse, GraderValidateResponse
```

----------------------------------------

TITLE: Installing Dependencies without Rye in OpenAI Python SDK
DESCRIPTION: Installs development dependencies using pip with the requirements lock file. This is for developers who prefer not to use Rye for environment management.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_3

LANGUAGE: sh
CODE:
```
$ pip install -r requirements-dev.lock
```

----------------------------------------

TITLE: Running Tests for OpenAI Python SDK
DESCRIPTION: Executes the test suite for the OpenAI Python SDK. This requires the mock server to be running for most tests.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_10

LANGUAGE: sh
CODE:
```
$ ./scripts/test
```

----------------------------------------

TITLE: Syncing Dependencies with Rye in OpenAI Python SDK
DESCRIPTION: Synchronizes all project dependencies using Rye's sync command with all features enabled. This is an alternative to using the bootstrap script after manually installing Rye.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_1

LANGUAGE: sh
CODE:
```
$ rye sync --all-features
```

----------------------------------------

TITLE: Creating Response - OpenAI Python
DESCRIPTION: Calls the `create` method on the `client.responses` object to initiate a new API response interaction. It accepts parameters (`params`) and returns a `Response` object. Corresponds to the `POST /responses` API endpoint.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_98

LANGUAGE: python
CODE:
```
client.responses.create(**params) -> Response
```

----------------------------------------

TITLE: Update Chat Completion (Python)
DESCRIPTION: Updates a specific chat completion by its ID with new parameters. Returns a ChatCompletion object.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_7

LANGUAGE: python
CODE:
```
client.chat.completions.update(completion_id, **params)
```

----------------------------------------

TITLE: List Chat Completions (Python)
DESCRIPTION: Lists chat completions, potentially filtered by parameters. Returns a paginated list of ChatCompletion objects.
SOURCE: https://github.com/openai/openai-python/blob/main/api.md#_snippet_8

LANGUAGE: python
CODE:
```
client.chat.completions.list(**params)
```

----------------------------------------

TITLE: Running Bootstrap Script for Rye Setup in OpenAI Python SDK
DESCRIPTION: Initializes the development environment using the bootstrap script with Rye. This script automatically sets up a Python environment with the expected version and dependencies.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_0

LANGUAGE: sh
CODE:
```
$ ./scripts/bootstrap
```

----------------------------------------

TITLE: Formatting OpenAI Python SDK Code
DESCRIPTION: Automatically formats the codebase and fixes ruff issues. This ensures consistent code style throughout the project.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_12

LANGUAGE: sh
CODE:
```
$ ./scripts/format
```

----------------------------------------

TITLE: Creating Example Files in OpenAI Python SDK
DESCRIPTION: Template for creating new example Python scripts within the examples directory. The shebang line allows direct execution using Rye run.
SOURCE: https://github.com/openai/openai-python/blob/main/CONTRIBUTING.md#2025-04-23_snippet_4

LANGUAGE: py
CODE:
```
#!/usr/bin/env -S rye run python
…
```
