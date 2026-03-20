import {
  DollarSign, FileText, Package, Send, TrendingUp, TrendingDown,
  Calendar, MapPin, AlertTriangle, Star, CreditCard,
} from "lucide-react";
import { useDashboard } from "@/hooks/useApi";

function StatCard({ label, value, change, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl p-5 border border-gray-200 flex-1 min-w-[180px]">
      <div className="flex justify-between items-start mb-2.5">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center`} style={{ background: color + "18" }}>
          <Icon size={16} style={{ color }} />
        </div>
      </div>
      <div className="text-2xl font-bold text-gray-900 tracking-tight">{value}</div>
      {change !== undefined && (
        <div className={`flex items-center gap-1 mt-1.5 text-xs ${change >= 0 ? "text-green-600" : "text-red-600"}`}>
          {change >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
          <span className="font-semibold">{Math.abs(change)}%</span>
          <span className="text-gray-500">vs last month</span>
        </div>
      )}
    </div>
  );
}

function ProgressBar({ value, max, color = "#2563eb" }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();

  if (isLoading) {
    return (
      <div className="p-7 flex items-center justify-center h-full">
        <div className="text-gray-400 text-sm">Loading dashboard...</div>
      </div>
    );
  }

  const stats = data || {};

  return (
    <div className="p-7 space-y-6">
      {/* Stats Row */}
      <div className="flex gap-4 flex-wrap">
        <StatCard label="Monthly Revenue" value={`$${(stats.monthly_revenue || 0).toLocaleString()}`} icon={DollarSign} color="#16a34a" />
        <StatCard label="Active Projects" value={stats.active_projects || 0} icon={FileText} color="#2563eb" />
        <StatCard label="Items Rented" value={stats.items_rented || 0} icon={Package} color="#d97706" />
        <StatCard label="Proposals Sent" value={stats.proposals_sent || 0} icon={Send} color="#9333ea" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Upcoming Events */}
        <div className="bg-white rounded-xl p-5 border border-gray-200 lg:col-span-2">
          <h3 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Calendar size={16} className="text-blue-600" />Upcoming Events
          </h3>
          <div className="space-y-3">
            {(stats.upcoming_events || []).length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No upcoming events</p>
            ) : (
              stats.upcoming_events.map((e) => (
                <div key={e.id} className="p-3.5 rounded-lg bg-gray-50 border border-gray-200 hover:border-accent/40 transition-colors cursor-pointer">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-sm font-semibold text-gray-900">{e.event_name}</div>
                      <div className="text-xs text-gray-400 mt-0.5">{e.client}</div>
                    </div>
                    <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-md ${
                      e.stage === "confirmed" ? "bg-green-50 text-green-600"
                      : e.stage === "deposit_paid" ? "bg-blue-50 text-blue-600"
                      : "bg-amber-50 text-amber-600"
                    }`}>{e.stage?.replace("_", " ")}</span>
                  </div>
                  <div className="flex gap-3 mt-2.5 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><Calendar size={11} />{new Date(e.date).toLocaleDateString()}</span>
                    {e.venue && <span className="flex items-center gap-1"><MapPin size={11} />{e.venue}</span>}
                    <span className="ml-auto font-mono font-semibold text-gray-700">${e.total?.toLocaleString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Inventory Alerts */}
        <div className="bg-white rounded-xl p-5 border border-gray-200">
          <h3 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-600" />Inventory Alerts
          </h3>
          <div className="space-y-3">
            {(stats.inventory_alerts || []).length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">All stock levels healthy</p>
            ) : (
              stats.inventory_alerts.map((item) => (
                <div key={item.id} className="flex items-center gap-3 py-2 border-b border-gray-200 last:border-0">
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-gray-800">{item.name}</div>
                    <div className="text-xs text-gray-500">{item.available} of {item.total} available</div>
                  </div>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-600">LOW</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Top Performers */}
      <div className="bg-white rounded-xl p-5 border border-gray-200">
        <h3 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Star size={16} className="text-purple-600" />Top Revenue Items
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {(stats.top_performers || []).map((item, i) => (
            <div key={item.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 border border-gray-200">
              <span className="text-xs font-extrabold text-gray-400 w-5">#{i + 1}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-gray-800 truncate">{item.name}</div>
                <div className="text-xs text-gray-500">{item.bookings} bookings</div>
              </div>
              <span className="text-sm font-bold text-green-600 font-mono">${item.revenue?.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
