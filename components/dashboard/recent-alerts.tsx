import React, { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { Bell, TrendingUp, Users, Zap, AlertCircle, HelpCircle } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { useToast } from "@/hooks/use-toast"

// Interface matching backend AlertItem schema
interface AlertItem {
  type: string; // "trend", "competitor", "sentiment"
  title: string;
  description: string;
  time: string;
}

// Interface for the API response
interface RecentAlertsData {
  alerts: AlertItem[];
}

interface RecentAlertsProps extends React.HTMLAttributes<HTMLDivElement> {}

// Helper function to map alert type to icon and color
const getAlertStyle = (type: string) => {
  switch (type.toLowerCase()) {
    case "trend":
      return { Icon: TrendingUp, color: "text-green-500" };
    case "sentiment":
      return { Icon: Zap, color: "text-blue-500" };
    case "competitor": // Keep competitor style
      return { Icon: Users, color: "text-amber-500" };
    case "keyword": // Add new case for keyword alerts
      return { Icon: Users, color: "text-amber-500" }; // Reuse competitor style for MVP
    default:
      return { Icon: HelpCircle, color: "text-muted-foreground" }; // Default fallback
  }
}

export function RecentAlerts({ className, ...props }: RecentAlertsProps) {
  const [data, setData] = useState<RecentAlertsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || ""
      const fetchUrl = `${apiUrl}/api/dashboard/recent-alerts`
      
      const response = await fetch(fetchUrl, {
        credentials: "include",
      })

      if (!response.ok) {
        let errorDetail = "Failed to fetch recent alerts."
        try {
          const errorData = await response.json()
          errorDetail = errorData.detail || `HTTP error! status: ${response.status}`
        } catch (jsonError) {
          errorDetail = `HTTP error! status: ${response.status}`
        }
        throw new Error(errorDetail)
      }
      
      const fetchedData: RecentAlertsData = await response.json()
      setData(fetchedData)
    } catch (err: any) {
      const errorMessage = err.message || "An unknown error occurred"
      setError(errorMessage)
      toast({
        title: "Error Fetching Alerts",
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
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle>Recent Alerts</CardTitle>
          <CardDescription>Important updates and notifications.</CardDescription>
        </div>
        <Bell className="h-5 w-5 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-start space-x-3 rounded-lg border p-3">
                <Skeleton className="h-5 w-5 rounded-full" />
                <div className="flex-1 space-y-1">
                  <Skeleton className="h-4 w-3/5" />
                  <Skeleton className="h-4 w-4/5" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              </div>
            ))}
          </div>
        )}
        {error && (
           <div className="flex min-h-[150px] flex-col items-center justify-center rounded-md border border-destructive/50 bg-destructive/10 p-4 text-destructive">
             <AlertCircle className="mb-2 h-6 w-6" />
             <p className="text-center font-medium">Error loading alerts</p>
             <p className="text-center text-sm">{error}</p>
           </div>
        )}
        {!loading && !error && data && data.alerts.length > 0 && (
          <div className="space-y-4">
            {data.alerts.map((alert, index) => {
              const { Icon, color } = getAlertStyle(alert.type);
              return (
                <div key={index} className="flex items-start space-x-3 rounded-lg border p-3">
                  <Icon className={cn("mt-0.5 h-5 w-5 flex-shrink-0", color)} />
                  <div className="space-y-1 overflow-hidden">
                    <p className="text-sm font-medium leading-none truncate" title={alert.title}>{alert.title}</p>
                    <p className="text-sm text-muted-foreground truncate" title={alert.description}>{alert.description}</p>
                    <p className="text-xs text-muted-foreground">{alert.time}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        {!loading && !error && (!data || data.alerts.length === 0) && (
          <div className="flex min-h-[150px] items-center justify-center rounded-md border border-dashed p-6 text-center text-muted-foreground">
            No recent alerts found.
          </div>
        )}
      </CardContent>
    </Card>
  )
}

