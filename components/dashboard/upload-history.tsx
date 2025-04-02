"use client"

import React, { useEffect, useState } from "react"
import { format } from "date-fns"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { AlertCircle, CheckCircle2, Clock, XCircle } from "lucide-react"

// Define the structure of an upload result based on the backend schema
interface UploadResult {
  id: string; // Primary key (UUID as string)
  job_id: string; // Job UUID
  original_filename: string | null;
  status: string | null; // 'queued', 'processing', 'completed', 'failed'
  created_at: string; // ISO string format
  updated_at: string; // ISO string format
  row_count: number | null;
  column_count: number | null;
  headers: string[] | null; // Assuming JSON is parsed to array by the API or here
  error_reason: string | null;
}

interface UploadHistoryProps extends React.HTMLAttributes<HTMLDivElement> {}

export function UploadHistory({ className, ...props }: UploadHistoryProps) {
  const [uploads, setUploads] = useState<UploadResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchUploads = async () => {
      setLoading(true)
      setError(null)
      try {
        // Use relative path for proxied API endpoint
        const response = await fetch("/api/dashboard/uploads", {
           credentials: 'include', // Include cookies for authentication
        })
        if (!response.ok) {
           const errorData = await response.json().catch(() => ({ detail: "Failed to fetch upload history." }))
           throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        // Assuming the API returns { uploads: [...] } based on UploadResultList schema
        setUploads(data.uploads || [])
      } catch (err: any) {
        console.error("Failed to fetch uploads:", err)
        setError(err.message || "An unknown error occurred")
      } finally {
        setLoading(false)
      }
    }

    fetchUploads()
    // Consider adding polling or a refresh mechanism later if needed
  }, []) // Empty dependency array ensures this runs once on mount


  const getStatusBadge = (status: string | null) => {
    switch (status) {
      case "completed":
        return <Badge variant="default" className="bg-green-500 hover:bg-green-600"><CheckCircle2 className="mr-1 h-3 w-3" /> Completed</Badge>
      case "processing":
        return <Badge variant="secondary" className="bg-blue-500 text-white hover:bg-blue-600"><Clock className="mr-1 h-3 w-3" /> Processing</Badge>
      case "queued":
        return <Badge variant="secondary" className="bg-yellow-500 text-white hover:bg-yellow-600"><Clock className="mr-1 h-3 w-3" /> Queued</Badge>
      case "failed":
        return <Badge variant="destructive"><XCircle className="mr-1 h-3 w-3" /> Failed</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  return (
    <Card className={cn("col-span-full", className)} {...props}>
      <CardHeader>
        <CardTitle>Upload History</CardTitle>
        <CardDescription>View the status and results of your recent data uploads.</CardDescription>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}
        {error && (
          <div className="flex items-center justify-center rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
            <AlertCircle className="mr-2 h-4 w-4" /> {error}
          </div>
        )}
        {!loading && !error && uploads.length === 0 && (
          <div className="flex items-center justify-center rounded-md border border-dashed p-6 text-center text-muted-foreground">
            No uploads found yet. Upload a file to get started.
          </div>
        )}
        {!loading && !error && uploads.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Filename</TableHead>
                <TableHead>Uploaded At</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Rows</TableHead>
                <TableHead className="text-right">Cols</TableHead>
                <TableHead>Error</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {uploads.map((upload) => (
                <TableRow key={upload.id}>
                  <TableCell className="font-medium">{upload.original_filename || "N/A"}</TableCell>
                  <TableCell>{format(new Date(upload.created_at), "PPpp")}</TableCell>
                  <TableCell>{getStatusBadge(upload.status)}</TableCell>
                  <TableCell className="text-right">{upload.row_count ?? "-"}</TableCell>
                  <TableCell className="text-right">{upload.column_count ?? "-"}</TableCell>
                  <TableCell className="max-w-xs truncate text-xs text-destructive" title={upload.error_reason || undefined}>
                     {upload.error_reason || "-"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
} 