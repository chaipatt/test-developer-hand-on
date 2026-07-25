import { z } from "zod";

// A single [price, quantity] level (both strings, as the exchange returns them).
export const levelSchema = z.array(z.string());

export const topOfBookSchema = z.object({
  symbol: z.string(),
  ts: z.string(),
  last_update_id: z.number().nullable(),
  best_bid: levelSchema.nullable(),
  best_ask: levelSchema.nullable(),
  spread: z.string().nullable(),
  bids: z.array(levelSchema),
  asks: z.array(levelSchema),
});

export const fullBookSchema = z.object({
  symbol: z.string(),
  ts: z.string(),
  last_update_id: z.number().nullable(),
  bids: z.array(levelSchema),
  asks: z.array(levelSchema),
});

export const marketStatsSchema = z.object({
  symbol: z.string(),
  price_change: z.string(),
  price_change_pct: z.string(),
  last_price: z.string(),
  high_price: z.string(),
  low_price: z.string(),
  volume: z.string(),
  quote_volume: z.string(),
  ts: z.string(),
});

export type TopOfBook = z.infer<typeof topOfBookSchema>;
export type FullBook = z.infer<typeof fullBookSchema>;
export type MarketStats = z.infer<typeof marketStatsSchema>;

