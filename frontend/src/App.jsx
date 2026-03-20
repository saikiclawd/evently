import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import useAuthStore from "@/store/authStore";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import InventoryPage from "@/pages/InventoryPage";
import ProjectsPage from "@/pages/ProjectsPage";
import ClientsPage from "@/pages/ClientsPage";
import ProposalsPage from "@/pages/ProposalsPage";
import PaymentsPage from "@/pages/PaymentsPage";
import DispatchPage from "@/pages/DispatchPage";
import CalendarPage from "@/pages/CalendarPage";
import ReportsPage from "@/pages/ReportsPage";
import WebsitePage from "@/pages/WebsitePage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthStore();
  if (isLoading) {
    return (
      <div className="h-screen bg-dark-bg flex items-center justify-center">
        <div className="text-gray-500 text-sm">Loading...</div>
      </div>
    );
  }
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
  const { isAuthenticated, loadUser } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      loadUser();
    } else {
      useAuthStore.setState({ isLoading: false });
    }
  }, []); // eslint-disable-line

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />

      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<DashboardPage />} />
        <Route path="inventory" element={<InventoryPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="proposals" element={<ProposalsPage />} />
        <Route path="payments" element={<PaymentsPage />} />
        <Route path="dispatch" element={<DispatchPage />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="website" element={<WebsitePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#161B22",
              color: "#E6EDF3",
              border: "1px solid #21272F",
              fontSize: "13px",
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
