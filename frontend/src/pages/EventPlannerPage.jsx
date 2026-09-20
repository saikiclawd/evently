import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { flora } from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, Calendar, Trash2, X, CheckCircle, ShoppingCart, ChevronDown } from "lucide-react";

const EVENT_TYPES = ["wedding","corporate","gala","bar_mitzvah","birthday","other"];
const STATUS_CONFIG = {
  inquiry:       { label: "Inquiry",     color: "bg-gray-100 text-gray-600" },
  proposal_sent: { label: "Proposal",    color: "bg-blue-50 text-blue-600" },
  confirmed:     { label: "Confirmed",   color: "bg-flora-sage-lt text-flora-sage" },
  in_production: { label: "In Prod.",    color: "bg-orange-50 text-orange-600" },
  completed:     { label: "Completed",   color: "bg-gray-100 text-gray-400" },
  cancelled:     { label: "Cancelled",   color: "bg-red-50 text-red-400" },
};

function NewEventModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    name: "", event_date: "", event_type: "wedding",
    venue: "", quoted_budget: "", guest_count: "", brief_notes: "",
  });
  const createMutation = useMutation({
    mutationFn: (data) => flora.createEvent(data),
    onSuccess: (r) => { toast.success("Event created"); onCreated(r.data); },
    onError: () => toast.error("Failed to create event"),
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const handleSave = () => {
    if (!form.name.trim()) return toast.error("Event name required");
    createMutation.mutate({
      ...form,
      quoted_budget: parseFloat(form.quoted_budget) || 0,
      guest_count:   form.guest_count ? parseInt(form.guest_count) : null,
    });
  };
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-[520px] max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="font-playfair text-lg text-gray-900">New Event</h2>
          <button onClick={onClose}><X size={18} className="text-gray-400" /></button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="label-xs">Event Name *</label>
            <input value={form.name} onChange={e => set("name", e.target.value)}
              className="input-field" placeholder="Chen-Patel Wedding" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label-xs">Date</label>
              <input type="date" value={form.event_date} onChange={e => set("event_date", e.target.value)}
                className="input-field" />
            </div>
            <div>
              <label className="label-xs">Type</label>
              <select value={form.event_type} onChange={e => set("event_type", e.target.value)}
                className="input-field capitalize">
                {EVENT_TYPES.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="label-xs">Venue</label>
            <input value={form.venue} onChange={e => set("venue", e.target.value)}
              className="input-field" placeholder="The Grand Ballroom" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label-xs">Quoted Budget ($)</label>
              <input type="number" value={form.quoted_budget} onChange={e => set("quoted_budget", e.target.value)}
                className="input-field" placeholder="8500" />
            </div>
            <div>
              <label className="label-xs">Guest Count</label>
              <input type="number" value={form.guest_count} onChange={e => set("guest_count", e.target.value)}
                className="input-field" placeholder="150" />
            </div>
          </div>
          <div>
            <label className="label-xs">Style Brief / Notes</label>
            <textarea value={form.brief_notes} onChange={e => set("brief_notes", e.target.value)}
              rows={3} className="input-field resize-none" placeholder="Garden romantic, blush and ivory, no lilies…" />
          </div>
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={handleSave} disabled={createMutation.isPending}
            className="bg-flora-gold text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50">
            {createMutation.isPending ? "Creating…" : "Create Event"}
          </button>
          <button onClick={onClose} className="text-sm text-gray-400 hover:text-gray-700 px-3">Cancel</button>
        </div>
      </div>
    </div>
  );
}

function AddArrangementModal({ eventId, onClose, onAdded }) {
  const [recipeId, setRecipeId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [location, setLocation] = useState("");
  const { data: recipes = [] } = useQuery({
    queryKey: ["flora-recipes"],
    queryFn: () => flora.recipes({ status: "published" }).then(r => r.data),
  });
  const addMutation = useMutation({
    mutationFn: (data) => flora.addArrangement(eventId, data),
    onSuccess: () => { toast.success("Arrangement added"); onAdded(); onClose(); },
    onError: () => toast.error("Failed to add arrangement"),
  });
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-96">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="font-playfair text-base text-gray-900">Add Arrangement</h3>
          <button onClick={onClose}><X size={16} className="text-gray-400" /></button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="label-xs">Recipe *</label>
            <select value={recipeId} onChange={e => setRecipeId(e.target.value)} className="input-field">
              <option value="">Select a recipe…</option>
              {recipes.map(r => (
                <option key={r.id} value={r.id}>{r.name} — {r.total_stems} stems</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label-xs">Quantity</label>
            <input type="number" min="1" value={quantity} onChange={e => setQuantity(parseInt(e.target.value) || 1)}
              className="input-field" />
          </div>
          <div>
            <label className="label-xs">Location / Note</label>
            <input value={location} onChange={e => setLocation(e.target.value)}
              className="input-field" placeholder="e.g. Tables 1–12, Ceremony arch" />
          </div>
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button
            onClick={() => {
              if (!recipeId) return toast.error("Select a recipe");
              addMutation.mutate({ recipe_id: recipeId, quantity, location_note: location });
            }}
            disabled={addMutation.isPending}
            className="bg-flora-gold text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50">
            Add
          </button>
          <button onClick={onClose} className="text-sm text-gray-400 hover:text-gray-700 px-3">Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default function EventPlannerPage() {
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState(null);
  const [showNewEvent, setShowNewEvent] = useState(false);
  const [showAddArr, setShowAddArr] = useState(false);
  const [filterStatus, setFilterStatus] = useState("");

  const { data: events = [], isLoading } = useQuery({
    queryKey: ["flora-events"],
    queryFn: () => flora.events().then(r => r.data),
  });

  const { data: event } = useQuery({
    queryKey: ["flora-event", selectedId],
    queryFn: () => flora.getEvent(selectedId).then(r => r.data),
    enabled: !!selectedId,
  });

  const { data: stemSummary } = useQuery({
    queryKey: ["flora-stems", selectedId],
    queryFn: () => flora.stemSummary(selectedId).then(r => r.data),
    enabled: !!selectedId,
  });

  const removeArr = useMutation({
    mutationFn: ({ eid, aid }) => flora.removeArrangement(eid, aid),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["flora-event", selectedId] }); qc.invalidateQueries({ queryKey: ["flora-stems", selectedId] }); },
  });

  const updateQty = useMutation({
    mutationFn: ({ eid, aid, qty }) => flora.updateArrangement(eid, aid, { quantity: qty }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["flora-event", selectedId] }); qc.invalidateQueries({ queryKey: ["flora-stems", selectedId] }); },
  });

  const confirmMut = useMutation({
    mutationFn: (id) => flora.confirmEvent(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["flora-events"] }); qc.invalidateQueries({ queryKey: ["flora-event", selectedId] }); toast.success("Event confirmed"); },
  });

  const genPO = useMutation({
    mutationFn: (id) => flora.generatePO(id),
    onSuccess: () => { toast.success("Purchase orders generated"); },
    onError: (e) => toast.error(e?.response?.data?.error || "PO generation failed"),
  });

  const filtered = events.filter(e => !filterStatus || e.status === filterStatus);

  const marginColor = (pct) => {
    if (pct >= 50) return "text-green-600";
    if (pct >= 30) return "text-amber-600";
    return "text-red-500";
  };

  return (
    <div className="h-full flex overflow-hidden bg-flora-cream">
      {/* LEFT — Event List */}
      <div className="w-72 border-r border-gray-200 bg-white flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <h1 className="font-playfair text-lg text-gray-900">Events</h1>
            <button onClick={() => setShowNewEvent(true)}
              className="w-7 h-7 rounded-lg bg-flora-gold text-white flex items-center justify-center hover:bg-amber-700 transition-colors">
              <Plus size={15} />
            </button>
          </div>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-flora-gold text-gray-500">
            <option value="">All statuses</option>
            {Object.entries(STATUS_CONFIG).map(([v, c]) => (
              <option key={v} value={v}>{c.label}</option>
            ))}
          </select>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading && <div className="text-center text-sm text-gray-400 py-8">Loading…</div>}
          {!isLoading && filtered.length === 0 && (
            <div className="text-center text-gray-400 text-sm py-8">
              <Calendar size={28} className="mx-auto mb-2 opacity-30" />
              No events yet
            </div>
          )}
          {filtered.map(e => {
            const sc = STATUS_CONFIG[e.status] || STATUS_CONFIG.inquiry;
            return (
              <button key={e.id} onClick={() => setSelectedId(e.id)}
                className={`w-full text-left px-3 py-3 rounded-lg mb-1 transition-colors ${
                  selectedId === e.id ? "bg-flora-gold-lt border border-flora-gold/30" : "hover:bg-gray-50"
                }`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-800 truncate pr-2">{e.name}</span>
                  <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${sc.color}`}>{sc.label}</span>
                </div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {e.event_date ? new Date(e.event_date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "No date"}
                  {e.venue ? ` · ${e.venue}` : ""}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* RIGHT — Event Build */}
      <div className="flex-1 overflow-y-auto">
        {!selectedId ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <Calendar size={48} className="mb-4 opacity-20" />
            <p className="text-base font-medium">Select or create an event</p>
            <button onClick={() => setShowNewEvent(true)}
              className="mt-4 flex items-center gap-2 bg-flora-gold text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-amber-700 transition-colors">
              <Plus size={15} /> New Event
            </button>
          </div>
        ) : !event ? (
          <div className="h-full flex items-center justify-center text-gray-400 text-sm">Loading…</div>
        ) : (
          <div className="p-7 space-y-6">
            {/* Event Header */}
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-playfair text-2xl text-gray-900">{event.name}</h2>
                <div className="flex items-center gap-3 mt-1.5 text-sm text-gray-500">
                  <span>{event.event_date ? new Date(event.event_date + "T00:00:00").toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" }) : "Date TBD"}</span>
                  {event.venue && <span>· {event.venue}</span>}
                  <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${STATUS_CONFIG[event.status]?.color}`}>
                    {STATUS_CONFIG[event.status]?.label}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                {event.status === "inquiry" || event.status === "proposal_sent" ? (
                  <button onClick={() => confirmMut.mutate(event.id)}
                    className="flex items-center gap-1.5 text-sm font-semibold text-white bg-flora-sage px-3 py-1.5 rounded-lg hover:bg-green-700 transition-colors">
                    <CheckCircle size={14} /> Confirm Event
                  </button>
                ) : null}
                {event.status === "confirmed" && (
                  <button onClick={() => genPO.mutate(event.id)} disabled={genPO.isPending}
                    className="flex items-center gap-1.5 text-sm font-semibold text-white bg-flora-gold px-3 py-1.5 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50">
                    <ShoppingCart size={14} /> {genPO.isPending ? "Generating…" : "Generate PO"}
                  </button>
                )}
              </div>
            </div>

            {/* Budget / Margin KPIs */}
            {stemSummary && (
              <div className="grid grid-cols-4 gap-4">
                {[
                  { label: "Quoted Budget",  value: `$${stemSummary.quoted_budget?.toLocaleString()}` },
                  { label: "Est. Cost",       value: `$${stemSummary.estimated_cost?.toLocaleString()}` },
                  { label: "Margin",          value: `${stemSummary.margin_pct}%`, special: true, pct: stemSummary.margin_pct },
                  { label: "Total Stems",     value: stemSummary.total_stems?.toLocaleString() },
                ].map(({ label, value, special, pct }) => (
                  <div key={label} className="bg-white rounded-xl p-4 border border-gray-200 text-center">
                    <div className={`font-playfair text-xl ${special ? marginColor(pct) : "text-flora-gold"}`}>{value}</div>
                    <div className="text-xs text-gray-400 mt-1 font-medium uppercase tracking-wide">{label}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Arrangements */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
                <h3 className="text-sm font-bold text-gray-700">Event Build</h3>
                <button onClick={() => setShowAddArr(true)}
                  className="flex items-center gap-1.5 text-xs font-semibold text-flora-gold hover:text-amber-700 transition-colors">
                  <Plus size={13} /> Add Recipe
                </button>
              </div>
              {!event.arrangements?.length ? (
                <div className="py-12 text-center text-gray-400">
                  <p className="text-sm mb-3">No arrangements yet.</p>
                  <button onClick={() => setShowAddArr(true)}
                    className="text-xs font-semibold text-flora-gold hover:underline">
                    + Add first arrangement
                  </button>
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100">
                      {["Arrangement", "Location", "Qty", "Stems/Unit", "Total Stems", "Cost", ""].map(h => (
                        <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wide px-5 py-3">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {event.arrangements.map(arr => (
                      <tr key={arr.id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="px-5 py-3 font-medium text-gray-800">{arr.recipe_name}</td>
                        <td className="px-5 py-3 text-gray-400 text-xs">{arr.location_note || "—"}</td>
                        <td className="px-5 py-3">
                          <input type="number" min="1" defaultValue={arr.quantity}
                            onBlur={e => {
                              const qty = parseInt(e.target.value) || 1;
                              if (qty !== arr.quantity) updateQty.mutate({ eid: event.id, aid: arr.id, qty });
                            }}
                            className="w-16 border border-gray-200 rounded px-2 py-1 text-center text-sm focus:outline-none focus:border-flora-gold" />
                        </td>
                        <td className="px-5 py-3 text-gray-600">{arr.stems_per_unit}</td>
                        <td className="px-5 py-3 font-semibold text-gray-900">{arr.total_stems?.toLocaleString()}</td>
                        <td className="px-5 py-3 text-flora-gold font-semibold">${arr.total_cost?.toFixed(2)}</td>
                        <td className="px-5 py-3">
                          <button onClick={() => removeArr.mutate({ eid: event.id, aid: arr.id })}
                            className="text-gray-300 hover:text-red-400 transition-colors">
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Stem breakdown by flower */}
            {stemSummary?.stems_by_flower?.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
                  <h3 className="text-sm font-bold text-gray-700">Stem Requirements by Flower</h3>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100">
                      {["Flower", "Buffered Stems", "Bunches", "Bunch Size", "Unit Cost", "Line Cost"].map(h => (
                        <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wide px-5 py-3">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {stemSummary.stems_by_flower.map(s => (
                      <tr key={s.flower_id} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="px-5 py-3 font-medium text-gray-800">{s.display_name}</td>
                        <td className="px-5 py-3 font-semibold text-gray-900">{s.buffered_stems}</td>
                        <td className="px-5 py-3 text-gray-600">{s.bunches}</td>
                        <td className="px-5 py-3 text-gray-400">{s.bunch_size}</td>
                        <td className="px-5 py-3 text-gray-600">${s.unit_cost?.toFixed(2)}</td>
                        <td className="px-5 py-3 font-semibold text-flora-gold">${s.line_cost?.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-flora-cream">
                      <td className="px-5 py-3 font-bold text-gray-700">Total</td>
                      <td className="px-5 py-3 font-bold text-gray-900">{stemSummary.total_stems}</td>
                      <td colSpan="3" />
                      <td className="px-5 py-3 font-bold text-flora-gold font-playfair text-base">
                        ${stemSummary.estimated_cost?.toFixed(2)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {showNewEvent && (
        <NewEventModal
          onClose={() => setShowNewEvent(false)}
          onCreated={(e) => { setSelectedId(e.id); setShowNewEvent(false); qc.invalidateQueries({ queryKey: ["flora-events"] }); }}
        />
      )}
      {showAddArr && selectedId && (
        <AddArrangementModal
          eventId={selectedId}
          onClose={() => setShowAddArr(false)}
          onAdded={() => { qc.invalidateQueries({ queryKey: ["flora-event", selectedId] }); qc.invalidateQueries({ queryKey: ["flora-stems", selectedId] }); }}
        />
      )}

      {/* Inline CSS for quick helpers */}
      <style>{`
        .label-xs { display: block; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; margin-bottom: 0.375rem; }
        .input-field { width: 100%; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 0.5rem 0.75rem; font-size: 0.875rem; outline: none; }
        .input-field:focus { border-color: #B8860B; }
        .font-playfair { font-family: 'Playfair Display', serif; }
      `}</style>
    </div>
  );
}
