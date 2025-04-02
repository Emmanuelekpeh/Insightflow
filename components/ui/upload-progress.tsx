"use client"

import * as React from "react"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react"

export type UploadStatus = "uploading" | "processing" | "completed" | "failed" | "queued"

interface UploadProgressProps {
  status: UploadStatus
  progress: number
  fileName: string
  error?: string
}

export function UploadProgress({ status, progress, fileName, error }: UploadProgressProps) {
  const getStatusConfig = () => {
    switch (status) {
      case "uploading":
        return {
          label: "Uploading...",
          color: "bg-primary",
          icon: Loader2,
          iconClass: "animate-spin text-primary"
        }
      case "queued":
        return {
          label: "In Queue...",
          color: "bg-amber-500",
          icon: Loader2,
          iconClass: "animate-spin text-amber-500"
        }
      case "processing":
        return {
          label: "Processing...",
          color: "bg-blue-500",
          icon: Loader2,
          iconClass: "animate-spin text-blue-500"
        }
      case "completed":
        return {
          label: "Completed",
          color: "bg-green-500",
          icon: CheckCircle2,
          iconClass: "text-green-500"
        }
      case "failed":
        return {
          label: "Failed",
          color: "bg-destructive",
          icon: AlertCircle,
          iconClass: "text-destructive"
        }
    }
  }

  const config = getStatusConfig()

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <config.icon className={cn("h-4 w-4", config.iconClass)} />
        <span className="text-sm">{config.label}</span>
      </div>
      <Progress 
        value={progress} 
        className="h-2" 
        indicatorClassName={cn(
          status === "failed" ? "bg-destructive" : config.color
        )} 
      />
      {error && status === "failed" && (
        <p className="text-xs text-destructive">{error}</p>
      )}
    </div>
  )
}