// ── Clients CRM Page — List view + Pipeline (Twenty-CRM-inspired kanban) ──
import { useState } from "react";
import { UserPlus, Search, Mail, Phone, FileText, LayoutGrid, Kanban, X } from "lucide-react";
import toast from "react-hot-toast";
import { useClients, useCreateClient } from "@/hooks/useApi";
import ClientPipelineBoard from "@/components/crm/ClientPipelineBoard";
import ClientDetailDrawer from "@/components/crm/ClientDetailDrawer";

const LIFECYCLE_META = {
  lead:         "bg-gray-100 text-gray-600",
  qualified:    "bg-blue-50 text-blue-600",
  active:       "bg-amber-50 text-amber-600",
  past_client:  "bg-green-50 text-green-600",
  lost:         "bg-red-50 text-red-500",
};

function AddClientModal({ onClose }) {
  const createClient = useCreateClient();
  const [form, setForm] = useState({ name: "", email: "", phone: "", lead_source: "", lifecycle_stage: "lead" });

  function submit() {
    if (!form.name.trim()) return;
    createClient.mutate(form, {
      onSuccess: () => { toast.success("Client added"); onClose(); },
      onError: () => toast.error("Failed to add client"),
    });
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-[440px] p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-bold text-gray-900">Add Client</h3>
          <button onClick={onClose} className="text-gray-300 hover:text-gray-600"><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent" />
          <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent" />
          <input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent" />
          <input placeholder="Lead source (referral, instagram...)" value={form.lead_source} onChange={(e) => setForm({ ...form, lead_source: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent" />
          <select value={form.lifecycle_stage} onChange={(e) => setForm({ ...form, lifecycle_stage: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent">
            {Object.keys(LIFECYCLE_META).map((s) => (
              <option key={s} value={s}>{s.replace("_", " ")}</option>
            ))}
          </select>
        </div>
        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm text-gray-500 hover:border-gray-300">
            Cancel
          </button>
          <button onClick={submit} disabled={!form.name.trim() || createClient.isPending}
            className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm font-semibold hover:bg-blue-700 disabled:opacity-40">
            {createClient.isPending ? "Saving…" : "Add Client"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ClientsPage() {
  const [search, setSearch] = useState("");
  const [view, setView] = useState("list"); // "list" | "pipeline"
  const [showAdd, setShowAdd] = useState(false);
  const [openClientId, setOpenClientId] = useState(null);
  const { data, isLoading } = useClients({ search });
  const clients = data?.clients || [];

  return (
    <div className="p-7">
      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search clients..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 bg-gray-50 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent" />
        </div>

        <div className="flex items-center bg-gray-100 rounded-lg p-0.5 ml-auto">
          <button onClick={() => setView("list")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
              view === "list" ? "bg-white text-gray-800 shadow-sm" : "text-gray-500"
            }`}>
            <LayoutGrid size={13} />List
          </button>
          <button onClick={() => setView("pipeline")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
              view === "pipeline" ? "bg-white text-gray-800 shadow-sm" : "text-gray-500"
            }`}>
            <Kanban size={13} />Pipeline
          </button>
        </div>

        <button onClick={() => setShowAdd(true)} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700">
          <UserPlus size={14} />Add Client
        </button>
      </div>

      {view === "pipeline" ? (
        <ClientPipelineBoard onOpen={setOpenClientId} />
      ) : isLoading ? (
        <div className="text-center py-20 text-gray-400 text-sm">Loading clients...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {clients.map((c) => (
            <div key={c.id} onClick={() => setOpenClientId(c.id)}
              className="bg-white rounded-xl p-5 border border-gray-200 hover:border-accent/40 transition-colors cursor-pointer">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-accent/10 to-blue-100 flex items-center justify-center text-base font-bold text-blue-600">
                  {c.name?.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-gray-900 truncate">{c.name}</div>
                  <div className="text-xs text-gray-400 truncate">{c.email}</div>
                </div>
              </div>

              <div className="flex gap-1.5 mb-3 flex-wrap">
                {c.lifecycle_stage && (
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md capitalize ${LIFECYCLE_META[c.lifecycle_stage] || "bg-gray-100 text-gray-500"}`}>
                    {c.lifecycle_stage.replace("_", " ")}
                  </span>
                )}
                {c.tags?.map((t) => (
                  <span key={t} className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                    t === "vip" ? "bg-purple-50 text-purple-600"
                    : t === "corporate" ? "bg-blue-50 text-blue-600"
                    : t === "repeat" ? "bg-green-50 text-green-600"
                    : "bg-gray-100 text-gray-500"
                  }`}>{t}</span>
                ))}
              </div>

              <div className="grid grid-cols-4 gap-2 py-3 border-t border-gray-200">
                <div>
                  <div className="text-[10px] text-gray-500">Events</div>
                  <div className="text-base font-bold text-gray-900">{c.event_count || 0}</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Spent</div>
                  <div className="text-base font-bold text-green-600 font-mono">${((c.total_spent || 0) / 1000).toFixed(1)}k</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Contacts</div>
                  <div className="text-base font-bold text-gray-900">{c.contact_count || 0}</div>
                </div>
                <div>
                  <div className="text-[10px] text-gray-500">Tasks</div>
                  <div className={`text-base font-bold ${c.open_task_count > 0 ? "text-amber-600" : "text-gray-300"}`}>{c.open_task_count || 0}</div>
                </div>
              </div>
              <div className="flex gap-2 mt-3" onClick={(e) => e.stopPropagation()}>
                <button className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-gray-50">
                  <Mail size={13} />Email
                </button>
                <button className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-gray-50">
                  <Phone size={13} />Call
                </button>
                <button className="flex-1 flex items-center justify-center gap-1 py-2 rounded-lg bg-gray-100 text-xs font-semibold text-gray-800 hover:bg-gray-600/20">
                  <FileText size={13} />Quote
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showAdd && <AddClientModal onClose={() => setShowAdd(false)} />}
      {openClientId && <ClientDetailDrawer clientId={openClientId} onClose={() => setOpenClientId(null)} />}
    </div>
  );
}
