# File Management System

## Tổng quan

Hệ thống quản lý file mới đã được triển khai với các tính năng:

- **Giới hạn 50 files per user**: Mỗi user chỉ được upload tối đa 50 files
- **User isolation**: Files của user không được chia sẻ với nhau
- **Metadata storage**: Lưu trữ metadata trong MongoDB theo user_id
- **Auto cleanup**: Tự động xóa files cũ khi vượt giới hạn

## Cấu trúc Database

### Collection: `file_metadata`

```javascript
{
  file_id: "uuid",           // Unique file identifier
  user_id: "string",         // User owner ID
  file_key: "string",        // S3 key/path (unique)
  file_name: "string",       // Original filename
  file_size: number,         // File size in bytes
  content_type: "string",    // MIME type
  upload_date: "ISO string", // Upload timestamp
  s3_bucket: "string",       // S3 bucket name
  is_active: boolean,        // Active status
  metadata: {}               // Additional metadata
}
```

### Indexes

- `file_id` (unique)
- `user_id`
- `file_key` (unique)
- `user_id + upload_date` (compound)
- `upload_date`
- `is_active`
- `content_type`

## API Changes

### Upload Endpoint: `POST /api/s3/upload`

**Thay đổi**: Bây giờ yêu cầu `user_id` parameter

```javascript
// Request
FormData {
  file: File,
  user_id: "string"
}

// Response
{
  success: true,
  message: "File uploaded successfully",
  file_info: {...},
  file_id: "uuid",
  file_count: number
}
```

### List Files Endpoint: `GET /api/s3/files`

**Thay đổi**: Bây giờ yêu cầu `user_id` query parameter

```javascript
// Request
GET /api/s3/files?user_id=user123

// Response
{
  success: true,
  files: [...],
  total_files: number,
  file_limit: {
    current: number,
    max: 50,
    remaining: number
  }
}
```

### Delete Endpoint: `DELETE /api/s3/delete/{file_key}`

**Thay đổi**: Bây giờ yêu cầu `user_id` query parameter và kiểm tra ownership

```javascript
// Request
DELETE /api/s3/delete/filename.txt?user_id=user123

// Response
{
  success: true,
  message: "File deleted successfully",
  file_key: "filename.txt"
}
```

## Backend Components

### 1. FileMetadata Model (`src/database/models.py`)

```python
@dataclass
class FileMetadata:
    file_id: str
    user_id: str
    file_key: str
    file_name: str
    file_size: int
    content_type: str
    upload_date: Optional[datetime] = None
    s3_bucket: Optional[str] = None
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
```

### 2. FileManager Service (`src/services/file_manager.py`)

Các chức năng chính:

- `check_file_limit(user_id)`: Kiểm tra giới hạn file
- `get_user_files(user_id)`: Lấy danh sách files của user
- `handle_file_upload()`: Xử lý upload với limit checking
- `delete_file()`: Xóa file với authorization check
- `cleanup_old_files()`: Tự động xóa files cũ

### 3. Updated API Endpoints (`auth_server.py`)

- Upload endpoint với user authentication
- List files với user isolation
- Delete với ownership verification

## Frontend Changes

### FilesBlock Component (`frontend/src/components/FilesBlock.tsx`)

**Thay đổi**: Thêm `userId` prop

```typescript
interface FilesBlockProps {
  className?: string;
  userId: string;  // New required prop
}
```

**Usage trong ChatPage**:
```typescript
<FilesBlock userId={user?.user_id || ''} />
```

## File Limit Logic

1. **Upload Process**:
   - Kiểm tra số lượng files hiện tại
   - Nếu >= 50 files: Xóa file cũ nhất
   - Upload file mới
   - Lưu metadata

2. **Auto Cleanup**:
   - Sắp xếp files theo `upload_date` (cũ nhất trước)
   - Xóa files vượt quá giới hạn
   - Cập nhật `is_active = false` trong database
   - Xóa file từ S3

## Migration

### Script: `migrate_existing_files.py`

Chạy script để migrate existing files:

```bash
python3 migrate_existing_files.py
```

Script sẽ:
- Scan S3 bucket cho existing files
- Tạo metadata entries với default user_id
- Cleanup orphaned metadata

### Test Script: `test_file_management.py`

Chạy tests để verify hệ thống:

```bash
python3 test_file_management.py
```

## Security Features

1. **User Isolation**: Files chỉ visible cho owner
2. **Authorization**: Delete chỉ cho phép owner
3. **Input Validation**: Validate user_id trong tất cả endpoints
4. **Error Handling**: Proper error messages và logging

## Monitoring

### Logs

- Upload success/failure với user_id
- File limit warnings
- Authorization failures
- Auto cleanup activities

### Statistics

Sử dụng FileManager để get statistics:

```python
file_manager = get_file_manager()
limit_check = file_manager.check_file_limit(user_id)
user_files = file_manager.get_user_files(user_id)
```

## Troubleshooting

### Common Issues

1. **"user_id is required"**: Frontend chưa gửi user_id
2. **"File not found or access denied"**: User cố delete file không phải của mình
3. **"File management service not available"**: FileManager import failed

### Debug Commands

```python
# Check user file count
from src.services.file_manager import get_file_manager
fm = get_file_manager()
print(fm.check_file_limit("user_id"))

# List user files
files = fm.get_user_files("user_id")
print(f"User has {len(files)} files")

# Check database
from src.database.models import get_db_config
db = get_db_config()
count = db.file_metadata.count_documents({"user_id": "user_id", "is_active": True})
print(f"Database shows {count} active files")
```

## Future Enhancements

1. **File sharing**: Cho phép user share files với nhau
2. **File versioning**: Lưu multiple versions của cùng file
3. **Storage quotas**: Giới hạn theo dung lượng thay vì số lượng
4. **File categories**: Phân loại files theo type/purpose
5. **Bulk operations**: Upload/delete multiple files cùng lúc
