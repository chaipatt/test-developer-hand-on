import { useQuery } from "@tanstack/react-query";

import { fetchFullBook, fetchMarketStats, fetchTopOfBook } from "./api";

// The book refreshes every few seconds; poll a little faster than the backend.
const REFETCH_MS = 3000;

export function useTopOfBook(symbol: string) {
  return useQuery({
    queryKey: ["orderbook", "top", symbol],
    queryFn: () => fetchTopOfBook(symbol),
    refetchInterval: REFETCH_MS,
    retry: false,
  });
}

export function useFullBook(symbol: string) {
  return useQuery({
    queryKey: ["orderbook", "full", symbol],
    queryFn: () => fetchFullBook(symbol),
    refetchInterval: REFETCH_MS,
    retry: false,
  });
}

export function useMarketStats(symbol: string) {
  return useQuery({
    queryKey: ["market-stats", symbol],
    queryFn: () => fetchMarketStats(symbol),
    refetchInterval: REFETCH_MS,
    retry: false,
  });
}

