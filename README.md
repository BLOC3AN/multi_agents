# Multi-Agent System with Parallel Execution

A clean and intelligent multi-agent system built with LangGraph that supports both single and parallel agent execution based on multi-intent detection.

## 🚀 Key Features

### 🧠 **Intelligent Intent Detection**
- **LLM-Powered Classification**: Uses AI to detect user intents instead of rule-based matching
- **Multi-Intent Support**: Automatically detects multiple intents in a single input
- **Confidence Scoring**: Each intent comes with confidence scores for better decision making

### ⚡ **Parallel Execution**
- **Automatic Mode Selection**: Switches between single and parallel mode based on detected intents
- **Concurrent Processing**: Runs multiple agents simultaneously using ThreadPoolExecutor
- **Smart Result Aggregation**: LLM intelligently combines results from multiple agents

### 🎯 **Specialized Agents**
- **Math Agent**: Solves mathematical problems and equations
- **English Agent**: Explains concepts, provides definitions, and answers questions
- **Poem Agent**: Creates poetry and creative writing based on input

### 🏗️ **Clean Architecture**
- **Modular Design**: Separation of concerns with clear component boundaries
- **Dependency Injection**: Flexible and testable architecture
- **Factory Patterns**: Easy extensibility for new LLM providers and agents
- **Error Resilience**: Comprehensive error handling and fallback mechanisms

## 🏛️ Architecture

### **Enhanced Parallel Processing Flow**
```
Input → Intent Classification → Mode Selection → Agent Execution → Result Aggregation → Output
         (Multi-Intent AI)      (Single/Parallel)   (Concurrent)      (LLM-Powered)
```

### **Project Structure**
```
src/
├── core/                      # Core functionality
│   ├── types.py              # Enhanced types with multi-intent support
│   ├── base_agent.py         # Base agent class with dependency injection
│   ├── intent_classifier.py  # LLM-powered multi-intent classification
│   ├── parallel_orchestrator.py  # Parallel execution coordinator
│   └── result_aggregator.py  # Intelligent result combination
├── agents/                    # Specialized agents
│   ├── math_agent.py         # Mathematical problem solving
│   ├── english_agent.py      # Concept explanations and Q&A
│   ├── poem_agent.py         # Creative writing and poetry
│   └── context_agent.py      # Legacy compatibility layer
├── llms/                      # LLM provider abstraction
│   ├── llm_factory.py        # Factory pattern for LLM creation
│   ├── gemini.py             # Google Gemini provider
│   └── openai.py             # OpenAI provider
├── config/                    # Configuration management
│   └── settings.py           # Environment-based settings
└── tests/                     # Comprehensive test suite
    ├── test_intent_classifier.py
    └── test_llm_factory.py
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

## 🚀 Usage

### **Interactive Mode**
```bash
python run.py
```
Experience the full interactive chat interface with real-time intent detection and parallel processing.

### **Single Command Mode**
```bash
# Single intent example
python run.py "Solve this equation: 2x + 5 = 11"

# Multi-intent example (triggers parallel mode)
python run.py "Explain machine learning and solve 2x + 5 = 11"
python run.py "Write a poem about AI and calculate 10 + 15"
```

### **Programmatic Usage**
```python
from graph import create_agent_graph, create_initial_state

# Create the enhanced parallel graph
graph = create_agent_graph()

# Single intent processing
result = graph.invoke(create_initial_state("Solve 2x + 3 = 7"))
print(f"Mode: {result['processing_mode']}")  # "single"
print(f"Result: {result['final_result']}")

# Multi-intent processing (automatic parallel mode)
result = graph.invoke(create_initial_state("Explain AI and write a poem about robots"))
print(f"Mode: {result['processing_mode']}")  # "parallel"
print(f"Intents: {[i.intent for i in result['detected_intents']]}")  # ["english", "poem"]
print(f"Result: {result['final_result']}")
```

### **Example Outputs**

**Single Intent:**
```
🎯 Primary Intent: math
🔄 Processing Mode: single
✅ Result: [Mathematical solution...]
```

**Multi-Intent (Parallel):**
```
🎯 Primary Intent: english
🔄 Processing Mode: parallel
🎪 Multiple Intents: english(0.85), math(0.78)
✅ Result: [Combined intelligent response...]
📊 Thông tin xử lý: 🔄 Xử lý song song: 2 agents | ✅ Thành công: 2 | ⏱️ Thời gian: 8.15s
```

## ⚙️ Configuration

### **Environment Variables**
```bash
# LLM Provider Configuration
LLM_PROVIDER=gemini                    # "gemini" or "openai"
LLM_MODEL=gemini-2.0-flash            # Model name
LLM_TEMPERATURE=0.2                   # Temperature for text generation (0.0-1.0)
LLM_TOP_P=0.2                         # Top-p sampling parameter
LLM_TOP_K=40                          # Top-k sampling parameter

