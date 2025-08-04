# S3 Storage Setup Guide

## Tổng quan

Hệ thống đã được tích hợp với S3 storage để quản lý files. UI hiển thị một block "Files" ngay trên block "History" trong sidebar bên trái.

## Cấu hình hiện tại

File `.env` đã được cập nhật với cấu hình S3 Viettel:

```env
# S3 Viettel Configuration
S3_ENDPOINT=https://atm290327-s3user.vcos3.cloudstorage.com.vn
S3_ACCESS_KEY=atm290327-s3user
S3_SECRET_KEY=X6RwSQeDqUuFR4l3DETMwXOvc1qH3xlNhEEQEjYq
S3_BUCKET_NAME=hailt
S3_REGION=us-east-1
```

## Tính năng đã triển khai

### 1. Backend (Python)
- **Model S3**: `src/database/model_s3.py` - Class quản lý S3 operations
- **API Endpoints**: Đã thêm vào `auth_server.py`
  - `POST /api/s3/upload` - Upload files
  - `GET /api/s3/files` - List files
  - `GET /api/s3/download/{file_key}` - Download files
  - `DELETE /api/s3/delete/{file_key}` - Delete files
  - `GET /api/s3/info/{file_key}` - Get file info

### 2. Frontend (React)
- **FilesBlock Component**: `frontend/src/components/FilesBlock.tsx`
- **Tích hợp vào ChatPage**: Hiển thị ngay trên HistoryBlock
- **Chức năng**:
  - Drag & drop upload
  - Click to upload
  - Download files
  - Delete files
  - Hiển thị file size và ngày tạo

## Trạng thái hiện tại

**⚠️ QUAN TRỌNG**: Hiện tại hệ thống đang chạy với **mock data** do vấn đề với S3 credentials.

### Vấn đề gặp phải
```
SignatureDoesNotMatch: The request signature we calculated does not match the signature you provided.
```

### Nguyên nhân có thể
1. **Credentials không đúng**: Access Key hoặc Secret Key có thể sai
2. **Signature version**: Viettel S3 có thể yêu cầu signature version khác
3. **Endpoint configuration**: Cấu hình endpoint có thể cần điều chỉnh
4. **Bucket permissions**: Bucket có thể chưa tồn tại hoặc không có quyền truy cập

## Cách khắc phục

### 1. Kiểm tra credentials
Đăng nhập vào Viettel Cloud Portal và xác nhận:
- Access Key ID
- Secret Access Key
- Endpoint URL
- Bucket name và permissions

### 2. Test credentials với AWS CLI
```bash
aws configure set aws_access_key_id atm290327-s3user
aws configure set aws_secret_access_key X6RwSQeDqUuFR4l3DETMwXOvc1qH3xlNhEEQEjYq
aws configure set default.region us-east-1

# Test với endpoint
aws s3 ls --endpoint-url https://atm290327-s3user.vcos3.cloudstorage.com.vn
```

### 3. Cập nhật code khi credentials đúng
Trong file `auth_server.py`, uncomment các dòng code thực và comment mock data:

```python
# Comment mock data section
# mock_files = [...]

# Uncomment real S3 operations
s3_manager = get_s3_manager()
result = s3_manager.list_files()
# ...
```

### 4. Alternative S3 providers
Nếu Viettel S3 không hoạt động, có thể thử:
- AWS S3
- MinIO
- DigitalOcean Spaces
- Wasabi

## Cấu trúc files

```
src/database/
├── model_s3.py          # S3 manager class
└── models.py            # Existing database models

frontend/src/components/
├── FilesBlock.tsx       # Files management UI
└── HistoryBlock.tsx     # Existing history component

auth_server.py           # API endpoints
.env                     # S3 configuration
requirements.txt         # Added boto3 dependencies
```

## Testing

### API Testing
```bash
# List files
curl -X GET http://localhost:8000/api/s3/files

# Upload file
curl -X POST -F "file=@test.txt" http://localhost:8000/api/s3/upload

# Download file
curl -X GET http://localhost:8000/api/s3/download/documents/test.txt

# Delete file
curl -X DELETE http://localhost:8000/api/s3/delete/documents/test.txt
```

### UI Testing
1. Mở http://localhost:3000
2. Login vào hệ thống
3. Kiểm tra Files block trong sidebar
4. Test upload/download/delete functions

## Next Steps

1. **Khắc phục S3 credentials** - Ưu tiên cao nhất
2. **Enable real S3 operations** - Uncomment code trong auth_server.py
3. **Add file type restrictions** - Giới hạn loại file upload
4. **Add file size limits** - Giới hạn kích thước file
5. **Add progress indicators** - Hiển thị progress khi upload/download
6. **Add file preview** - Preview files trước khi download
7. **Add folder organization** - Tổ chức files theo folders

## Support

Nếu cần hỗ trợ:
1. Kiểm tra logs: `tail -f logs/auth.log`
2. Restart services: `make restart-auth`
3. Check service status: `make status`
