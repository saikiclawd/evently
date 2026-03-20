import { useState } from "react";
import { Plus, Route, Zap, MapPin, Clock, Package, Edit, Grip, Users, Calendar, Download } from "lucide-react";
import { useRoutes, useAutoRoute } from "@/hooks/useApi";
import toast from "react-hot-toast";

const stopTypeColors = {
  delivery: "bg-accent/10 text-accent border-accent/30",
  pickup: "bg-green-500/10 text-green-400 border-green-500/30",
  setup: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  teardown: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  custom: "bg-gray-500/10 text-gray-400 border-gray-500/30",
};

export default function DispatchPage() {
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const { data: routes = [], isLoading } = useRoutes({ date });
  const autoRoute = useAutoRoute();

  const handleAutoRoute = async (routeId) => {
    try {
      const result = await autoRoute.mutateAsync(routeId);
      toast.success(`Route optimized! ${result.total_distance_miles} mi, ${result.total_drive_minutes} min`);
    } catch {
      toast.error("Failed to optimize route");
    }
  };

  return (
    <div className="p-7">
      <div className="flex items-center gap-3 mb-5">
        <h2 className="text-lg font-bold text-gray-100 flex items-center gap-2">
          <Route size={20} className="text-accent" />Route Planner
        </h2>
        <span className="text-[10px] font-bold px-2.5 py-1 rounded-md bg-accent/10 text-accent tracking-wide">AI AUTO-ROUTE</span>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
          className="ml-4 px-3 py-1.5 rounded-lg border border-dark-border bg-dark-surface text-sm text-gray-200 focus:outline-none focus:border-accent" />
        <div className="ml-auto flex gap-2">
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-dark-border text-xs font-semibold text-gray-300 hover:bg-dark-surface">
            <Zap size={14} />Auto-Route All
          </button>
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-accent text-white text-xs font-semibold hover:bg-accent/90">
            <Plus size={14} />New Route
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-20 text-gray-500 text-sm">Loading routes...</div>
      ) : routes.length === 0 ? (
        <div className="text-center py-20">
          <Route size={40} className="text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 text-sm">No routes for this date</p>
          <p className="text-gray-500 text-xs mt-1">Create a route or select a different date</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {routes.map((route) => (
            <div key={route.id} className="bg-dark-card rounded-xl border border-dark-border overflow-hidden">
              {/* Route header */}
              <div className="px-5 py-4 border-b border-dark-border bg-dark-surface flex justify-between items-center">
                <div>
                  <div className="text-sm font-bold text-gray-100">{route.vehicle?.name || "Unassigned Vehicle"}</div>
                  <div className="flex items-center gap-3 text-xs text-gray-400 mt-1">
                    {route.crew?.length > 0 && (
                      <span className="flex items-center gap-1"><Users size={12} />{route.crew.map((c) => c.user?.name).join(", ")}</span>
                    )}
                    <span className="flex items-center gap-1"><Calendar size={12} />{new Date(route.route_date).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-accent/10 text-accent">
                    {route.stops?.length || 0} stops
                  </span>
                  {route.total_distance_miles > 0 && (
                    <span className="text-[11px] text-gray-500">{route.total_distance_miles} mi</span>
                  )}
                  <button onClick={() => handleAutoRoute(route.id)}
                    className="w-7 h-7 rounded flex items-center justify-center text-gray-500 hover:bg-dark-card hover:text-accent" title="Optimize">
                    <Zap size={14} />
                  </button>
                  <button className="w-7 h-7 rounded flex items-center justify-center text-gray-500 hover:bg-dark-card hover:text-gray-300" title="Edit">
                    <Edit size={14} />
                  </button>
                </div>
              </div>

              {/* Stops */}
              {(route.stops || []).map((stop, i) => (
                <div key={stop.id} className="flex gap-3.5 px-5 py-4 border-b border-dark-border last:border-0">
                  <div className="flex flex-col items-center gap-1">
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border ${stopTypeColors[stop.stop_type] || stopTypeColors.custom}`}>
                      {i + 1}
                    </div>
                    {i < (route.stops?.length || 0) - 1 && (
                      <div className="w-0.5 flex-1 bg-dark-border rounded" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-sm font-semibold text-gray-100">{stop.venue_name || "Stop"}</div>
                        {stop.address && <div className="text-xs text-gray-500 mt-0.5 truncate">{stop.address}</div>}
                      </div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${stopTypeColors[stop.stop_type] || stopTypeColors.custom}`}>
                        {stop.stop_type}
                      </span>
                    </div>
                    <div className="flex gap-4 mt-2 text-xs text-gray-500">
                      {stop.arrival_time && <span className="flex items-center gap-1"><Clock size={12} />{stop.arrival_time}</span>}
                      <span className="flex items-center gap-1"><Clock size={12} />{stop.duration_minutes} min on site</span>
                      {stop.drive_minutes_from_prev > 0 && (
                        <span className="text-gray-600">{stop.drive_minutes_from_prev} min drive</span>
                      )}
                    </div>
                  </div>
                  <Grip size={14} className="text-gray-600 cursor-grab mt-1 flex-shrink-0" />
                </div>
              ))}

              {/* Route actions */}
              <div className="px-5 py-3 bg-dark-surface flex gap-2">
                <button className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-dark-border text-[11px] text-gray-400 hover:text-gray-200 hover:bg-dark-card">
                  <Plus size={12} />Add Stop
                </button>
                <button className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-dark-border text-[11px] text-gray-400 hover:text-gray-200 hover:bg-dark-card">
                  <MapPin size={12} />Open in Maps
                </button>
                <button className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-dark-border text-[11px] text-gray-400 hover:text-gray-200 hover:bg-dark-card">
                  <Download size={12} />Pull Sheet
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
