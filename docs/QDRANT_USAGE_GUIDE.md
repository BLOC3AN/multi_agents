# Qdrant Vector Database Usage Guide

## Tổng quan

Qdrant Vector Database được tích hợp vào hệ thống Multi-Agent để hỗ trợ tìm kiếm semantic và lưu trữ vector embeddings. Hệ thống sử dụng Qdrant Cloud với cấu hình vector 1024 chiều và hỗ trợ cả dense vector và sparse vector (BM25).

## Cấu hình

### Environment Variables

Trong file `.env`, cần có các biến sau:

```env
QDRANT_CLOUD_API_KEY=your_qdrant_api_key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_COLLECTION=agent_data
```

### Cài đặt Dependencies

```bash
pip install qdrant-client>=1.7.0
```

## Cấu trúc Vector Collection

### Vector Configuration
- **Dense Vector**: 1024 chiều, sử dụng COSINE distance
- **Sparse Vector**: BM25 với IDF modifier
- **Collection Name**: `agent_data` (có thể thay đổi trong .env)

### Payload Structure

```json
{
  "id": "unique_id_string_or_int",
  "vector": {
    "dense_vector": [...],  // 1024 dimensions
    "bm25_sparse_vector": {...}  // optional sparse vector
  },
  "payload": {
    "text": "Nội dung đoạn văn bản hoặc câu hỏi",
    "title": "Tiêu đề (nếu có)",
    "source": "tên file hoặc nguồn dữ liệu", 
    "page": 1,
    "timestamp": "2025-08-04T15:30:00Z",
    "metadata": {
      "author": "Tên tác giả",
      "category": "Loại tài liệu",
      "language": "vi"
    },
    "extra": {
      "summary": "Tóm tắt ngắn gọn nếu có",
      "url": "https://example.com/source"
    }
  }
}
```

## Sử dụng cơ bản

### 1. Import và khởi tạo

```python
from src.database.model_qdrant import (
    get_qdrant_config,
    create_vector_document,
    VectorDocument
)

# Khởi tạo Qdrant config
qdrant = get_qdrant_config()
```

### 2. Tạo và lưu trữ document

```python
# Tạo document
doc = create_vector_document(
    text="Python là một ngôn ngữ lập trình mạnh mẽ",
    title="Giới thiệu Python",
    source="python_tutorial.md",
    author="Lập trình viên",
    category="programming",
    language="vi"
)

# Tạo vector embedding (1024 chiều)
# Trong thực tế, sử dụng model embedding như OpenAI, Sentence Transformers, etc.
embedding = your_embedding_model.encode(doc.text)  # List[float] với 1024 chiều

# Lưu vào Qdrant
success = qdrant.upsert_document(doc, embedding)
```

### 3. Tìm kiếm semantic

```python
# Tạo query embedding
query_text = "học lập trình Python"
query_embedding = your_embedding_model.encode(query_text)

# Tìm kiếm
results = qdrant.search_similar(
    query_vector=query_embedding,
    limit=10,
    score_threshold=0.7
)

# Xử lý kết quả
for result in results:
    doc = result['document']
    score = result['score']
    print(f"Title: {doc.title}")
    print(f"Score: {score:.3f}")
    print(f"Text: {doc.text[:100]}...")
```

### 4. Tìm kiếm với filter

```python
# Tìm kiếm với điều kiện lọc
filter_conditions = {
    "must": [
        {
            "key": "metadata.category",
            "match": {"value": "programming"}
        },
        {
            "key": "metadata.language", 
            "match": {"value": "vi"}
        }
    ]
}

results = qdrant.search_similar(
    query_vector=query_embedding,
    limit=5,
    score_threshold=0.5,
    filter_conditions=filter_conditions
)
```

### 5. Quản lý documents

