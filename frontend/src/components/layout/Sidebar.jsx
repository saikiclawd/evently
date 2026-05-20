import { NavLink } from "react-router-dom";
import {
  BarChart3, Package, FileText, CreditCard, Truck, Users,
  Calendar, Globe, Zap, ChevronLeft, ChevronRight, PenTool, LogOut,
  FlowerIcon, ClipboardList, ShoppingCart, BookOpen, Sparkles,
} from "lucide-react";
import useAuthStore from "@/store/authStore";

// Use Flower from lucide if available, otherwise use a custom SVG
const Flower = ({ size = 18, className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="12" r="3"/>
    <path d="M12 2a4 4 0 0 1 4 4 4 4 0 0 1-4 4 4 4 0 0 1-4-4 4 4 0 0 1 4-4"/>
    <path d="M12 14a4 4 0 0 1 4 4 4 4 0 0 1-4 4 4 4 0 0 1-4-4 4 4 0 0 1 4-4"/>
    <path d="M2 12a4 4 0 0 1 4-4 4 4 0 0 1 4 4 4 4 0 0 1-4 4 4 4 0 0 1-4-4"/>
    <path d="M14 12a4 4 0 0 1 4-4 4 4 0 0 1 4 4 4 4 0 0 1-4 4 4 4 0 0 1-4-4"/>
  </svg>
);

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

const floraItems = [
  { to: "/flora/ai",      icon: Sparkles,       label: "AI Analyzer" },
  { to: "/flora/recipes", icon: BookOpen,       label: "Recipes" },
  { to: "/flora/events",  icon: Calendar,       label: "Events" },
  { to: "/flora/orders",  icon: ShoppingCart,   label: "Orders" },
  { to: "/flora/catalog", icon: ClipboardList,  label: "Catalog" },
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

        {/* FloraFlow Section */}
        {!collapsed && (
          <div className="mt-4 mb-1 px-3 flex items-center gap-1.5">
            <Flower size={12} className="text-flora-gold" />
            <span className="text-[10px] font-bold text-flora-gold tracking-widest uppercase">FloraFlow</span>
          </div>
        )}
        {collapsed && <div className="mt-3 mb-1 border-t border-gray-100" />}
        {floraItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2.5 rounded-lg mb-0.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-flora-gold-lt text-flora-gold"
                  : "text-gray-500 hover:bg-flora-cream hover:text-gray-800"
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
