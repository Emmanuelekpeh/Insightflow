from fastapi import HTTPException, status

class FileValidationError(HTTPException):
    """Exception raised when file validation fails."""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class FileSizeError(FileValidationError):
    """Exception raised when file size exceeds limit."""
    def __init__(self, max_size_mb: float):
        super().__init__(
            detail=f"File too large. Maximum size is {max_size_mb:.1f}MB"
        )

class FileTypeError(FileValidationError):
    """Exception raised when file type is not allowed."""
    def __init__(self, allowed_types: list[str]):
        super().__init__(
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

class FileExtensionError(FileValidationError):
    """Exception raised when file extension is not allowed."""
    def __init__(self, allowed_extensions: list[str]):
        super().__init__(
            detail=f"Invalid file extension. Allowed extensions: {', '.join(allowed_extensions)}"
        )

class ProcessingError(HTTPException):
    """Exception raised when file processing fails."""
    def __init__(self, detail: str = "Error processing file"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class QueueError(HTTPException):
    """Exception raised when job queueing fails."""
    def __init__(self, detail: str = "Failed to queue processing task"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

class StorageError(HTTPException):
    """Exception raised when file storage operations fail."""
    def __init__(self, detail: str = "Error storing file"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        ) 