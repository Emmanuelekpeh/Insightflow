"use client"

import React, { useState, useCallback } from 'react';
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { MarketInsights } from "@/components/dashboard/market-insights"
import { CompetitorAnalysis } from "@/components/dashboard/competitor-analysis"
import { SentimentAnalysis } from "@/components/dashboard/sentiment-analysis"
import { RecentAlerts } from "@/components/dashboard/recent-alerts"
import { UploadData } from "@/components/dashboard/upload-data"
import { UploadHistory } from "@/components/dashboard/upload-history"

export default function DashboardPage() {
  const [historyKey, setHistoryKey] = useState(0);

  const handleUploadComplete = useCallback(() => {
    setHistoryKey(prevKey => prevKey + 1);
  }, []);

  return (
    <DashboardShell>
      <DashboardHeader heading="Dashboard" text="View your market insights, competitor analysis, and sentiment data." />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <MarketInsights className="lg:col-span-2" />
        <SentimentAnalysis />
        <CompetitorAnalysis className="md:col-span-2 lg:col-span-2" />
        <RecentAlerts />
        <UploadData onUploadComplete={handleUploadComplete} />
        <UploadHistory className="md:col-span-2 lg:col-span-3" refreshTrigger={historyKey} />
      </div>
    </DashboardShell>
  )
}

