import { z } from "zod";

export const adminUserSchema = z.object({
  id: z.number(),
  email: z.string(),
  role: z.string(),
  is_active: z.boolean(),
  description: z.string(),
  created_at: z.string(),
});

export const pollerStatusSchema = z.object({
  running: z.boolean(),
  symbols: z.array(z.string()),
  poll_interval_seconds: z.number().optional(),
  poll_count: z.number().optional(),
  last_poll_ts: z.string().nullable().optional(),
  last_error: z.string().nullable().optional(),
});

// One exchange's live view of a pair; numeric fields are strings (exact
// precision from the backend) and nullable when a side is unavailable.
export const exchangeQuoteSchema = z.object({
  exchange: z.string(),
  last_price: z.string().nullable(),
  price_change_pct: z.string().nullable(),
  quote_volume: z.string().nullable(),
  best_bid: z.string().nullable(),
  best_ask: z.string().nullable(),
  spread_pct: z.string().nullable(),
  error: z.string().nullable().optional(),
});

export const exchangeComparisonSchema = z.object({
  symbol: z.string(),
  binance: exchangeQuoteSchema,
  bitkub: exchangeQuoteSchema,
  arbitrage_spread_pct: z.string().nullable(),
});

export const exchangeCompareSchema = z.object({
  generated_at: z.string(),
  pairs: z.array(exchangeComparisonSchema),
});

export type AdminUser = z.infer<typeof adminUserSchema>;
export type PollerStatus = z.infer<typeof pollerStatusSchema>;
export type ExchangeQuote = z.infer<typeof exchangeQuoteSchema>;
export type ExchangeComparison = z.infer<typeof exchangeComparisonSchema>;
export type ExchangeCompare = z.infer<typeof exchangeCompareSchema>;
