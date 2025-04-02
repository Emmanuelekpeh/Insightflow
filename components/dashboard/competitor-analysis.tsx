"use client"

import type React from "react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { BarChart, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Bar, CartesianGrid, XAxis, YAxis } from "recharts"
import { Badge } from "@/components/ui/badge"

interface CompetitorAnalysisProps extends React.HTMLAttributes<HTMLDivElement> {}

export function CompetitorAnalysis({ className, ...props }: CompetitorAnalysisProps) {
  const competitorData = [
    { name: "Your Company", value: 85 },
    { name: "Competitor A", value: 75, change: "up" },
    { name: "Competitor B", value: 65, change: "down" },
    { name: "Competitor C", value: 55, change: "up" },
    { name: "Competitor D", value: 45, change: "down" },
  ]

  const recentChanges = [
    {
      competitor: "Competitor A",
      change: "New product launch: Vitamin D3 + K2 Complex",
      date: "2 days ago",
    },
    {
      competitor: "Competitor B",
      change: "Price decrease on Omega-3 supplements by 15%",
      date: "5 days ago",
    },
    {
      competitor: "Competitor C",
      change: "New marketing campaign on social media",
      date: "1 week ago",
    },
  ]

  return (
    <Card className={cn("col-span-3", className)} {...props}>
      <CardHeader>
        <CardTitle>Competitor Analysis</CardTitle>
        <CardDescription>Monitor your competitors' market presence and recent activities.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-6 md:grid-cols-2">
          <div className="h-[250px]">
            <ChartContainer
              config={{
                value: {
                  label: "Market Presence Score",
                  color: "hsl(var(--chart-1))",
                },
              }}
            >
              <BarChart data={competitorData} layout="vertical" margin={{ top: 10, right: 10, left: 80, bottom: 0 }}>
                <CartesianGrid horizontal strokeDasharray="3 3" />
                <XAxis type="number" tickLine={false} axisLine={false} />
                <YAxis dataKey="name" type="category" tickLine={false} axisLine={false} width={70} />
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
          </div>
          <div>
            <h3 className="mb-4 text-lg font-medium">Recent Changes</h3>
            <div className="space-y-4">
              {recentChanges.map((item, index) => (
                <div key={index} className="rounded-lg border p-3">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline">{item.competitor}</Badge>
                    <span className="text-xs text-muted-foreground">{item.date}</span>
                  </div>
                  <p className="mt-2 text-sm">{item.change}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

