"use client";

import { FullBook } from "@/features/orderbook/components/full-book";
import { DEFAULT_SYMBOL } from "@/lib/constants";

export default function DashboardPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <p className="text-sm">
        Full order-book depth for {DEFAULT_SYMBOL}. Visible to any signed-in user.
      </p>
      <FullBook symbol={DEFAULT_SYMBOL} />
    </div>
  );
}
