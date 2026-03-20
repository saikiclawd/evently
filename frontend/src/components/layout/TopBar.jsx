import { Search, Bell, Settings } from "lucide-react";
import { useLocation } from "react-router-dom";
import useAuthStore from "@/store/authStore";

const pageTitles = {
  "/": "Dashboard",
  "/inventory": "Inventory",
  "/projects": "Projects",
  "/clients": "CRM",
  "/proposals": "Proposals",
  "/payments": "Payments",
  "/dispatch": "Dispatch",
  "/calendar": "Calendar",
  "/reports": "Reports",
  "/website": "Website Integration",
};

export default function TopBar() {
  const { pathname } = useLocation();
  const { user } = useAuthStore();
  const title = pageTitles[pathname] || "Evently";

  return (
    <header className="h-16 px-7 flex items-center justify-between border-b border-dark-border bg-white flex-shrink-0">
      <h1 className="text-lg font-bold text-gray-900">{title}</h1>

      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search anything..."
            className="w-64 pl-9 pr-3 py-2 rounded-lg border border-dark-border bg-dark-bg text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 transition-colors"
          />
        </div>

        {/* Actions */}
        <button className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition-colors">
          <Bell size={18} />
        </button>
        <button className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition-colors">
          <Settings size={18} />
        </button>

        {/* Avatar */}
        {user?.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.name}
            className="w-9 h-9 rounded-full cursor-pointer object-cover ring-2 ring-dark-border"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-accent to-blue-700 flex items-center justify-center text-xs font-bold text-white cursor-pointer">
            {user?.name?.charAt(0)?.toUpperCase() || "U"}
          </div>
        )}
      </div>
    </header>
  );
}
