"use client"

import type React from "react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Progress } from "@/components/ui/progress"

interface SentimentAnalysisProps extends React.HTMLAttributes<HTMLDivElement> {}

export function SentimentAnalysis({ className, ...props }: SentimentAnalysisProps) {
  const sentimentData = {
    positive: 68,
    neutral: 22,
    negative: 10,
    topics: [
      { name: "Customer Service", sentiment: 85 },
      { name: "Product Quality", sentiment: 75 },
      { name: "Pricing", sentiment: 45 },
      { name: "Delivery", sentiment: 60 },
    ],
  }

  return (
    <Card className={cn("col-span-1", className)} {...props}>
      <CardHeader>
        <CardTitle>Sentiment Analysis</CardTitle>
        <CardDescription>Customer sentiment across social media and forums.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Positive</div>
              <div className="text-sm font-medium text-green-500">{sentimentData.positive}%</div>
            </div>
            <Progress value={sentimentData.positive} className="h-2 bg-muted" indicatorClassName="bg-green-500" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Neutral</div>
              <div className="text-sm font-medium text-amber-500">{sentimentData.neutral}%</div>
            </div>
            <Progress value={sentimentData.neutral} className="h-2 bg-muted" indicatorClassName="bg-amber-500" />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Negative</div>
              <div className="text-sm font-medium text-red-500">{sentimentData.negative}%</div>
            </div>
            <Progress value={sentimentData.negative} className="h-2 bg-muted" indicatorClassName="bg-red-500" />
          </div>
          <div className="pt-4">
            <h4 className="mb-3 text-sm font-medium">Sentiment by Topic</h4>
            <div className="space-y-3">
              {sentimentData.topics.map((topic, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span>{topic.name}</span>
                    <span
                      className={cn(
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
        </div>
      </CardContent>
    </Card>
  )
}

