"use client"

import type React from "react"
import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { FileUp, Upload, Loader2 } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { UploadProgress, type UploadStatus } from "@/components/ui/upload-progress"

interface UploadDataProps extends React.HTMLAttributes<HTMLDivElement> {}

interface UploadState {
  status: UploadStatus
  progress: number
  jobId?: string
  error?: string
}

const POLL_INTERVAL = 2000 // 2 seconds

export function UploadData({ className, ...props }: UploadDataProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadState, setUploadState] = useState<UploadState>({
    status: "uploading",
    progress: 0
  })
  const pollInterval = useRef<NodeJS.Timeout | undefined>(undefined)
  const { toast } = useToast()

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollInterval.current) {
        clearInterval(pollInterval.current)
      }
    }
  }, [])

  const pollJobStatus = async (jobId: string) => {
    try {
      const response = await fetch(`/api/dashboard/jobs/${jobId}/status`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Error checking job status")
      }

      // Update progress based on status
      switch (data.status) {
        case "completed":
          setUploadState(prev => ({ ...prev, status: "completed", progress: 100 }))
          if (pollInterval.current) {
            clearInterval(pollInterval.current)
          }
          toast({
            title: "Processing Complete",
            description: "Your file has been successfully processed."
          })
          // Clear the form after a delay
          setTimeout(() => {
            setSelectedFile(null)
            setUploadState({ status: "uploading", progress: 0 })
          }, 2000)
          break

        case "failed":
          setUploadState(prev => ({ 
            ...prev, 
            status: "failed", 
            error: data.message || "Processing failed"
          }))
          if (pollInterval.current) {
            clearInterval(pollInterval.current)
          }
          toast({
            title: "Processing Failed",
            description: data.message || "An error occurred while processing your file.",
            variant: "destructive"
          })
          break

        case "processing":
          setUploadState(prev => ({ ...prev, status: "processing", progress: 75 }))
          break

        case "queued":
          setUploadState(prev => ({ ...prev, status: "queued", progress: 50 }))
          break

        default:
          console.warn("Unknown job status:", data.status)
      }
    } catch (error) {
      console.error("Error polling job status:", error)
      // Don't stop polling on network errors, they might be temporary
    }
  }

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

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0]
      setSelectedFile(file)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload.",
        variant: "destructive",
      })
      return
    }

    // Reset upload state
    setUploadState({
      status: "uploading",
      progress: 0
    })

    const formData = new FormData()
    formData.append("file", selectedFile)

    try {
      // Start with upload progress simulation
      const progressInterval = setInterval(() => {
        setUploadState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 40) // Cap at 40% during upload
        }))
      }, 200)

      const response = await fetch("/api/dashboard/upload", {
        method: "POST",
        body: formData,
      })

      clearInterval(progressInterval)

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || "Upload failed")
      }

      // Update state to show queued status
      setUploadState({
        status: "queued",
        progress: 50,
        jobId: result.job_id
      })

      // Start polling for job status
      pollInterval.current = setInterval(() => {
        pollJobStatus(result.job_id)
      }, POLL_INTERVAL)

    } catch (error: any) {
      setUploadState({
        status: "failed",
        progress: 0,
        error: error.message || "An unexpected error occurred."
      })

      toast({
        title: "Upload Failed",
        description: error.message || "An unexpected error occurred.",
        variant: "destructive",
      })
    }
  }

  const handleClearSelection = () => {
    setSelectedFile(null)
    setUploadState({
      status: "uploading",
      progress: 0
    })
    if (pollInterval.current) {
      clearInterval(pollInterval.current)
    }
  }

  return (
    <Card className={cn("col-span-1", className)} {...props}>
      <CardHeader>
        <CardTitle>Upload Data</CardTitle>
        <CardDescription>Upload your sales data (CSV/Excel) for processing.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          className={cn(
            "flex flex-col items-center justify-center rounded-lg border border-dashed p-6 transition-colors",
            isDragging ? "border-primary bg-primary/5" : "border-muted-foreground/20",
            selectedFile ? "bg-muted/50" : "",
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {selectedFile ? (
            <div className="flex flex-col items-center space-y-2 text-center">
              <FileUp className="h-8 w-8 text-primary" />
              <p className="text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                ({(selectedFile.size / 1024).toFixed(1)} KB)
              </p>
              {uploadState.status === "uploading" && (
                <Button
                  variant="link"
                  size="sm"
                  className="text-xs text-destructive h-auto p-0"
                  onClick={handleClearSelection}
                >
                  Clear Selection
                </Button>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center space-y-2 text-center">
              <Upload className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium">Drag & drop your file here</p>
              <p className="text-xs text-muted-foreground">Supports CSV and Excel files</p>
              <label htmlFor="file-upload" className="mt-2">
                <span className="text-xs text-primary underline cursor-pointer">or browse files</span>
                <input
                  id="file-upload"
                  type="file"
                  className="sr-only"
                  accept=".csv,.xlsx,.xls,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  onChange={handleFileChange}
                  disabled={uploadState.status !== "uploading"}
                />
              </label>
            </div>
          )}
        </div>

        {selectedFile && (
          <UploadProgress
            status={uploadState.status}
            progress={uploadState.progress}
            fileName={selectedFile.name}
            error={uploadState.error}
          />
        )}
      </CardContent>
      {selectedFile && uploadState.status === "uploading" && (
        <CardFooter>
          <Button 
            className="w-full"
            onClick={handleUpload}
            disabled={uploadState.status !== "uploading"}
          >
            Upload and Analyze
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}

