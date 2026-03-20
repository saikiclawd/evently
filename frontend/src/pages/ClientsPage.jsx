// ── Clients CRM Page ──
import { useState } from "react";
import { UserPlus, Search, Mail, Phone, FileText } from "lucide-react";
import { useClients } from "@/hooks/useApi";

export default function ClientsPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useClients({ search });
  const clients = data?.clients || [];

  return (
    <div className="p-7">
      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search clients..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-dark-border bg-dark-surface text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent" />
        </div>
        <button className="ml-auto flex items-center gap-1.5 px-3 py-2 rounded-lg bg-accent text-white text-xs font-semibold hover:bg-accent/90">
          <UserPlus size={14} />Add Client
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-20 text-gray-500 text-sm">Loading clients...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {clients.map((c) => (
            <div key={c.id} className="bg-dark-card rounded-xl p-5 border border-dark-border hover:border-accent/30 transition-colors cursor-pointer">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-accent/20 to-purple-500/20 flex items-center justify-center text-base font-bold text-accent">
                  {c.name?.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-gray-100 truncate">{c.name}</div>
                  <div className="text-xs text-gray-400 truncate">{c.email}</div>
                </div>
              </div>
              {c.tags?.length > 0 && (
                <div className="flex gap-1 mb-3 flex-wrap">
                  {c.tags.map((t) => (
                    <span key={t} className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                      t === "vip" ? "bg-purple-500/10 text-purple-400"
                      : t === "corporate" ? "bg-accent/10 text-accent"
                      : t === "repeat" ? "bg-green-500/10 text-green-400"
                      : "bg-dark-border text-gray-400"
                    }`}>{t}</span>
                  ))}
                </div>
              )}
              <div className="grid grid-cols-3 gap-2 py-3 border-t border-dark-border">
                <div>
                  <div className="text-[10px] text-gray-500">Events</div>
                  <div className="text-base font-bold text-gray-100">{c.event_count || 0}</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Total Spent</div>
                  <div className="text-base font-bold text-green-400 font-mono">${((c.total_spent || 0) / 1000).toFixed(1)}k</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Last Event</div>
                  <div className="text-xs text-gray-400 mt-1">{c.updated_at ? new Date(c.updated_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—"}</div>
                </div>
              </div>
              <div className="flex gap-2 mt-3">
                <button className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg border border-dark-border text-xs font-semibold text-gray-300 hover:bg-dark-surface">
                  <Mail size={13} />Email
                </button>
                <button className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg border border-dark-border text-xs font-semibold text-gray-300 hover:bg-dark-surface">
                  <Phone size={13} />Call
                </button>
                <button className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg bg-dark-border text-xs font-semibold text-gray-200 hover:bg-gray-600/20">
                  <FileText size={13} />Quote
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