# API Keys
GOOGLE_API_KEY=your_google_api_key    # Required for Gemini
OPENAI_API_KEY=your_openai_api_key    # Required for OpenAI

# Application Settings
DEBUG=false                           # Enable debug logging
```

### **Parallel Execution Configuration**
The system automatically configures parallel execution with sensible defaults:
- **Max Concurrent Agents**: 3
- **Timeout**: 30 seconds
- **Confidence Threshold**: 0.3 (minimum confidence to include an intent)
- **Intelligent Aggregation**: Enabled by default

## 🔧 Extending the System

### **Adding New Agents**

1. **Create Agent Class**:
```python
from src.core.base_agent import BaseAgent

class ScienceAgent(BaseAgent):
    def get_agent_name(self) -> str:
        return "ScienceAgent"

    def get_prompt(self, user_input: str) -> str:
        return f"Explain this scientific concept: {user_input}"
```

2. **Register with Orchestrator**:
```python
# In graph.py
parallel_orchestrator.register_agent("science", lambda: ScienceAgent(llm_factory))
```

3. **Update Intent Classification**:
The LLM-powered classifier will automatically learn to detect new intent types. You can also enhance the manual extraction fallback in `_extract_intents_manually()`.

### **Adding New LLM Providers**

1. **Create Provider Class**:
```python
from src.config.settings import LLMConfig

class ClaudeProvider:
    def __init__(self, config: LLMConfig):
        self.config = config

    def create_llm(self):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=self.config.model,
            temperature=self.config.temperature
        )
```

2. **Register Provider**:
```python
# In llm_factory.py
self._providers["claude"] = ClaudeProvider
```

### **Customizing Parallel Execution**

```python
from src.core.types import ParallelExecutionConfig

custom_config = ParallelExecutionConfig(
    max_concurrent_agents=5,
    timeout_seconds=60.0,
    confidence_threshold=0.2,
    require_primary_intent=False
)

orchestrator = ParallelOrchestrator(llm_factory, custom_config)
```

## 🧪 Testing

### **Run All Tests**
```bash
python -m pytest tests/ -v
```

### **Test Specific Components**
```bash
# Test intent classification
python -m pytest tests/test_intent_classifier.py -v

# Test LLM factory
python -m pytest tests/test_llm_factory.py -v
```

### **Manual Testing**
```bash
# Test the complete system
python graph.py

# Test interactive mode
python run.py
```

## 📊 Performance Characteristics

### **Single Mode**
- **Latency**: ~2-5 seconds per request
- **Resource Usage**: 1 LLM call per request
- **Use Case**: Simple, single-intent queries

### **Parallel Mode**
- **Latency**: ~5-15 seconds per request (depending on agents)
- **Resource Usage**: Multiple concurrent LLM calls
- **Efficiency**: Processes multiple intents simultaneously
- **Use Case**: Complex, multi-intent queries

### **Optimization Features**
- **Lazy Loading**: LLM instances created only when needed
- **Timeout Protection**: Prevents hanging requests
- **Error Resilience**: Graceful degradation on failures
- **Confidence Filtering**: Only processes high-confidence intents

## 🚦 System Status

- ✅ **Multi-Intent Detection**: Fully implemented
- ✅ **Parallel Execution**: Working with ThreadPoolExecutor
- ✅ **Result Aggregation**: LLM-powered intelligent combination
- ✅ **Error Handling**: Comprehensive error management
- ✅ **Backward Compatibility**: Legacy functions maintained
- ✅ **Testing**: Unit tests for core components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

Apache License 2.0

## 🐳 Docker Deployment

The system includes complete Docker deployment setup for both development and production environments.

### **Quick Docker Deployment**

```bash
# Development deployment
./deployment/scripts/deploy.sh dev --build

# Production deployment
cp deployment/.env.production deployment/.env
# Edit deployment/.env with your API keys
./deployment/scripts/deploy.sh prod --build
```

### **API Endpoints**
Once deployed, the API will be available at:
- **API Base**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **Interactive Docs**: `http://localhost:8000/docs`
- **Process Endpoint**: `POST http://localhost:8000/process`

### **Example API Usage**
```bash
# Single intent
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"input": "Solve 2x + 3 = 7"}'

# Multi-intent parallel processing
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{"input": "Explain AI and solve 2x + 3 = 7", "use_parallel": true}'
```

### **Docker Services**
- **multi-agent-api**: Main FastAPI application
- **redis**: Caching and session management
- **nginx**: Reverse proxy (production)
- **prometheus**: Metrics collection (optional)
- **grafana**: Monitoring dashboard (optional)

For detailed deployment instructions, see [`deployment/README.md`](deployment/README.md).

---

**Built with ❤️ using LangGraph, LangChain, FastAPI, Docker, and modern Python practices**
