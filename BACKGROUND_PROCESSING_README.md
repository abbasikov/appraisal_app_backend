# Background Photo Processing

This implementation adds background processing capabilities to handle photo imports from Dropbox without blocking the server.

## Features

- **Background Task Processing**: Photo imports run in the background using Celery
- **Progress Tracking**: Real-time status updates and progress monitoring
- **Batch Processing**: Configurable batch sizes for optimal performance
- **Recurring Batches**: Option to process all photos in batches until complete
- **Task Management**: View task history and monitor ongoing processes
- **Error Handling**: Comprehensive error reporting and recovery

## Architecture

### Components

1. **Celery** - Background job queue system
2. **Redis** - Message broker and result backend
3. **TaskStatus Model** - Database tracking for task status and progress
4. **Background Tasks** - Celery tasks for photo import operations
5. **API Endpoints** - New endpoints for managing background tasks

### Workflow

```
1. User triggers photo import via API
2. API creates background task and returns task ID
3. Celery worker processes photos in background
4. Progress updates stored in database
5. User can monitor progress via task status endpoints
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- Redis server
- PostgreSQL/SQLite database

### Installation

1. **Run the setup script**:
   ```bash
   python setup_background_processing.py
   ```

2. **Manual setup** (if automatic setup fails):
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Install and start Redis
   brew install redis  # macOS
   redis-server
   
   # Create database tables
   python add_task_status_table.py
   ```

### Starting Services

1. **Start a Celery worker** (required):
   ```bash
   python start_celery_worker.py
   ```

2. **Start Flower monitoring** (optional):
   ```bash
   python start_celery_flower.py
   ```
   Navigate to http://localhost:5555 for the web UI

3. **Start the FastAPI server**:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### Background Photo Import

**POST** `/api/v1/projects/{project_id}/import-photos-background`

Start background photo import process.

**Request Body**:
```json
{
  "batch_size": 10,
  "recurring": false
}
```

**Response**:
```json
{
  "task_id": "12345-abcd-6789-efgh",
  "message": "Photo import task started",
  "project_id": 1,
  "batch_size": 10,
  "recurring": false,
  "estimated_duration": "Approximately 30 seconds"
}
```

### Task Status Monitoring

**GET** `/api/v1/projects/{project_id}/task-status/{task_id}`

Get current status of a background task.

**Response**:
```json
{
  "id": 1,
  "task_id": "12345-abcd-6789-efgh",
  "task_type": "photo_import",
  "project_id": 1,
  "user_id": 1,
  "status": "processing",
  "progress": 65,
  "total_items": 100,
  "processed_items": 65,
  "error_message": null,
  "result_data": "{\"imported_count\": 65, \"total_found\": 100}",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:00Z",
  "completed_at": null
}
```

### Project Tasks

**GET** `/api/v1/projects/{project_id}/tasks`

Get all background tasks for a project.

**Response**:
```json
[
  {
    "id": 1,
    "status": "completed",
    "progress": 100,
    "created_at": "2024-01-15T10:00:00Z",
    ...
  }
]
```

## Task Types

### Single Batch Processing
- Processes one batch of photos
- Good for quick imports or testing
- Estimated duration: `batch_size * 3 seconds`

### Recurring Batch Processing
- Continues processing batches until all photos are imported
- Includes delays between batches to prevent server overload
- Good for large photo collections
- Progress updates after each batch

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Celery Settings

Configured in `app/core/celery_app.py`:

- **Task timeout**: 30 minutes max per task
- **Soft timeout**: 25 minutes warning
- **Worker concurrency**: 2 workers (adjustable)
- **Result expiration**: 1 hour

## Monitoring

### Flower Dashboard

Access real-time monitoring at http://localhost:5555

Features:
- Active and completed tasks
- Worker status and performance
- Task execution history
- Real-time graphs and statistics

### Database Monitoring

Query task status directly:

```sql
-- Current active tasks
SELECT * FROM task_status WHERE status IN ('pending', 'processing');

-- Task history for a project
SELECT * FROM task_status WHERE project_id = 1 ORDER BY created_at DESC;

-- Failed tasks
SELECT * FROM task_status WHERE status = 'failed';
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Check if Redis is running
   redis-cli ping
   
   # Start Redis if not running
   redis-server
   ```

2. **Celery Worker Won't Start**
   ```bash
   # Check Redis connection
   python -c "import redis; redis.Redis().ping()"
   
   # Check Python dependencies
   pip install celery redis flower
   ```

3. **Tasks Not Processing**
   - Ensure Celery worker is running
   - Check worker logs for errors
   - Verify Redis connectivity

4. **Database Errors**
   ```bash
   # Recreate task status table
   python add_task_status_table.py
   ```

### Performance Tuning

1. **Adjust batch size** based on server capacity
2. **Increase worker concurrency** for faster processing
3. **Monitor Redis memory usage** during large imports
4. **Use SSD storage** for better I/O performance

## Migration from Synchronous Processing

The original synchronous endpoints remain available:

- **POST** `/api/v1/projects/{project_id}/import-photos` - Original synchronous endpoint

For new implementations, use the background endpoints:

- **POST** `/api/v1/projects/{project_id}/import-photos-background` - New background endpoint

## Security Considerations

- Background tasks run with full database access
- Ensure proper user permissions are maintained
- Monitor Redis for potential security issues
- Use proper authentication for monitoring endpoints

## Future Enhancements

- WebSocket support for real-time progress updates
- Task cancellation functionality
- Priority queues for urgent imports
- Distributed workers across multiple servers
- Automatic cleanup of old tasks
