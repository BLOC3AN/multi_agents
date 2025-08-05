# Manual Embedding Guide

## 🎯 Overview

Manual embedding feature allows administrators to manually embed files into Qdrant when automatic embedding fails during upload. This is useful for recovering from embedding errors or embedding files that were uploaded before the embedding system was implemented.

## 🔧 Features Added

### 1. **Individual File Embedding**
- ✅ "Embed" button for each file missing from Qdrant
- ✅ Real-time loading state with spinner
- ✅ Only shows for files that exist in MongoDB and S3 but missing from Qdrant
- ✅ Automatic refresh of sync status after embedding

### 2. **Bulk Embedding**
- ✅ "Embed All Missing" button to embed multiple files at once
- ✅ Sequential processing to avoid overwhelming the server
- ✅ Progress indication and error handling
- ✅ Shows count of files to be embedded

### 3. **Smart UI Logic**
- ✅ Buttons only appear when needed (missing from Qdrant)
- ✅ Disabled state during processing
- ✅ Visual feedback with icons and loading states
- ✅ Error messages displayed to user

## 🖥️ User Interface

### Location
- **Admin Page** → **Sync Tab** → **Global Sync Status Panel**

### Visual Indicators
- 🔴 **Red Qdrant icon**: File missing from Qdrant
- 🟢 **Green Qdrant icon**: File present in Qdrant
- 🔵 **Blue "Embed" button**: Available for manual embedding
- 🔄 **Spinning icon**: Embedding in progress

### Buttons
1. **Individual "Embed" Button**
   - Appears next to files missing from Qdrant
   - Shows "Embedding..." with spinner during process
   - Automatically refreshes status after completion

2. **"Embed All Missing (X)" Button**
   - Appears in actions section when multiple files need embedding
   - Shows count of files to be embedded
   - Processes files sequentially
   - Shows "Embedding All..." during process

## 🔧 Technical Implementation

### API Endpoint
```
POST /api/s3/embed-existing
Content-Type: application/json

{
  "user_id": "user123",
  "file_key": "document.txt"
}
```

### Response Format
```json
{
  "success": true,
  "message": "File embedded successfully",
  "embedding_id": "uuid-here",
  "embedded": true
}
```

### Error Handling
```json
{
  "success": false,
  "error": "Failed to embed file: File not found"
}
```

## 📋 Usage Instructions

### For Individual Files

1. **Navigate to Admin Page**
   - Go to `/admin` in your browser
   - Click on the "Sync" tab

2. **Identify Missing Files**
   - Look for files with red Qdrant icons
   - These files exist in MongoDB and S3 but are missing from Qdrant

3. **Manual Embed**
   - Click the blue "Embed" button next to the file
   - Wait for the process to complete (button shows "Embedding...")
   - Status will automatically refresh

### For Multiple Files

1. **Check for Bulk Option**
   - If multiple files are missing from Qdrant
   - Look for "Embed All Missing (X)" button in the actions section

2. **Bulk Embed**
   - Click "Embed All Missing" button
   - Files will be processed sequentially
   - Wait for completion (button shows "Embedding All...")

## 🛠️ Troubleshooting

### Common Issues

1. **"Failed to embed file" Error**
   - **Cause**: File content cannot be extracted or processed
   - **Solution**: Check file format support, ensure file is not corrupted
   - **Supported formats**: .txt, .md, .py, .js, .html, .docx, .pdf

2. **"File not found" Error**
   - **Cause**: File exists in MongoDB but not in S3
   - **Solution**: Re-upload the file or check S3 sync

3. **"File already embedded" Message**
   - **Cause**: File is already in Qdrant
   - **Solution**: This is normal, no action needed

4. **Button Not Appearing**
   - **Cause**: File is already embedded or missing from MongoDB/S3
   - **Solution**: Check file status in all three systems

### Debug Commands

```bash
# Check embedding status
python3 scripts/test_manual_embed.py

# Check sync status
python3 scripts/sync_db_s3.py

# Check file health
python3 scripts/file_health_check.py --s3
```

## 📊 Monitoring

### Sync Status Indicators

| Icon | Status | Meaning |
|------|--------|---------|
| 🟢 | Synced | File present in all systems |
| 🟡 | Out of Sync | File missing from one system |
| 🔴 | Missing | File missing from multiple systems |

### Storage Locations

| Icon | System | Purpose |
|------|--------|---------|
| 💾 | MongoDB | File metadata |
| 🗄️ | S3 | File content |
| 🔍 | Qdrant | Vector embeddings |

## 🔄 Workflow

### Automatic Embedding (Normal Flow)
```
User Upload → S3 Storage → MongoDB Metadata → Qdrant Embedding
```

### Manual Embedding (Recovery Flow)
```
Admin Identifies Missing → Click Embed → API Call → Qdrant Storage → Status Refresh
```

## 🎯 Best Practices

1. **Regular Monitoring**
   - Check sync status regularly
   - Address missing embeddings promptly

2. **Bulk Operations**
   - Use "Embed All Missing" for efficiency
   - Monitor server load during bulk operations

3. **Error Investigation**
   - Check file formats for failed embeddings
   - Verify file integrity in S3

4. **Preventive Measures**
   - Ensure embedding service is running during uploads
   - Monitor Qdrant service health

## 📈 Performance Notes

- **Sequential Processing**: Files are embedded one at a time to avoid server overload
- **Timeout**: Each embedding operation has a 30-second timeout
- **Rate Limiting**: Built-in delays between bulk operations
- **Memory Usage**: Large files may require more processing time

## 🔐 Security

- **User Isolation**: Each user can only embed their own files
- **Admin Access**: Manual embedding requires admin privileges
- **Validation**: File ownership verified before embedding
- **Audit Trail**: All embedding operations are logged

## 📝 Files Modified

### Frontend Components
- `frontend/src/components/SyncStatusPanel.tsx` - Added manual embed UI

### Backend APIs
- `auth_server.py` - `/api/s3/embed-existing` endpoint (already existed)

### Scripts
- `scripts/test_manual_embed.py` - Testing and validation script

### Documentation
- `docs/MANUAL_EMBEDDING_GUIDE.md` - This guide
