# RAG System Guide

## 🎯 Tổng quan

Hệ thống RAG (Retrieval-Augmented Generation) cho phép AI assistant trả lời câu hỏi dựa trên tài liệu đã được upload và embedding trong vector database. Luồng hoạt động: **user query → RAG [Vector search, Hybrid search] → LLM**.

## ✅ Tính năng

### 1. **Vector Search**
- **Dense Vector Search**: Sử dụng cosine similarity với 1024-dim embeddings
- **Sparse Vector Search**: Sử dụng BM25 cho keyword matching
- **Hybrid Search**: Kết hợp cả dense và sparse search với weighted scoring

### 2. **Context Building**
- Lọc và rank documents theo relevance score
- Format context tối ưu cho LLM consumption
- Giới hạn context length để tránh token limit
- Source attribution và metadata tracking

### 3. **RAG Agent**
- Kế thừa BaseAgent architecture
- Tích hợp với existing LLM providers (Gemini, OpenAI)
- User isolation và error handling
- Conversation context support

## 📁 Cấu trúc Files

```
src/RAG/
├── __init__.py              # Package initialization
├── vector_search.py         # Vector search service
├── context_builder.py       # Context building logic
└── rag_agent.py            # Main RAG agent

examples/
└── rag_usage_example.py     # Usage examples và tests

docs/
└── RAG_SYSTEM_GUIDE.md     # This guide
```

## 🚀 Cách sử dụng

### 1. **Basic RAG Agent Usage**

```python
from src.RAG import RAGAgent
from src.llms.llm_factory import LLMFactory
from src.config.settings import config
from src.core.types import AgentState

# Initialize RAG agent
llm_factory = LLMFactory(config.llm)
rag_agent = RAGAgent(
    llm_factory=llm_factory,
    search_type="hybrid",  # "dense", "sparse", or "hybrid"
    max_context_length=4000
)

# Create query state
state = AgentState(
    input="What is machine learning?",
    user_id="user123",
    conversation_context=[],
    # ... other fields
)

# Process with RAG
result = rag_agent.process(state)
print(result["final_result"])  # AI response with context
print(result["rag_metadata"])  # Search metadata
```

### 2. **Vector Search Only**

```python
from src.RAG import VectorSearchService

# Initialize search service
search_service = VectorSearchService()

# Perform different types of search
dense_results = search_service.search_dense("machine learning", "user123", limit=5)
sparse_results = search_service.search_sparse("python programming", "user123", limit=5)
hybrid_results = search_service.search_hybrid("data science", "user123", limit=5)

# Unified search interface
results = search_service.search(
    query="AI algorithms",
    user_id="user123",
    search_type="hybrid",
    limit=10
)
```

### 3. **Context Building**

```python
from src.RAG import ContextBuilder

# Initialize context builder
context_builder = ContextBuilder(
    max_context_length=3000,
    min_relevance_score=0.3,
    max_documents=5
)

# Build context from search results
context_data = context_builder.build_context(search_results, query="AI question")

print(f"Documents: {context_data['total_documents']}")
print(f"Context: {context_data['context']}")
print(f"Sources: {context_data['sources']}")
```

## 🔧 Configuration

### Environment Variables
```env
# Qdrant Configuration (already configured)
QDRANT_CLOUD_API_KEY=your_api_key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_COLLECTION=agent_data

# LLM Configuration (already configured)
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash
LLM_TEMPERATURE=0.2
```

### RAG Agent Parameters
```python
RAGAgent(
    llm_factory=llm_factory,
    search_type="hybrid",        # Search strategy
    max_context_length=4000,     # Max context chars
    max_search_results=10        # Max search results
)
```

### Context Builder Parameters
```python
ContextBuilder(
    max_context_length=4000,     # Max context chars
    min_relevance_score=0.3,     # Min score to include
    max_documents=5              # Max documents to include
)
```

## 🔄 Integration với Existing System

### 1. **Với Simple Graph**
```python
from src.core.simple_graph import process_rag_node

# RAG node đã được thêm vào simple_graph.py
# Sử dụng process_rag_node thay vì process_conversation_node
```

### 2. **Với Auth Server**
```python
# Trong auth_server.py, có thể thêm RAG endpoint
@app.post("/api/rag/query")
async def rag_query(request: dict):
    user_id = request.get("user_id")
    query = request.get("query")
    
    # Create RAG agent
    rag_agent = create_rag_agent()
    
    # Process query
    state = AgentState(input=query, user_id=user_id, ...)
    result = rag_agent.process(state)
    
    return result
```

## 📊 Search Types Comparison

| Search Type | Strengths | Use Cases |
|-------------|-----------|-----------|
| **Dense** | Semantic similarity, context understanding | Conceptual questions, similar meaning |
| **Sparse** | Exact keyword matching, fast | Specific terms, names, technical keywords |
| **Hybrid** | Best of both worlds, balanced results | General purpose, most recommended |

## 🎯 Best Practices

### 1. **Search Strategy**
- Sử dụng **hybrid search** cho most cases
- Dùng **dense search** cho conceptual questions
- Dùng **sparse search** cho exact keyword matching

### 2. **Context Management**
- Giới hạn context length để tránh token limits
- Filter documents với min relevance score
- Provide source attribution trong responses

### 3. **Error Handling**
- Graceful fallback khi RAG components unavailable
- User-friendly error messages
- Maintain conversation flow even khi search fails

### 4. **Performance**
- Cache search results nếu cần
- Optimize embedding dimensions
- Monitor search latency

## 🧪 Testing

### Run Example Tests
```bash
cd /path/to/multi_agents
python examples/rag_usage_example.py
```

### Test Components
```python
# Test vector search
python -c "from examples.rag_usage_example import test_vector_search; test_vector_search()"

# Test context builder
python -c "from examples.rag_usage_example import test_context_builder; test_context_builder()"

# Test RAG agent
python -c "from examples.rag_usage_example import test_rag_agent; test_rag_agent()"
```

## 🔍 Troubleshooting

### Common Issues

1. **"Qdrant infrastructure not available"**
   - Check QDRANT_CLOUD_API_KEY và QDRANT_URL trong .env
   - Verify Qdrant connection

2. **"No search results found"**
   - Check if user has uploaded documents
   - Verify user_id isolation
   - Try different search types

3. **"Context too long"**
   - Reduce max_context_length
   - Increase min_relevance_score
   - Reduce max_documents

4. **"RAG agent not available"**
   - Check if all dependencies installed
   - Verify import paths
   - Fallback to regular conversation agent

## 📈 Future Enhancements

- [ ] **Advanced Reranking**: Implement cross-encoder reranking
- [ ] **Query Expansion**: Auto-expand queries for better recall
- [ ] **Caching**: Cache search results và embeddings
- [ ] **Analytics**: Track search performance và user satisfaction
- [ ] **Multi-modal**: Support image và audio documents
