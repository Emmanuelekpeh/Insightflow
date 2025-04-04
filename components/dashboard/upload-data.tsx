"use client"

import React, { useState, useRef, useCallback } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { FileUp, Upload, Loader2, X } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { UploadProgress, UploadStatus } from "@/components/ui/upload-progress"

interface UploadDataProps extends React.HTMLAttributes<HTMLDivElement> {
  onUploadComplete?: () => void; // Callback to notify parent
}

interface UploadState {
  status: UploadStatus
  progress: number
  jobId?: string
  error?: string
}

// Constants (should match backend)
const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls"];

export function UploadData({ className, onUploadComplete, ...props }: UploadDataProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [uploadState, setUploadState] = useState<UploadState | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const resetState = () => {
    setSelectedFile(null);
    setUploadState(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = ""; // Clear the input
    }
  }

  const pollJobStatus = useCallback(async (jobId: string, uploadId: string) => {
    const interval = setInterval(async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const response = await fetch(`${apiUrl}/api/dashboard/jobs/${jobId}/status`, {
          credentials: 'include',
        });

        if (!response.ok) {
          // Handle non-200 responses, but don't stop polling unless it's 404
          if (response.status === 404) {
            clearInterval(interval);
            setUploadState((prev) => ({
              ...prev!,
              status: "failed",
              error: "Processing job not found. It might have expired or failed silently.",
            }));
            toast({ title: "Upload Failed", description: "Processing job not found.", variant: "destructive" });
            if (onUploadComplete) onUploadComplete(); // Notify parent
          } else {
            // Log other errors but continue polling
            console.warn(`Job status check failed with status ${response.status}`);
          }
          return; // Don't process further on non-OK responses other than 404 handled above
        }

        const data = await response.json();

        setUploadState((prev) => { // Update progress based on status
          if (!prev) return null; // Should not happen if polling
          let newStatus = prev.status;
          let newProgress = prev.progress;
          let errorMsg = prev.error;

          switch (data.status) {
            case "queued":
              newStatus = "queued";
              newProgress = 50; // Indicate queueing progress
              break;
            case "processing":
              newStatus = "processing";
              newProgress = 75; // Indicate processing progress
              break;
            case "completed":
              clearInterval(interval);
              newStatus = "completed";
              newProgress = 100;
              toast({ title: "Upload Successful", description: `File '${selectedFile?.name}' processed.` });
              if (onUploadComplete) onUploadComplete(); // Notify parent
              break;
            case "failed":
              clearInterval(interval);
              newStatus = "failed";
              newProgress = 0; // Reset progress on failure
              errorMsg = data.error || "Processing failed with an unknown error.";
              toast({ title: "Upload Failed", description: errorMsg, variant: "destructive" });
              if (onUploadComplete) onUploadComplete(); // Notify parent
              break;
            // default: // Do nothing for unknown or intermediate states
          }
          return { ...prev, status: newStatus, progress: newProgress, error: errorMsg };
        });
      } catch (error: any) {
        console.error("Error polling job status:", error);
        // Only stop polling on network errors, let backend status dictate flow otherwise
        // clearInterval(interval); 
        // setUploadState((prev) => ({ ...prev!, status: "failed", error: "Failed to get job status." }));
        // toast({ title: "Error", description: "Could not retrieve job status.", variant: "destructive" });
      }
    }, 3000); // Poll every 3 seconds
    return () => clearInterval(interval); // Cleanup function
  }, [toast, selectedFile?.name, onUploadComplete]);

  const handleFileValidation = (file: File): boolean => {
    if (!file) return false;

    // Check Size
    if (file.size > MAX_FILE_SIZE) {
      toast({
        title: "File Too Large",
        description: `File size cannot exceed ${MAX_FILE_SIZE_MB}MB.`,
        variant: "destructive",
      });
      return false;
    }

    // Check Extension
    const fileExtension = file.name.slice(((file.name.lastIndexOf(".") - 1) >>> 0) + 1).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(fileExtension)) {
      toast({
        title: "Invalid File Type",
        description: `Allowed file types: ${ALLOWED_EXTENSIONS.join(", ")}.`,
        variant: "destructive",
      });
      return false;
    }

    // Basic MIME type check (less reliable but quick)
    // More robust check happens on the backend with python-magic
    // if (!file.type || !ALLOWED_MIME_TYPES.includes(file.type)) {
    //   toast({ title: "Invalid File Content", description: `File content does not match allowed types.`, variant: "destructive" });
    //   return false;
    // }

    return true;
  };

  const handleFileSelection = (file: File | null) => {
    if (file && handleFileValidation(file)) {
      setSelectedFile(file);
      setUploadState(null); // Reset upload state when new file selected
    } else {
      // Clear selection if validation fails or file is null
      setSelectedFile(null);
      setUploadState(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    handleFileSelection(file);
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files ? e.target.files[0] : null
    handleFileSelection(file);
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploadState({ status: "uploading", progress: 0 })

    const formData = new FormData()
    formData.append("file", selectedFile)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/api/dashboard/upload`, {
        method: "POST",
        body: formData,
        credentials: 'include',
        // No Content-Type header needed, browser sets it for FormData
      });

      // Simulate upload progress (replace with actual progress if available)
      // For simplicity, just jump to 25% on successful request start
      setUploadState((prev) => ({ ...prev!, progress: 25 }));

      const data = await response.json();

      if (!response.ok) {
        // Use error detail from backend response if available
        const errorMsg = data.detail || `Upload failed with status: ${response.status}`;
        throw new Error(errorMsg);
      }
      
      // Move to queued state, backend job_id received
      setUploadState((prev) => ({
        ...prev!,
        status: "queued",
        progress: 50,
        jobId: data.job_id
      }));
      
      toast({ title: "Upload Started", description: `File '${selectedFile.name}' is queued for processing.` });
      
      // Start polling for job status
      pollJobStatus(data.job_id, data.upload_id);

    } catch (error: any) {
      console.error("Upload error:", error);
      const errorMsg = error.message || "An unexpected error occurred during upload.";
      setUploadState((prev) => ({ ...prev!, status: "failed", error: errorMsg }));
      toast({ title: "Upload Error", description: errorMsg, variant: "destructive" });
      if (onUploadComplete) onUploadComplete(); // Notify parent on failure too
    }
  }

  const handleClearSelection = () => {
    resetState();
  }

  return (
    <Card className={cn("col-span-1", className)} {...props}>
      <CardHeader>
        <CardTitle>Upload Data</CardTitle>
        <CardDescription>Upload CSV or Excel files for analysis.</CardDescription>
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            "flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-md transition-colors",
            isDragging ? "border-primary bg-primary/10" : "border-border hover:border-primary/50",
            selectedFile || uploadState ? "border-primary/30" : ""
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {!selectedFile && !uploadState && (
            <>
              <Upload className="h-10 w-10 text-muted-foreground mb-4" />
              <p className="mb-2 text-sm">Drag & drop file here, or click to select</p>
              <p className="text-xs text-muted-foreground">(Max {MAX_FILE_SIZE_MB}MB, types: {ALLOWED_EXTENSIONS.join(", ")})</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={() => fileInputRef.current?.click()}>
                Select File
              </Button>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                accept={ALLOWED_EXTENSIONS.join(",")}
              />
            </>
          )}

          {selectedFile && !uploadState && (
            <div className="text-center">
              <p className="font-medium">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground mb-4">
                ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
              <div className="flex gap-2 justify-center">
                <Button onClick={handleUpload}>Upload File</Button>
                <Button variant="outline" size="icon" onClick={handleClearSelection}><X className="h-4 w-4" /></Button>
              </div>
            </div>
          )}

          {uploadState && selectedFile && (
            <div className="w-full">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium truncate max-w-[70%] text-muted-foreground" title={selectedFile.name}>{selectedFile.name}</p>
                {(uploadState.status === "completed" || uploadState.status === "failed") && (
                  <Button variant="ghost" size="sm" onClick={handleClearSelection}>Clear</Button>
                )}
              </div>
              <UploadProgress
                status={uploadState.status}
                progress={uploadState.progress}
                fileName={selectedFile.name}
                error={uploadState.error}
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

