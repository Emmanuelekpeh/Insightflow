"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

// Interface matching the backend SentimentAnalysisResponse schema
interface SentimentTopic {
  name: string;
  sentiment: number;
}

interface SentimentAnalysisData {
  positive: number;
  neutral: number;
  negative: number;
  topics: SentimentTopic[];
}

interface SentimentAnalysisProps extends React.HTMLAttributes<HTMLDivElement> {}

export function SentimentAnalysis({ className, ...props }: SentimentAnalysisProps) {
  const [data, setData] = useState<SentimentAnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || ""
      const fetchUrl = `${apiUrl}/api/dashboard/sentiment-analysis`
      
      const response = await fetch(fetchUrl, {
        credentials: "include",
      })

      if (!response.ok) {
        let errorDetail = "Failed to fetch sentiment analysis."
        try {
          const errorData = await response.json()
          errorDetail = errorData.detail || `HTTP error! status: ${response.status}`
        } catch (jsonError) {
          errorDetail = `HTTP error! status: ${response.status}`
        }
        throw new Error(errorDetail)
      }
      
      const fetchedData: SentimentAnalysisData = await response.json()
      setData(fetchedData)
    } catch (err: any) {
      const errorMessage = err.message || "An unknown error occurred"
      setError(errorMessage)
      toast({
        title: "Error Fetching Sentiment",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return (
    <Card className={cn("col-span-1", className)} {...props}>
      <CardHeader>
        <CardTitle>Sentiment Analysis</CardTitle>
        <CardDescription>Sentiment across your uploaded data.</CardDescription>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="space-y-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-5 w-1/3" />
                <Skeleton className="h-2 w-full" />
              </div>
            ))}
            <div className="pt-4">
              <Skeleton className="h-5 w-1/4 mb-3" />
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <Skeleton className="h-4 w-2/5" />
                      <Skeleton className="h-4 w-1/5" />
                    </div>
                    <Skeleton className="h-1.5 w-full" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {error && (
          <div className="flex min-h-[200px] flex-col items-center justify-center rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
            <AlertCircle className="mb-2 h-6 w-6" />
            <p className="text-center font-medium">Error loading sentiment</p>
            <p className="text-center text-sm">{error}</p>
          </div>
        )}
        {!loading && !error && data && (
          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Positive</div>
                <div className="text-sm font-medium text-green-500">{data.positive}%</div>
              </div>
              <Progress value={data.positive} className="h-2 bg-muted" indicatorClassName="bg-green-500" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Neutral</div>
                <div className="text-sm font-medium text-amber-500">{data.neutral}%</div>
              </div>
              <Progress value={data.neutral} className="h-2 bg-muted" indicatorClassName="bg-amber-500" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Negative</div>
                <div className="text-sm font-medium text-red-500">{data.negative}%</div>
              </div>
              <Progress value={data.negative} className="h-2 bg-muted" indicatorClassName="bg-red-500" />
            </div>
            {data.topics && data.topics.length > 0 ? (
              <div className="pt-4">
                <h4 className="mb-3 text-sm font-medium">Sentiment by Topic</h4>
                <div className="space-y-3">
                  {data.topics.map((topic, index) => (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="truncate max-w-[70%]" title={topic.name}>{topic.name}</span>
                        <span
                          className={cn(
                            "font-semibold",
                            topic.sentiment > 70
                              ? "text-green-500"
                              : topic.sentiment > 50
                                ? "text-amber-500"
                                : "text-red-500",
                          )}
                        >
                          {topic.sentiment}%
                        </span>
                      </div>
                      <Progress
                        value={topic.sentiment}
                        className="h-1.5 bg-muted"
                        indicatorClassName={cn(
                          topic.sentiment > 70 ? "bg-green-500" : topic.sentiment > 50 ? "bg-amber-500" : "bg-red-500",
                        )}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
               <div className="pt-4 text-center text-sm text-muted-foreground">
                 No specific topics found.
               </div>
            )}
          </div>
        )}
         {!loading && !error && !data && (
           <div className="flex min-h-[200px] items-center justify-center rounded-md border border-dashed p-6 text-center text-muted-foreground">
             No sentiment data found. Upload data to see insights.
           </div>
         )}
      </CardContent>
    </Card>
  )
}

