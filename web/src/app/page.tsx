"use client";

import { MarketStatsWidget } from "@/features/orderbook/components/market-stats";
import { TopOfBook } from "@/features/orderbook/components/top-of-book";
import { DEFAULT_SYMBOL } from "@/lib/constants";

export default function HomePage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Public order book</h1>
      <p className="text-sm">
        Live top-of-book for {DEFAULT_SYMBOL}, polled from the Binance TH public
        API. No login required.
      </p>
      <MarketStatsWidget symbol={DEFAULT_SYMBOL} />
      <TopOfBook symbol={DEFAULT_SYMBOL} />
    </div>
  );
}

