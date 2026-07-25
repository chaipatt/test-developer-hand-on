import { useQuery } from "@tanstack/react-query";

import { fetchExchangeCompare, fetchPollerStatus, fetchUsers } from "./api";

export function useAdminUsers() {
  return useQuery({
    queryKey: ["admin", "users"],
    queryFn: fetchUsers,
    retry: false,
  });
}

export function usePollerStatus() {
  return useQuery({
    queryKey: ["admin", "poller-status"],
    queryFn: fetchPollerStatus,
    refetchInterval: 5000,
    retry: false,
  });
}

export function useExchangeCompare() {
  return useQuery({
    queryKey: ["admin", "exchange-compare"],
    queryFn: fetchExchangeCompare,
    refetchInterval: 5000,
    retry: false,
  });
}
