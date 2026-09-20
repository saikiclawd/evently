import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { flora } from "@/lib/api";
import toast from "react-hot-toast";
import { ShoppingCart, Send, CheckCircle, X, ChevronDown, Eye } from "lucide-react";

const STATUS_CONFIG = {
  draft:     { label: "Draft",     color: "bg-gray-100 text-gray-600",       dot: "#9CA3AF" },
  sent:      { label: "Sent",      color: "bg-blue-50 text-blue-600",        dot: "#2563EB" },
  confirmed: { label: "Confirmed", color: "bg-flora-sage-lt text-flora-sage", dot: "#5E7E6A" },
  received:  { label: "Received",  color: "bg-green-50 text-green-600",      dot: "#16a34a" },
  partial:   { label: "Partial",   color: "bg-orange-50 text-orange-600",    dot: "#d97706" },
  cancelled: { label: "Cancelled", color: "bg-red-50 text-red-500",          dot: "#ef4444" },
};

function PODetail({ orderId, onClose }) {
  const { data: order, isLoading } = useQuery({
    queryKey: ["flora-order", orderId],
    queryFn: () => flora.getOrder(orderId).then(r => r.data),
  });
  const qc = useQueryClient();
  const sendMut = useMutation({
    mutationFn: () => flora.sendOrder(orderId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["flora-orders"] }); qc.invalidateQueries({ queryKey: ["flora-order", orderId] }); toast.success("PO marked as sent"); },
  });

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-[720px] max-h-[90vh] overflow-y-auto">
        {/* Chrome-style header */}
        <div className="bg-gray-900 px-6 py-4 rounded-t-2xl flex items-center justify-between">
          <div>
            {isLoading ? (
              <div className="text-white/60 text-sm">Loading…</div>
            ) : (
              <>
                <div className="font-playfair text-white text-lg">{order?.po_number}</div>
                <div className="text-white/50 text-sm mt-0.5">
                  {order?.event_name} · {order?.vendor_name}
                </div>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            {order?.status === "draft" && (
              <button onClick={() => sendMut.mutate()} disabled={sendMut.isPending}
                className="flex items-center gap-1.5 bg-flora-gold text-white text-sm font-semibold px-4 py-1.5 rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-50">
                <Send size={13} /> {sendMut.isPending ? "Sending…" : "Mark Sent"}
              </button>
            )}
            <button onClick={onClose} className="text-white/50 hover:text-white transition-colors">
              <X size={18} />
            </button>
          </div>
        </div>

        {order && (
          <div className="p-6">
            {/* Meta */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Required By</div>
                <div className="text-sm font-semibold text-gray-800">
                  {order.required_by_date
                    ? new Date(order.required_by_date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
                    : "—"}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Status</div>
                <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${STATUS_CONFIG[order.status]?.color}`}>
                  {STATUS_CONFIG[order.status]?.label}
                </span>
              </div>
              <div className="bg-flora-gold-lt rounded-lg p-3">
                <div className="text-xs font-semibold text-flora-gold uppercase tracking-wide mb-1">Total</div>
                <div className="font-playfair text-xl text-flora-gold">${order.total_amount?.toFixed(2)}</div>
              </div>
            </div>

            {/* Line Items */}
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-100">
                  {["Flower / Variety", "Stems", "Bunches", "Bunch Size", "Unit Price", "Total"].map(h => (
                    <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wide pb-3 pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(order.line_items || []).map(li => (
                  <tr key={li.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 pr-4 font-medium text-gray-800">{li.flower_name}</td>
                    <td className="py-3 pr-4 font-semibold text-gray-900">{li.stems_required}</td>
                    <td className="py-3 pr-4 text-gray-600">{li.bunches_required}</td>
                    <td className="py-3 pr-4 text-gray-400">× {li.bunch_size}</td>
                    <td className="py-3 pr-4 text-gray-600">${li.unit_price?.toFixed(2)}</td>
                    <td className="py-3 font-semibold text-flora-gold">${li.line_total?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-gray-200">
                  <td colSpan="5" className="pt-3 font-bold text-gray-700">Total</td>
                  <td className="pt-3 font-bold text-flora-gold font-playfair text-lg">${order.total_amount?.toFixed(2)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      <style>{`.font-playfair { font-family: 'Playfair Display', serif; }`}</style>
    </div>
  );
}

export default function OrderEnginePage() {
  const [filterStatus, setFilterStatus] = useState("");
  const [viewingId, setViewingId] = useState(null);

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ["flora-orders", filterStatus],
    queryFn: () => flora.orders(filterStatus ? { status: filterStatus } : {}).then(r => r.data),
  });

  const totalByStatus = orders.reduce((acc, o) => {
    acc[o.status] = (acc[o.status] || 0) + 1;
    return acc;
  }, {});

  const grandTotal = orders
    .filter(o => o.status !== "cancelled")
    .reduce((s, o) => s + (o.total_amount || 0), 0);

  return (
    <div className="p-7 space-y-6 bg-flora-cream min-h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-playfair text-2xl text-gray-900">Order Engine</h1>
          <p className="text-sm text-gray-400 mt-1">All purchase orders generated from confirmed events</p>
        </div>
        <div className="flex gap-2">
          {Object.entries(STATUS_CONFIG).map(([status, cfg]) => {
            const count = totalByStatus[status] || 0;
            if (!count) return null;
            return (
              <button key={status} onClick={() => setFilterStatus(filterStatus === status ? "" : status)}
                className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border transition-colors ${
                  filterStatus === status ? cfg.color + " border-current" : "border-gray-200 text-gray-500 hover:border-gray-300"
                }`}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: cfg.dot }} />
                {cfg.label} {count}
              </button>
            );
          })}
          {filterStatus && (
            <button onClick={() => setFilterStatus("")} className="text-xs text-gray-400 hover:text-gray-700 px-2">Clear</button>
          )}
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Orders", value: orders.length },
          { label: "Draft",        value: totalByStatus.draft    || 0 },
          { label: "Sent",         value: totalByStatus.sent     || 0 },
          { label: "Value (Active)", value: `$${grandTotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white rounded-xl p-4 border border-gray-200 text-center">
            <div className="font-playfair text-xl text-flora-gold">{value}</div>
            <div className="text-xs text-gray-400 mt-1 font-medium uppercase tracking-wide">{label}</div>
          </div>
        ))}
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="text-center text-gray-400 text-sm py-16">Loading orders…</div>
        ) : orders.length === 0 ? (
          <div className="text-center py-16">
            <ShoppingCart size={40} className="mx-auto text-gray-200 mb-4" />
            <p className="text-sm font-medium text-gray-400">No purchase orders yet</p>
            <p className="text-xs text-gray-400 mt-1">
              Confirm an event in Event Planner and click "Generate PO"
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                {["PO Number", "Event", "Vendor", "Required By", "Stems", "Total", "Status", ""].map(h => (
                  <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wide px-5 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {orders.map(o => {
                const sc = STATUS_CONFIG[o.status] || STATUS_CONFIG.draft;
                return (
                  <tr key={o.id} className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer"
                    onClick={() => setViewingId(o.id)}>
                    <td className="px-5 py-3 font-mono text-xs font-semibold text-gray-600">{o.po_number}</td>
                    <td className="px-5 py-3 font-medium text-gray-800">{o.event_name}</td>
                    <td className="px-5 py-3 text-gray-600">{o.vendor_name}</td>
                    <td className="px-5 py-3 text-gray-500 text-xs">
                      {o.required_by_date
                        ? new Date(o.required_by_date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" })
                        : "—"}
                    </td>
                    <td className="px-5 py-3 text-gray-600">{o.line_count} varieties</td>
                    <td className="px-5 py-3 font-semibold text-flora-gold">${o.total_amount?.toFixed(2)}</td>
                    <td className="px-5 py-3">
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${sc.color}`}>{sc.label}</span>
                    </td>
                    <td className="px-5 py-3">
                      <button onClick={e => { e.stopPropagation(); setViewingId(o.id); }}
                        className="text-gray-300 hover:text-flora-gold transition-colors">
                        <Eye size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {viewingId && <PODetail orderId={viewingId} onClose={() => setViewingId(null)} />}

      <style>{`.font-playfair { font-family: 'Playfair Display', serif; }`}</style>
    </div>
  );
}
