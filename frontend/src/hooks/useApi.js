import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "@/lib/api";

// ── Inventory ──

export function useInventory(params) {
  return useQuery({
    queryKey: ["inventory", params],
    queryFn: () => api.inventory.list(params).then((r) => r.data),
  });
}

export function useInventoryItem(id) {
  return useQuery({
    queryKey: ["inventory", id],
    queryFn: () => api.inventory.get(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateInventoryItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => api.inventory.create(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inventory"] }),
  });
}

export function useUpdateInventoryItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }) => api.inventory.update(id, data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inventory"] }),
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () => api.inventory.categories().then((r) => r.data),
  });
}

// ── Projects ──

export function useProjects(params) {
  return useQuery({
    queryKey: ["projects", params],
    queryFn: () => api.projects.list(params).then((r) => r.data),
  });
}

export function useProject(id) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => api.projects.get(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => api.projects.create(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useChangeStage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, stage }) => api.projects.changeStage(id, stage).then((r) => r.data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ["project", id] });
      qc.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useAddLineItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, data }) => api.projects.addItem(projectId, data).then((r) => r.data),
    onSuccess: (_, { projectId }) => qc.invalidateQueries({ queryKey: ["project", projectId] }),
  });
}

// ── Clients ──

export function useClients(params) {
  return useQuery({
    queryKey: ["clients", params],
    queryFn: () => api.clients.list(params).then((r) => r.data),
  });
}

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => api.clients.create(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clients"] }),
  });
}

// ── Payments ──

export function usePayments(params) {
  return useQuery({
    queryKey: ["payments", params],
    queryFn: () => api.payments.list(params).then((r) => r.data),
  });
}

// ── Dispatch ──

export function useVehicles() {
  return useQuery({
    queryKey: ["vehicles"],
    queryFn: () => api.dispatch.vehicles().then((r) => r.data),
  });
}

export function useRoutes(params) {
  return useQuery({
    queryKey: ["routes", params],
    queryFn: () => api.dispatch.routes(params).then((r) => r.data),
  });
}

export function useAutoRoute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (routeId) => api.dispatch.autoRoute(routeId).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["routes"] }),
  });
}

// ── Messages ──

export function useMessages(params) {
  return useQuery({
    queryKey: ["messages", params],
    queryFn: () => api.messages.list(params).then((r) => r.data),
  });
}

export function useSendMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => api.messages.send(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["messages"] }),
  });
}

// ── Website ──

export function useWishlists(params) {
  return useQuery({
    queryKey: ["wishlists", params],
    queryFn: () => api.website.wishlists(params).then((r) => r.data),
  });
}

// ── Dashboard ──

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.dashboard.stats().then((r) => r.data),
    refetchInterval: 60000, // Refresh every minute
  });
}

export function useRevenueReport(params) {
  return useQuery({
    queryKey: ["revenue", params],
    queryFn: () => api.dashboard.revenue(params).then((r) => r.data),
  });
}

export function usePipeline() {
  return useQuery({
    queryKey: ["pipeline"],
    queryFn: () => api.dashboard.pipeline().then((r) => r.data),
  });
}

// ── Activity ──

export function useActivity(params) {
  return useQuery({
    queryKey: ["activity", params],
    queryFn: () => api.activity.list(params).then((r) => r.data),
  });
}
