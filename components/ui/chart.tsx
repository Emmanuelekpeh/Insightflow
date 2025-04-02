"use client"

import type React from "react"

import { cn } from "@/lib/utils"
import { AreaChart as RechartsAreaChart, BarChart as RechartsBarChart, Tooltip as RechartsTooltip, TooltipProps as RechartsTooltipProps } from "recharts"

interface ChartContainerProps {
  children: React.ReactNode
  config: Record<string, { label: string; color: string }>
  className?: string
}

export function ChartContainer({ children, config, className }: ChartContainerProps) {
  // Set CSS variables for colors
  const style = Object.entries(config).reduce(
    (acc, [key, value]) => {
      acc[`--color-${key}`] = value.color
      return acc
    },
    {} as Record<string, string>,
  )

  return (
    <div className={cn("w-full", className)} style={style}>
      {children}
    </div>
  )
}

interface ChartTooltipProps extends RechartsTooltipProps<any, any> {
  hideLabel?: boolean;
  indicator?: "dot" | "line";
  cursor?: boolean | object;
}

export function ChartTooltip({ 
  hideLabel, 
  indicator, 
  cursor = true, 
  ...props
}: ChartTooltipProps) {
  const renderTooltipContent = (tooltipRenderProps: RechartsTooltipProps<any, any>) => {
    return (
      <ChartTooltipContent
        {...tooltipRenderProps}
        hideLabel={hideLabel}
        indicator={indicator}
      />
    );
  };

  return <RechartsTooltip content={renderTooltipContent} cursor={cursor} {...props} />;
}

interface ChartTooltipContentProps {
  active?: boolean
  payload?: any[]
  label?: string
  hideLabel?: boolean
  indicator?: "dot" | "line"
}

export function ChartTooltipContent({
  active,
  payload,
  label,
  hideLabel = false,
  indicator = "dot",
}: ChartTooltipContentProps) {
  if (!active || !payload || !payload.length) {
    return null
  }

  return (
    <div className="rounded-md border bg-background p-2 shadow-md">
      {!hideLabel && label && <p className="mb-2 text-sm font-medium">{label}</p>}
      <div className="flex flex-col gap-1">
        {payload.map((item, index) => {
          // Skip items with no value
          if (item.value === undefined) return null

          return (
            <div key={index} className="flex items-center gap-2">
              {indicator === "dot" && <div className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />}
              {indicator === "line" && <div className="h-2 w-4" style={{ backgroundColor: item.color }} />}
              <span className="text-xs font-medium">{item.name}:</span>
              <span className="text-xs">{item.value}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export { RechartsBarChart as BarChart, RechartsAreaChart as AreaChart }

