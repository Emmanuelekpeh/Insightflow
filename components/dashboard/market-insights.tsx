"use client"

import React, { useState, useEffect, useCallback } from "react"
import { format } from "date-fns" // Import date-fns for formatting
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import { AreaChart, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Area, CartesianGrid, XAxis, YAxis } from "recharts"
import { Skeleton } from "@/components/ui/skeleton" // Import Skeleton
import { AlertCircle } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

// Define interfaces matching backend schema
interface TrendDataPoint {
  collected_at: string; // ISO string
  score: number;
}

interface MarketInsightsData {
  trend_data: TrendDataPoint[];
  topTrendingTopic: string;
  growthRate: string;
}

interface MarketInsightsProps extends React.HTMLAttributes<HTMLDivElement> {}

export function MarketInsights({ className, ...props }: MarketInsightsProps) {
  const [data, setData] = useState<MarketInsightsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || ""
      const fetchUrl = `${apiUrl}/api/dashboard/market-insights`
      
      const response = await fetch(fetchUrl, {
        credentials: "include",
      })

      if (!response.ok) {
        let errorDetail = "Failed to fetch market insights."
        try {
          const errorData = await response.json()
          errorDetail = errorData.detail || `HTTP error! status: ${response.status}`
        } catch (jsonError) {
          errorDetail = `HTTP error! status: ${response.status}`
        }
        throw new Error(errorDetail)
      }
      
      const fetchedData: MarketInsightsData = await response.json()
      setData(fetchedData)
    } catch (err: any) {
      const errorMessage = err.message || "An unknown error occurred"
      setError(errorMessage)
      toast({
        title: "Error Fetching Market Insights",
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

  // Format data for the chart
  const chartData = data?.trend_data.map(item => ({
    month: format(new Date(item.collected_at), "MMM"), // Format date to month abbreviation
    trend: item.score, // Map score to 'trend' key
    // We don't have industry average data from backend yet
  })) || []

  return (
    <Card className={cn("col-span-3", className)} {...props}>
      <CardHeader>
        <CardTitle>Market Insights</CardTitle>
        <CardDescription>Track emerging trends based on your data.</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="trends">
          <TabsList className="mb-4">
            <TabsTrigger value="trends">Trends</TabsTrigger>
            {/* Keep other tabs but show placeholder content */}
            <TabsTrigger value="mentions" disabled={loading || !!error}>Mentions</TabsTrigger>
            <TabsTrigger value="growth" disabled={loading || !!error}>Growth</TabsTrigger>
          </TabsList>
          <TabsContent value="trends" className="space-y-4">
            {loading && (
              <>
                <Skeleton className="h-[300px] w-full" />
                <div className="grid grid-cols-2 gap-4">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </div>
              </>
            )}
            {error && (
              <div className="flex min-h-[300px] flex-col items-center justify-center rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
                <AlertCircle className="mb-2 h-6 w-6" />
                <p className="text-center font-medium">Error loading trends</p>
                <p className="text-center text-sm">{error}</p>
              </div>
            )}
            {!loading && !error && data && (
              <>
                <div className="h-[300px]">
                  <ChartContainer
                    config={{
                      trend: {
                        label: "Your Trend",
                        color: "hsl(var(--chart-1))",
                      },
                      // Remove industry config as we don't have the data
                    }}
                  >
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="month" tickLine={false} axisLine={false} />
                      <YAxis tickLine={false} axisLine={false} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Area
                        type="monotone"
                        dataKey="trend"
                        stroke="var(--color-trend)"
                        fill="var(--color-trend)"
                        fillOpacity={0.2}
                      />
                      {/* Remove Industry Area */}
                    </AreaChart>
                  </ChartContainer>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg border p-3">
                    <div className="text-sm font-medium text-muted-foreground">Top Trending Topic</div>
                    <div className="text-2xl font-bold">{data.topTrendingTopic || "N/A"}</div>
                  </div>
                  <div className="rounded-lg border p-3">
                    <div className="text-sm font-medium text-muted-foreground">Growth Rate</div>
                    <div className="text-2xl font-bold">{data.growthRate || "N/A"}</div>
                  </div>
                </div>
              </>
            )}
            {!loading && !error && !data && (
               <div className="flex min-h-[300px] items-center justify-center rounded-md border border-dashed p-6 text-center text-muted-foreground">
                 No trend data found. Upload data to see insights.
               </div>
            )}
          </TabsContent>
          <TabsContent value="mentions">
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              Mentions data will appear here (feature coming soon)
            </div>
          </TabsContent>
          <TabsContent value="growth">
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              Growth data will appear here (feature coming soon)
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

