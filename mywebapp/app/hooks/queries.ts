import { useQuery } from "@tanstack/react-query";
import { client } from "~/client";

export function useMmfStatus() {
  return useQuery({
    queryFn: () => client.GET("/api/mmf/status"),
    queryKey: ["mmf", "status"],
  });
}
