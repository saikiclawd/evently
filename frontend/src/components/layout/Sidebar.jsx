import { NavLink } from "react-router-dom";
import {
  BarChart3, Package, FileText, CreditCard, Truck, Users,
  Calendar, Globe, Zap, ChevronLeft, ChevronRight, PenTool, LogOut,
} from "lucide-react";
import useAuthStore from "@/store/authStore";

const navItems = [
  { to: "/", icon: BarChart3, label: "Dashboard" },
  { to: "/inventory", icon: Package, label: "Inventory" },
  { to: "/projects", icon: FileText, label: "Projects" },
  { to: "/clients", icon: Users, label: "CRM" },
  { to: "/proposals", icon: PenTool, label: "Proposals" },
  { to: "/payments", icon: CreditCard, label: "Payments" },
  { to: "/dispatch", icon: Truck, label: "Dispatch" },
  { to: "/calendar", icon: Calendar, label: "Calendar" },
  { to: "/reports", icon: BarChart3, label: "Reports" },
  { to: "/website", icon: Globe, label: "Website" },
];

export default function Sidebar({ collapsed, setCollapsed }) {
  const { user, logout } = useAuthStore();

  return (
    <aside
      className={`h-screen bg-white border-r border-dark-border flex flex-col transition-all duration-200 flex-shrink-0 ${
        collapsed ? "w-16" : "w-56"
      }`}
    >
      {/* Logo */}
      <div className="h-16 flex items-center gap-2.5 px-4 border-b border-dark-border">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-blue-700 flex items-center justify-center flex-shrink-0">
          <Zap size={18} className="text-white" />
        </div>
        {!collapsed && (
          <div>
            <div className="text-sm font-extrabold text-gray-900 tracking-tight">Evently</div>
            <div className="text-[10px] font-semibold text-gray-400 tracking-widest">PRO</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2.5 rounded-lg mb-0.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-accent/8 text-accent"
                  : "text-gray-500 hover:bg-gray-50 hover:text-gray-800"
              } ${collapsed ? "justify-center px-0" : ""}`
            }
          >
            <Icon size={18} className="flex-shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-dark-border p-2 space-y-1">
        {!collapsed && user && (
          <div className="px-3 py-2 text-xs text-gray-400 truncate">
            {user.email}
          </div>
        )}
        <button
          onClick={logout}
          className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-xs text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors ${
            collapsed ? "justify-center px-0" : ""
          }`}
        >
          <LogOut size={16} />
          {!collapsed && <span>Logout</span>}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-xs text-gray-400 hover:text-gray-700 transition-colors ${
            collapsed ? "justify-center px-0" : ""
          }`}
        >
          {collapsed ? <ChevronRight size={16} /> : <><ChevronLeft size={16} /><span>Collapse</span></>}
        </button>
      </div>
    </aside>
  );
}
