import { useQuery } from "@tanstack/react-query";
import { apiService } from "../services/api";
import type { DiscoveryResponse } from "../types";

export function useDiscovery() {
  return useQuery<DiscoveryResponse | null>({
    queryKey: ["discovery"],
    queryFn: async () => {
      try {
        const cachedData = await apiService.discoverCached();
        if (cachedData) return cachedData;
        // Fallback if cache is empty
        const todayData = await apiService.discoverToday();
        return todayData;
      } catch (error: unknown) {
        const requestError = error as { response?: { status?: number } };
        // A cache miss is expected; the live endpoint is the fallback.
        if (requestError.response?.status === 404) {
          return apiService.discoverToday();
        }
        throw error;
      }
    },
    staleTime: Infinity, // Ensure memory-only cache; no automatic background refetches
    refetchOnWindowFocus: false,
  });
}
