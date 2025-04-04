"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { BarChart, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Bar, CartesianGrid, XAxis, YAxis } from "recharts"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

// Interfaces matching backend schema
interface CompetitorDataPoint {
  name: string;
  value: number;
  change?: string | null; // MVP has null
}

interface RecentChange {
  competitor: string;
  change: string;
  date: string;
}

interface CompetitorAnalysisData {
  competitorData: CompetitorDataPoint[];
  recentChanges: RecentChange[]; // MVP is empty list
}

interface CompetitorAnalysisProps extends React.HTMLAttributes<HTMLDivElement> {}

export function CompetitorAnalysis({ className, ...props }: CompetitorAnalysisProps) {
  const [data, setData] = useState<CompetitorAnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || ""
      const fetchUrl = `${apiUrl}/api/dashboard/competitor-analysis`
      
      const response = await fetch(fetchUrl, {
        credentials: "include",
      })

      if (!response.ok) {
        let errorDetail = "Failed to fetch competitor analysis."
        try {
          const errorData = await response.json()
          errorDetail = errorData.detail || `HTTP error! status: ${response.status}`
        } catch (jsonError) {
          errorDetail = `HTTP error! status: ${response.status}`
        }
        throw new Error(errorDetail)
      }
      
      const fetchedData: CompetitorAnalysisData = await response.json()
      setData(fetchedData)
    } catch (err: any) {
      const errorMessage = err.message || "An unknown error occurred"
      setError(errorMessage)
      toast({
        title: "Error Fetching Competitor Data",
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
    <Card className={cn("col-span-3", className)} {...props}>
      <CardHeader>
        <CardTitle>Competitor Analysis</CardTitle>
        <CardDescription>Top keywords by frequency from your data (MVP). Actual competitor tracking coming soon.</CardDescription>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="grid gap-6 md:grid-cols-2">
            <Skeleton className="h-[250px] w-full" />
            <div>
              <Skeleton className="h-6 w-1/3 mb-4" />
              <div className="space-y-4">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            </div>
          </div>
        )}
        {error && (
           <div className="flex min-h-[250px] flex-col items-center justify-center rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
             <AlertCircle className="mb-2 h-6 w-6" />
             <p className="text-center font-medium">Error loading competitor data</p>
             <p className="text-center text-sm">{error}</p>
           </div>
        )}
        {!loading && !error && data && (
          <div className="grid gap-6 md:grid-cols-2">
            <div className="h-[250px]">
              {data.competitorData && data.competitorData.length > 0 ? (
                <ChartContainer
                  config={{
                    value: {
                      label: "Frequency",
                      color: "hsl(var(--chart-1))",
                    },
                  }}
                >
                  <BarChart data={data.competitorData} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
                    <CartesianGrid horizontal strokeDasharray="3 3" />
                    <XAxis type="number" tickLine={false} axisLine={false} />
                    <YAxis 
                      dataKey="name" 
                      type="category" 
                      tickLine={false} 
                      axisLine={false} 
                      width={150}
                      tick={{ fontSize: 12 }} 
                      label={{ value: 'Top Keywords (Proxy)', angle: -90, position: 'insideLeft', offset: -10, style: { textAnchor: 'middle', fill: 'hsl(var(--muted-foreground))', fontSize: 12 } }}
                    />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar
                      dataKey="value"
                      fill="var(--color-value)"
                      radius={4}
                      barSize={20}
                      label={{ position: "right", formatter: (value: number) => `${value}` }}
                    />
                  </BarChart>
                </ChartContainer>
              ) : (
                <div className="flex h-full items-center justify-center rounded-md border border-dashed p-6 text-center text-muted-foreground">
                  No competitor/keyword data found.
                </div>
              )}
            </div>
            <div>
              <h3 className="mb-4 text-lg font-medium">Recent Changes (Coming Soon)</h3>
              <div className="space-y-4">
                {data.recentChanges && data.recentChanges.length > 0 ? (
                  data.recentChanges.map((item, index) => (
                    <div key={index} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <Badge variant="outline">{item.competitor}</Badge>
                        <span className="text-xs text-muted-foreground">{item.date}</span>
                      </div>
                      <p className="mt-2 text-sm">{item.change}</p>
                    </div>
                  ))
                ) : (
                  <div className="flex h-[150px] items-center justify-center rounded-md border border-dashed p-6 text-center text-muted-foreground">
                    No recent competitor changes detected yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        {!loading && !error && !data && (
           <div className="flex min-h-[250px] items-center justify-center rounded-md border border-dashed p-6 text-center text-muted-foreground">
             No competitor data found. Upload data to see insights.
           </div>
        )}
      </CardContent>
    </Card>
  )
}