```python
# Lấy document theo ID
doc = qdrant.get_document("document_id")

# Cập nhật document
updated_doc = VectorDocument(
    id="document_id",
    text="Nội dung đã cập nhật",
    title="Tiêu đề mới",
    # ... các field khác
)
new_embedding = your_embedding_model.encode(updated_doc.text)
qdrant.upsert_document(updated_doc, new_embedding)

# Xóa document
qdrant.delete_document("document_id")
```

## Sử dụng thông qua Database Models

### Kiểm tra availability

```python
from src.database.models import is_qdrant_available, get_vector_db_info

if is_qdrant_available():
    info = get_vector_db_info()
    print(f"Collection có {info['points_count']} documents")
```

### Lưu trữ đơn giản

```python
from src.database.models import store_vector_document

doc_id = store_vector_document(
    text="Nội dung document",
    embedding=embedding_vector,
    title="Tiêu đề",
    source="file.txt",
    author="Tác giả",
    category="loại"
)
```

### Tìm kiếm đơn giản

```python
from src.database.models import search_vector_documents

results = search_vector_documents(
    query_embedding=query_vector,
    limit=10,
    score_threshold=0.7
)
```

## Testing

### Chạy tests

```bash
# Chạy tất cả tests
python -m pytest tests/test_qdrant_model.py -v

# Chạy test cụ thể
python tests/test_qdrant_model.py
```

### Chạy example

```bash
python examples/qdrant_usage_example.py
```

## Best Practices

### 1. Vector Embeddings
- Sử dụng model embedding chất lượng cao (OpenAI, Sentence Transformers)
- Đảm bảo vector có đúng 1024 chiều
- Normalize vectors nếu cần thiết

### 2. Document Structure
- Luôn cung cấp `text` và `title` có ý nghĩa
- Sử dụng `source` để track nguồn gốc
- Thêm metadata phù hợp cho filtering

### 3. Search Optimization
- Điều chỉnh `score_threshold` phù hợp với use case
- Sử dụng filters để thu hẹp kết quả
- Limit số lượng kết quả hợp lý

### 4. Error Handling
- Luôn kiểm tra `is_qdrant_available()` trước khi sử dụng
- Handle exceptions khi kết nối Qdrant
- Có fallback mechanism khi vector search không khả dụng

## Troubleshooting

### Lỗi kết nối
```
❌ Failed to initialize Qdrant collection
```
- Kiểm tra `QDRANT_CLOUD_API_KEY` và `QDRANT_URL` trong .env
- Verify Qdrant Cloud cluster đang hoạt động
- Check network connectivity

### Lỗi vector dimension
```
❌ Vector dimension mismatch
```
- Đảm bảo embedding vector có đúng 1024 chiều
- Kiểm tra embedding model output

### Lỗi import
```
⚠️ Qdrant model not available
```
- Cài đặt `qdrant-client`: `pip install qdrant-client>=1.7.0`
- Restart application sau khi cài đặt

## Monitoring

### Collection Statistics
```python
qdrant = get_qdrant_config()
info = qdrant.get_collection_info()
print(f"Points: {info['points_count']}")
print(f"Vectors: {info['vectors_count']}")
print(f"Status: {info['status']}")
```

### Performance Monitoring
- Monitor search latency
- Track vector storage usage
- Monitor Qdrant Cloud metrics

## File Upload Integration

### Tự động Embedding khi Upload

Hệ thống đã được tích hợp để tự động embedding files khi upload:

```python
# File upload với embedding tự động
upload_result = file_manager.handle_file_upload(
    user_id="user123",
    file_key="document.txt",
    file_name="document.txt",
    file_size=1024,
    content_type="text/plain",
    file_content=file_bytes  # Quan trọng: cần truyền file content
)

# Kết quả sẽ có thông tin embedding
if upload_result["success"]:
    print(f"File uploaded: {upload_result['file_id']}")
    if upload_result.get("embedding_id"):
        print(f"File embedded: {upload_result['embedding_id']}")
```

### Kiểm tra File đã Embedded

