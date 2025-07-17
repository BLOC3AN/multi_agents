# Multi-Agent System

A clean and simple multi-agent system built with LangGraph that routes user input to specialized agents based on intent classification.

## Features

- **Intent Classification**: Automatically routes input to appropriate agents
- **Specialized Agents**: 
  - Math Agent: Solves mathematical problems
  - English Agent: Explains concepts in English
  - Poem Agent: Creates poetry based on input
- **Multiple LLM Providers**: Support for Gemini and OpenAI
- **Clean Architecture**: Modular design with dependency injection
- **Error Handling**: Comprehensive error handling and logging
- **Configuration Management**: Environment-based configuration

## Architecture

```
src/
├── core/                 # Core functionality
│   ├── types.py         # Shared types and data structures
│   ├── base_agent.py    # Base agent class
│   └── intent_classifier.py  # Intent classification logic
├── agents/              # Specialized agents
│   ├── math_agent.py    # Mathematical problem solving
│   ├── english_agent.py # English explanations
│   └── poem_agent.py    # Poetry creation
├── llms/                # LLM providers
│   ├── llm_factory.py   # LLM factory pattern
│   ├── gemini.py        # Gemini provider
│   └── openai.py        # OpenAI provider
└── config/              # Configuration management
    └── settings.py      # Application settings
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd multi_agents
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Interactive Mode
```bash
python run.py
```

### Single Command
```bash
python run.py "Solve this equation: 2x + 5 = 11"
```

### Programmatic Usage
```python
from graph import create_agent_graph

graph = create_agent_graph()
result = graph.invoke({
    "input": "Write a poem about nature",
    "intent": None,
    "result": None,
    "error": None
})

print(result["result"])
```

## Configuration

The system uses environment variables for configuration:

- `LLM_PROVIDER`: Choose between "gemini" or "openai"
- `LLM_MODEL`: Model name (e.g., "gemini-2.0-flash")
- `LLM_TEMPERATURE`: Temperature for text generation (0.0-1.0)
- `GOOGLE_API_KEY`: Required for Gemini
- `OPENAI_API_KEY`: Required for OpenAI
- `DEBUG`: Enable debug logging

## Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`:
```python
from src.core.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def get_agent_name(self) -> str:
        return "MyAgent"
    
    def get_prompt(self, user_input: str) -> str:
        return f"Process this: {user_input}"
```

2. Add intent keywords to `IntentClassifier`
3. Update the graph routing logic

## Adding New LLM Providers

1. Create a provider class:
```python
class MyLLMProvider:
    def __init__(self, config: LLMConfig):
        self.config = config
    
    def create_llm(self):
        # Return your LLM instance
        pass
```

2. Register in `LLMFactory`:
```python
factory.register_provider("myllm", MyLLMProvider)
```

## Testing

Run tests with:
```bash
python -m pytest tests/
```

## License

Apache License 2.0
