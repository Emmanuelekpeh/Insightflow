import type React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Bell, TrendingUp, Users, Zap } from "lucide-react"

interface RecentAlertsProps extends React.HTMLAttributes<HTMLDivElement> {}

export function RecentAlerts({ className, ...props }: RecentAlertsProps) {
  const alerts = [
    {
      icon: TrendingUp,
      title: "Trending Topic Alert",
      description: "Gut health is trending 45% above average",
      time: "2 hours ago",
      color: "text-green-500",
    },
    {
      icon: Users,
      title: "Competitor Alert",
      description: "Competitor A launched a new product line",
      time: "1 day ago",
      color: "text-amber-500",
    },
    {
      icon: Zap,
      title: "Sentiment Shift",
      description: "Positive sentiment increased by 12%",
      time: "3 days ago",
      color: "text-blue-500",
    },
  ]

  return (
    <Card className={cn("col-span-1", className)} {...props}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle>Recent Alerts</CardTitle>
          <CardDescription>Important updates and notifications.</CardDescription>
        </div>
        <Bell className="h-5 w-5 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {alerts.map((alert, index) => (
            <div key={index} className="flex items-start space-x-3 rounded-lg border p-3">
              <alert.icon className={cn("mt-0.5 h-5 w-5", alert.color)} />
              <div className="space-y-1">
                <p className="text-sm font-medium leading-none">{alert.title}</p>
                <p className="text-sm text-muted-foreground">{alert.description}</p>
                <p className="text-xs text-muted-foreground">{alert.time}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