```python
from src.services.file_embedding_service import get_file_embedding_service

embedding_service = get_file_embedding_service()
is_embedded = embedding_service.check_file_embedded(
    user_id="user123",
    filename="document.txt",
    file_key="documents/document.txt"
)
```

### Embedding File đã tồn tại

```python
# Embed file đã upload trước đó
result = file_manager.embed_existing_file(
    user_id="user123",
    file_key="document.txt"
)
```

### Xóa File và Vector

Khi xóa file, vector embedding cũng được xóa tự động:

```python
# Xóa file sẽ tự động xóa embedding
success = file_manager.delete_file("document.txt", "user123")
```

## API Endpoints

### Search Files

```bash
POST /api/s3/search
Content-Type: application/json

{
  "user_id": "user123",
  "query": "machine learning algorithms",
  "limit": 10
}
```

Response:
```json
{
  "success": true,
  "query": "machine learning algorithms",
  "results": [
    {
      "id": "doc_id",
      "title": "ML Guide.pdf",
      "source": "files/ml_guide.pdf",
      "text_preview": "Machine learning is...",
      "score": 0.85,
      "metadata": {...},
      "timestamp": "2025-08-04T10:30:00Z"
    }
  ],
  "total_results": 1,
  "search_type": "vector_similarity"
}
```

### Embed Existing File

```bash
POST /api/s3/embed-existing
Content-Type: application/json

{
  "user_id": "user123",
  "file_key": "document.txt"
}
```

## Supported File Types

Hệ thống tự động embedding các loại file sau:

- **Text files**: `.txt`, `.log`
- **Markdown**: `.md`, `.markdown`
- **Code files**: `.py`, `.js`, `.html`, `.css`, `.json`, `.xml`, `.yaml`, `.yml`
- **Documents**: `.docx` (cần cài `python-docx`)
- **PDFs**: `.pdf` (cần cài `PyPDF2`)

## Text Extraction

### Plain Text
```python
text = TextExtractor.extract_from_text(file_bytes)
```

### Markdown
```python
text = TextExtractor.extract_from_markdown(file_bytes)
# Tự động loại bỏ markdown formatting
```

### DOCX
```python
text = TextExtractor.extract_from_docx(file_bytes)
# Cần: pip install python-docx
```

### PDF
```python
text = TextExtractor.extract_from_pdf(file_bytes)
# Cần: pip install PyPDF2
```

## Embedding Models

### Sentence Transformers (Recommended)
```bash
pip install sentence-transformers
```

Sử dụng model `all-MiniLM-L6-v2` (384 dimensions, padded to 1024).

### Mock Embeddings (Development)
Nếu không có sentence-transformers, hệ thống sử dụng mock embeddings dựa trên hash.

## Tích hợp với Multi-Agent System

Qdrant model được tích hợp sẵn vào hệ thống database chính, có thể sử dụng cùng với MongoDB để:

1. **Semantic Search**: Tìm kiếm documents dựa trên ý nghĩa
2. **RAG (Retrieval Augmented Generation)**: Cung cấp context cho LLM
3. **Knowledge Base**: Lưu trữ và truy xuất kiến thức
4. **Content Recommendation**: Gợi ý nội dung liên quan
5. **File Management**: Tự động embedding và search files

### Workflow hoàn chỉnh

1. **User upload file** → Frontend gửi file + user_id
2. **File Manager** → Lưu metadata vào MongoDB + S3
3. **Embedding Service** → Extract text + tạo embedding
4. **Qdrant** → Lưu vector với user_id isolation
5. **Search** → User có thể search semantic trong files của mình
6. **Delete** → Xóa file cũng xóa vector tương ứng

Hệ thống đảm bảo:
- ✅ User isolation (mỗi user chỉ thấy files của mình)
- ✅ Duplicate prevention (không embed lại file đã có)
- ✅ Automatic cleanup (xóa file = xóa vector)
- ✅ Fallback support (hoạt động ngay cả khi Qdrant offline)
- ✅ Multiple file types support
- ✅ Real-time search với high accuracy
