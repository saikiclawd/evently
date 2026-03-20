import { useState } from "react";
import { Plus, Search, MapPin, Eye, MoreVertical, Calendar } from "lucide-react";
import { useProjects, useChangeStage } from "@/hooks/useApi";
import toast from "react-hot-toast";

const stageColors = {
  draft: "bg-gray-100 text-gray-500",
  proposal_sent: "bg-amber-50 text-amber-600",
  signed: "bg-blue-50 text-blue-600",
  deposit_paid: "bg-blue-50 text-blue-600",
  confirmed: "bg-green-50 text-green-600",
  paid_in_full: "bg-emerald-50 text-emerald-600",
  completed: "bg-teal-50 text-teal-600",
  cancelled: "bg-red-50 text-red-600",
};

export default function ProjectsPage() {
  const [filter, setFilter] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useProjects({ stage: filter || undefined, search, page });
  const changeStage = useChangeStage();

  const projects = data?.projects || [];
  const tabs = [
    { key: "", label: "All", count: data?.total },
    { key: "confirmed", label: "Confirmed" },
    { key: "proposal_sent", label: "Pending" },
    { key: "draft", label: "Draft" },
  ];

  return (
    <div className="p-7">
      <div className="flex items-center gap-3 mb-5 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search projects..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 bg-gray-50 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent" />
        </div>
        <div className="flex gap-1">
          {tabs.map((t) => (
            <button key={t.key} onClick={() => { setFilter(t.key); setPage(1); }}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${filter === t.key ? "bg-blue-50 text-blue-600" : "text-gray-400 hover:bg-white"}`}>
              {t.label}
            </button>
          ))}
        </div>
        <button className="ml-auto flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700">
          <Plus size={14} />New Project
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[90px_1.5fr_1fr_1fr_120px_130px_80px_60px] px-5 py-3 border-b border-gray-200 text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
          <span>ID</span><span>Event / Client</span><span>Venue</span><span>Date</span>
          <span>Stage</span><span className="text-right">Amount</span><span className="text-center">Items</span><span></span>
        </div>

        {isLoading ? (
          <div className="py-12 text-center text-gray-400 text-sm">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">No projects found</div>
        ) : (
          projects.map((p) => (
            <div key={p.id}
              className="grid grid-cols-[90px_1.5fr_1fr_1fr_120px_130px_80px_60px] px-5 py-4 border-b border-gray-200 items-center hover:bg-gray-50/50 transition-colors cursor-pointer">
              <span className="text-xs font-mono text-gray-500">{p.project_number}</span>
              <div>
                <div className="text-sm font-semibold text-gray-900">{p.event_name}</div>
                <div className="text-xs text-gray-500">{p.client?.name}</div>
              </div>
              <span className="text-xs text-gray-400 flex items-center gap-1 truncate">
                <MapPin size={12} />{p.venue_name || "—"}
              </span>
              <span className="text-xs text-gray-500">
                {p.event_start ? new Date(p.event_start).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—"}
              </span>
              <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md w-fit ${stageColors[p.stage] || stageColors.draft}`}>
                {p.stage?.replace("_", " ")}
              </span>
              <div className="text-right">
                <div className="text-sm font-semibold text-gray-900 font-mono">${(p.total || 0).toLocaleString()}</div>
                {p.balance_due > 0 && <div className="text-[10px] text-amber-600">${p.balance_due.toLocaleString()} due</div>}
              </div>
              <div className="text-center text-xs text-gray-500">{p.item_count} items</div>
              <div className="flex gap-1 justify-end">
                <button className="w-7 h-7 rounded flex items-center justify-center text-gray-400 hover:bg-white hover:text-gray-700">
                  <Eye size={14} />
                </button>
                <button className="w-7 h-7 rounded flex items-center justify-center text-gray-400 hover:bg-white hover:text-gray-700">
                  <MoreVertical size={14} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
