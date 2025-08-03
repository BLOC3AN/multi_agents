import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Optional, BinaryIO
import logging
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)

class S3Manager:
    """
    S3 Manager class để thao tác với S3 storage
    """

    def __init__(self):
        """
        Khởi tạo S3 client với config từ environment variables
        """
        self.endpoint_url = os.getenv('S3_ENDPOINT')
        self.access_key = os.getenv('S3_ACCESS_KEY')
        self.secret_key = os.getenv('S3_SECRET_KEY')
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'hailt')
        self.region = os.getenv('S3_REGION', 'us-east-1')

        if not all([self.endpoint_url, self.access_key, self.secret_key]):
            raise ValueError("Missing S3 configuration. Please check your .env file.")

        try:
            # Sử dụng signature V4 cho Viettel S3
            from botocore.config import Config

            config = Config(signature_version='s3v4')

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url,
                config=config
            )

            # Test connection
            self._test_connection()
            logger.info(f"S3 client initialized successfully for bucket: {self.bucket_name}")

        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def _test_connection(self):
        """
        Test S3 connection và tạo bucket nếu chưa tồn tại
        """
        try:
            # Kiểm tra bucket có tồn tại không
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists and is accessible")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket không tồn tại, tạo mới
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created new bucket: {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {str(create_error)}")
                    raise
            elif error_code == '403':
                # Forbidden - có thể bucket đã tồn tại nhưng không có quyền head_bucket
                # Thử list objects để test quyền truy cập
                try:
                    self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
                    logger.info(f"Bucket {self.bucket_name} is accessible (403 on head_bucket but can list objects)")
                except ClientError as list_error:
                    logger.error(f"Cannot access bucket {self.bucket_name}: {str(list_error)}")
                    raise
            else:
                logger.error(f"Error accessing bucket: {str(e)}")
                raise

    def upload_file(self, file_obj: BinaryIO, file_name: str, folder: str = "documents") -> Dict:
        """
        Upload file lên S3

        Args:
            file_obj: File object để upload
            file_name: Tên file
            folder: Thư mục trong bucket (default: documents)

        Returns:
            Dict chứa thông tin file đã upload
        """
        try:
            # Tạo key cho file (upload trực tiếp vào root bucket)
            file_key = file_name  # Bỏ folder để test

            # Detect content type
            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = 'application/octet-stream'

            # Thử upload với put_object (giống như test Python)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_obj.getvalue()
            )

            # Get file info
            file_info = self.get_file_info(file_key)

            logger.info(f"Successfully uploaded file: {file_key}")
            return {
                'success': True,
                'file_key': file_key,
                'file_name': file_name,
                'file_info': file_info
            }

        except Exception as e:
            logger.error(f"Failed to upload file {file_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def download_file(self, file_key: str) -> Dict:
        """
        Download file từ S3

        Args:
            file_key: Key của file trong S3

        Returns:
            Dict chứa file data hoặc error
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)

            return {
                'success': True,
                'file_data': response['Body'].read(),
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'file_size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified')
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                return {'success': False, 'error': 'File not found'}
            else:
                logger.error(f"Failed to download file {file_key}: {str(e)}")
                return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to download file {file_key}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_download_url(self, file_key: str, expiration: int = 3600) -> Dict:
        """
        Tạo presigned URL để download file

        Args:
            file_key: Key của file trong S3
            expiration: Thời gian hết hạn URL (seconds, default: 1 hour)

        Returns:
            Dict chứa download URL hoặc error
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )

            return {
                'success': True,
                'download_url': url,
                'expires_in': expiration
            }

        except Exception as e:
            logger.error(f"Failed to generate download URL for {file_key}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_files(self, folder: str = "", limit: int = 100) -> Dict:
        """
        Liệt kê files trong bucket

        Args:
            folder: Thư mục cần liệt kê (default: "" = all files)
            limit: Số lượng file tối đa (default: 100)

        Returns:
            Dict chứa danh sách files
        """
        try:
            prefix = f"{folder}/" if folder else ""

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    file_info = {
                        'key': obj['Key'],
                        'name': obj['Key'].split('/')[-1],  # Lấy tên file từ key
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'folder': '/'.join(obj['Key'].split('/')[:-1]) if '/' in obj['Key'] else ''
                    }
                    files.append(file_info)

            return {
                'success': True,
                'files': files,
                'total': len(files),
                'has_more': response.get('IsTruncated', False)
            }

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_file(self, file_key: str) -> Dict:
        """
        Xóa file từ S3

        Args:
            file_key: Key của file cần xóa

        Returns:
            Dict chứa kết quả xóa
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)

            logger.info(f"Successfully deleted file: {file_key}")
            return {
                'success': True,
                'message': f'File {file_key} deleted successfully'
            }

        except Exception as e:
            logger.error(f"Failed to delete file {file_key}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_file_info(self, file_key: str) -> Dict:
        """
        Lấy thông tin chi tiết của file

        Args:
            file_key: Key của file

        Returns:
            Dict chứa thông tin file
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)

            return {
                'key': file_key,
                'name': file_key.split('/')[-1],
                'size': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', 'unknown'),
                'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag', '').strip('"')
            }

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {'error': 'File not found'}
            else:
                return {'error': str(e)}
        except Exception as e:
            return {'error': str(e)}

    def get_file_content(self, file_key: str) -> Dict:
        """
        Lấy nội dung file để hiển thị (không download)

        Args:
            file_key: Key của file trong S3

        Returns:
            Dict chứa nội dung file và metadata
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )

            file_content = response['Body'].read()
            stored_content_type = response.get('ContentType', 'application/octet-stream')

            # Override content type based on file extension for better detection
            import mimetypes
            file_name = file_key.split('/')[-1]
            detected_content_type, _ = mimetypes.guess_type(file_name)
            content_type = detected_content_type or stored_content_type

            # Determine if file is text-based for preview
            text_types = [
                'text/', 'application/json', 'application/xml',
                'application/javascript', 'application/csv'
            ]

            # Also check file extension for common text files
            text_extensions = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log']
            file_ext = '.' + file_name.split('.')[-1].lower() if '.' in file_name else ''

            is_text = any(content_type.startswith(t) for t in text_types) or file_ext in text_extensions

            result = {
                'success': True,
                'file_key': file_key,
                'file_name': file_name,
                'content_type': content_type,
                'size': len(file_content),
                'is_text': is_text
            }

            if is_text:
                # For text files, decode content
                try:
                    result['content'] = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        result['content'] = file_content.decode('latin-1')
                    except:
                        result['is_text'] = False
                        result['content'] = None
            else:
                # Handle special file types
                if content_type.startswith('image/'):
                    import base64
                    result['content'] = base64.b64encode(file_content).decode('utf-8')
                elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_ext == '.docx':
                    # Handle Word documents
                    try:
                        from docx import Document
                        import io

                        # Create a Document object from the file content
                        doc = Document(io.BytesIO(file_content))

                        # Extract text from all paragraphs
                        text_content = []
                        for paragraph in doc.paragraphs:
                            if paragraph.text.strip():  # Only add non-empty paragraphs
                                text_content.append(paragraph.text)

                        result['content'] = '\n\n'.join(text_content)
                        result['is_text'] = True
                        result['content_type'] = 'text/plain'  # Override for display

                        logger.info(f"Successfully extracted text from Word document: {file_key}")
                    except Exception as e:
                        logger.error(f"Failed to extract text from Word document {file_key}: {str(e)}")
                        result['content'] = None
                else:
                    result['content'] = None

            logger.info(f"Successfully retrieved content for file: {file_key} (type: {content_type}, is_text: {is_text})")
            return result

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {
                    'success': False,
                    'error': 'File not found'
                }
            else:
                logger.error(f"Failed to get file content: {str(e)}")
                return {
                    'success': False,
                    'error': str(e)
                }
        except Exception as e:
            logger.error(f"Failed to get file content: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
s3_manager = None

def get_s3_manager() -> S3Manager:
    """
    Get singleton S3Manager instance
    """
    global s3_manager
    if s3_manager is None:
        s3_manager = S3Manager()
    return s3_manager