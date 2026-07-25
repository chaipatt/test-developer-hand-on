"use client";

import { useState } from "react";

import { ExchangeCompareWidget } from "@/features/admin/components/exchange-compare";
import { PollerStatusCard } from "@/features/admin/components/poller-status";
import { UsersTable } from "@/features/admin/components/users-table";
import { FullBook } from "@/features/orderbook/components/full-book";
import { DEFAULT_SYMBOL } from "@/lib/constants";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "exchange-compare", label: "Exchange Compare" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function AdminPage() {
  const [tab, setTab] = useState<TabId>("overview");

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Admin</h1>
      <p className="text-sm">
        Everything a user sees, plus admin-only views. Admin role required.
      </p>

      <nav className="flex gap-2 border-b border-current" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`px-3 py-2 text-sm -mb-px border-b-2 ${
              tab === t.id
                ? "border-current font-semibold"
                : "border-transparent opacity-70 hover:opacity-100"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <div className="space-y-6">
          <section className="space-y-2">
            <h2 className="font-semibold">Poller status</h2>
            <PollerStatusCard />
          </section>

          <section className="space-y-2">
            <h2 className="font-semibold">Users</h2>
            <UsersTable />
          </section>

          <section className="space-y-2">
            <h2 className="font-semibold">Full order book ({DEFAULT_SYMBOL})</h2>
            <FullBook symbol={DEFAULT_SYMBOL} />
          </section>
        </div>
      )}

      {tab === "exchange-compare" && (
        <section className="space-y-2">
          <h2 className="font-semibold">Exchange comparison (Binance TH vs Bitkub)</h2>
          <ExchangeCompareWidget />
        </section>
      )}
    </div>
  );
}
