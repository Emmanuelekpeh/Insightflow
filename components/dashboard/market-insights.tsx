"use client"

import type React from "react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import { AreaChart, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Area, CartesianGrid, XAxis, YAxis } from "recharts"

interface MarketInsightsProps extends React.HTMLAttributes<HTMLDivElement> {}

export function MarketInsights({ className, ...props }: MarketInsightsProps) {
  const trendData = [
    { month: "Jan", trend: 65, industry: 40 },
    { month: "Feb", trend: 75, industry: 45 },
    { month: "Mar", trend: 85, industry: 48 },
    { month: "Apr", trend: 70, industry: 52 },
    { month: "May", trend: 90, industry: 55 },
    { month: "Jun", trend: 100, industry: 60 },
  ]

  return (
    <Card className={cn("col-span-3", className)} {...props}>
      <CardHeader>
        <CardTitle>Market Insights</CardTitle>
        <CardDescription>Track emerging trends in the health industry compared to industry average.</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="trends">
          <TabsList className="mb-4">
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="mentions">Mentions</TabsTrigger>
            <TabsTrigger value="growth">Growth</TabsTrigger>
          </TabsList>
          <TabsContent value="trends" className="space-y-4">
            <div className="h-[300px]">
              <ChartContainer
                config={{
                  trend: {
                    label: "Your Trend",
                    color: "hsl(var(--chart-1))",
                  },
                  industry: {
                    label: "Industry Average",
                    color: "hsl(var(--chart-2))",
                  },
                }}
              >
                <AreaChart data={trendData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
                  <Area
                    type="monotone"
                    dataKey="industry"
                    stroke="var(--color-industry)"
                    fill="var(--color-industry)"
                    fillOpacity={0.1}
                  />
                </AreaChart>
              </ChartContainer>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border p-3">
                <div className="text-sm font-medium text-muted-foreground">Top Trending Topic</div>
                <div className="text-2xl font-bold">Plant-based Supplements</div>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-sm font-medium text-muted-foreground">Growth Rate</div>
                <div className="text-2xl font-bold">+24.5%</div>
              </div>
            </div>
          </TabsContent>
          <TabsContent value="mentions">
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              Mentions data will appear here
            </div>
          </TabsContent>
          <TabsContent value="growth">
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              Growth data will appear here
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

