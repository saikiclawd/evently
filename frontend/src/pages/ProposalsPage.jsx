import { useState } from "react";
import { Plus, Grip, Trash2, Send, Eye, Download, Image, Layers, Shield, Clock, Copy } from "lucide-react";
import { useProjects } from "@/hooks/useApi";

const tabs = [
  { key: "builder", label: "Quote Builder" },
  { key: "templates", label: "Templates" },
  { key: "sent", label: "Sent Proposals" },
];

const stageColors = {
  signed: "bg-green-50 text-green-600",
  paid_in_full: "bg-emerald-50 text-emerald-600",
  proposal_sent: "bg-amber-50 text-amber-600",
  draft: "bg-gray-100 text-gray-500",
};

const templates = [
  { name: "Wedding Package", icon: "💒", desc: "Pre-built template with ceremony + reception items" },
  { name: "Corporate Event", icon: "🏢", desc: "AV, staging, and cocktail reception setup" },
  { name: "Birthday Party", icon: "🎂", desc: "Tables, chairs, linens, and decor basics" },
  { name: "Outdoor Festival", icon: "🎪", desc: "Tenting, lighting, staging, and PA systems" },
];

export default function ProposalsPage() {
  const [activeTab, setActiveTab] = useState("sent");
  const { data } = useProjects({ per_page: 50 });
  const projects = data?.projects || [];
  const sentProposals = projects.filter((p) => p.stage !== "draft");

  return (
    <div className="p-7">
      <div className="flex items-center gap-2 mb-5">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === t.key ? "bg-blue-50 text-blue-600" : "text-gray-400 hover:bg-white"
            }`}>
            {t.label}
            {t.key === "sent" && <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded-md bg-gray-100">{sentProposals.length}</span>}
          </button>
        ))}
        <button className="ml-auto flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700">
          <Plus size={14} />New Quote
        </button>
      </div>

      {activeTab === "builder" && (
        <div className="grid grid-cols-[1fr_360px] gap-5">
          {/* Builder area */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h3 className="text-sm font-bold text-gray-900">Drag & Drop Quote Builder</h3>
                <p className="text-xs text-gray-400 mt-0.5">Add items from inventory to build a professional proposal</p>
              </div>
              <div className="flex gap-2">
                <button className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-gray-200 text-[11px] text-gray-400 hover:text-gray-800">
                  <Image size={12} />Add Photo
                </button>
                <button className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-gray-200 text-[11px] text-gray-400 hover:text-gray-800">
                  <Layers size={12} />Packages
                </button>
              </div>
            </div>
            <div className="text-center py-16 text-gray-500">
              <Layers size={36} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">Select a project or create a new quote</p>
              <p className="text-xs text-gray-400 mt-1">Drag items from your inventory to build the proposal</p>
            </div>
          </div>

          {/* Summary sidebar */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
            <h3 className="text-sm font-bold text-gray-900">Quote Summary</h3>
            <div className="space-y-2.5 text-sm">
              {[["Subtotal", "$0.00"], ["Tax", "$0.00"], ["Delivery", "$0.00"]].map(([l, v]) => (
                <div key={l} className="flex justify-between text-gray-500">
                  <span>{l}</span><span className="font-mono">{v}</span>
                </div>
              ))}
              <div className="h-px bg-gray-100" />
              <div className="flex justify-between text-lg font-bold">
                <span className="text-gray-900">Total</span>
                <span className="text-blue-600 font-mono">$0.00</span>
              </div>
            </div>
            <div className="space-y-2 pt-4 border-t border-gray-200">
              <button className="w-full py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 flex items-center justify-center gap-2">
                <Send size={14} />Send Proposal
              </button>
              <button className="w-full py-2.5 rounded-lg border border-gray-200 text-gray-700 text-sm font-semibold hover:bg-gray-50 flex items-center justify-center gap-2">
                <Eye size={14} />Preview Client View
              </button>
              <button className="w-full py-2.5 rounded-lg border border-gray-200 text-gray-700 text-sm font-semibold hover:bg-gray-50 flex items-center justify-center gap-2">
                <Download size={14} />Export PDF
              </button>
            </div>
            <div className="p-3.5 bg-gray-50 rounded-lg border border-gray-200 space-y-2">
              <div className="text-[10px] text-gray-400 font-semibold uppercase tracking-wide">Digital Signature</div>
              <div className="flex items-center gap-2 text-xs text-gray-500"><Shield size={13} className="text-green-600" />E-signature collection enabled</div>
              <div className="flex items-center gap-2 text-xs text-gray-500"><Clock size={13} className="text-amber-600" />Quote expires in 14 days</div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "sent" && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {sentProposals.length === 0 ? (
            <div className="py-12 text-center text-gray-400 text-sm">No proposals sent yet</div>
          ) : (
            sentProposals.map((p) => (
              <div key={p.id} className="flex items-center gap-4 px-5 py-4 border-b border-gray-200 hover:bg-gray-50/50 transition-colors cursor-pointer">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-gray-900">{p.event_name}</div>
                  <div className="text-xs text-gray-500">{p.client?.name}</div>
                </div>
                <span className="text-sm font-semibold text-gray-900 font-mono">${(p.total || 0).toLocaleString()}</span>
                <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-md ${stageColors[p.stage] || stageColors.draft}`}>
                  {p.stage?.replace("_", " ")}
                </span>
                <button className="w-7 h-7 rounded flex items-center justify-center text-gray-400 hover:bg-white hover:text-gray-700">
                  <Eye size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === "templates" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {templates.map((t, i) => (
            <div key={i} className="bg-white rounded-xl p-5 border border-gray-200 hover:border-accent/40 transition-colors cursor-pointer text-center">
              <div className="text-3xl mb-3">{t.icon}</div>
              <div className="text-sm font-semibold text-gray-900 mb-1">{t.name}</div>
              <div className="text-xs text-gray-400 mb-4">{t.desc}</div>
              <button className="flex items-center justify-center gap-1.5 mx-auto px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-gray-50">
                <Copy size={12} />Use Template
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
