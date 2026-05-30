import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { flora } from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, X, Leaf, Store } from "lucide-react";

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function FlowerForm({ flower, onClose, onSaved }) {
  const isEdit = !!flower;
  const [form, setForm] = useState({
    common_name:        flower?.common_name        || "",
    variety:            flower?.variety            || "",
    color:              flower?.color              || "",
    cost_per_stem:      flower?.cost_per_stem      || "",
    bunch_size:         flower?.bunch_size         || 10,
    default_buffer_pct: flower?.default_buffer_pct || 10,
    season_months:      flower?.season_months      || [],
    season_notes:       flower?.season_notes       || "",
  });

  const qc = useQueryClient();
  const mut = useMutation({
    mutationFn: (data) =>
      isEdit ? flora.updateFlower(flower.id, data) : flora.createFlower(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["flora-flowers"] });
      toast.success(isEdit ? "Flower updated" : "Flower added");
      onSaved();
    },
    onError: () => toast.error("Failed to save"),
  });

  const toggleMonth = (m) => {
    setForm(f => ({
      ...f,
      season_months: f.season_months.includes(m)
        ? f.season_months.filter(x => x !== m)
        : [...f.season_months, m].sort((a, b) => a - b),
    }));
  };

  const handleSave = () => {
    if (!form.common_name.trim()) return toast.error("Name required");
    mut.mutate({
      ...form,
      cost_per_stem:      parseFloat(form.cost_per_stem) || 0,
      bunch_size:         parseInt(form.bunch_size) || 10,
      default_buffer_pct: parseFloat(form.default_buffer_pct) || 10,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-[480px] max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="font-playfair text-lg text-gray-900">{isEdit ? "Edit Flower" : "Add Flower"}</h2>
          <button onClick={onClose}><X size={16} className="text-gray-400" /></button>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label-xs">Common Name *</label>
              <input value={form.common_name} onChange={e => setForm(f => ({ ...f, common_name: e.target.value }))}
                className="input-field" placeholder="Garden Rose" />
            </div>
            <div>
              <label className="label-xs">Variety</label>
              <input value={form.variety} onChange={e => setForm(f => ({ ...f, variety: e.target.value }))}
                className="input-field" placeholder="White Ohara" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="label-xs">Color</label>
              <input value={form.color} onChange={e => setForm(f => ({ ...f, color: e.target.value }))}
                className="input-field" placeholder="Blush" />
            </div>
            <div>
              <label className="label-xs">Cost / Stem ($)</label>
              <input type="number" step="0.01" value={form.cost_per_stem}
                onChange={e => setForm(f => ({ ...f, cost_per_stem: e.target.value }))}
                className="input-field" placeholder="2.40" />
            </div>
            <div>
              <label className="label-xs">Bunch Size</label>
              <input type="number" min="1" value={form.bunch_size}
                onChange={e => setForm(f => ({ ...f, bunch_size: e.target.value }))}
                className="input-field" />
            </div>
          </div>
          <div>
            <label className="label-xs">Default Buffer %</label>
            <input type="number" min="0" max="100" value={form.default_buffer_pct}
              onChange={e => setForm(f => ({ ...f, default_buffer_pct: e.target.value }))}
              className="input-field w-32" />
          </div>
          <div>
            <label className="label-xs">Season Months (click to toggle)</label>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {MONTHS.map((m, i) => {
                const num = i + 1;
                const active = form.season_months.includes(num);
                return (
                  <button key={m} onClick={() => toggleMonth(num)}
                    className={`text-xs font-semibold px-2.5 py-1 rounded-lg border transition-colors ${
                      active ? "bg-flora-sage-lt text-flora-sage border-flora-sage/30" : "bg-gray-50 text-gray-400 border-gray-200 hover:border-gray-300"
                    }`}>
                    {m}
                  </button>
                );
              })}
            </div>
          </div>
          <div>
            <label className="label-xs">Season Notes</label>
            <input value={form.season_notes} onChange={e => setForm(f => ({ ...f, season_notes: e.target.value }))}
              className="input-field" placeholder="Peak April–June, premium pricing off-season" />
          </div>
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={handleSave} disabled={mut.isPending}
            className="bg-flora-gold text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50">
            {mut.isPending ? "Saving…" : "Save"}
          </button>
          <button onClick={onClose} className="text-sm text-gray-400 hover:text-gray-700 px-3">Cancel</button>
        </div>
      </div>
    </div>
  );
}

function VendorForm({ vendor, onClose, onSaved }) {
  const isEdit = !!vendor;
  const [form, setForm] = useState({
    name:            vendor?.name            || "",
    contact_name:    vendor?.contact_name    || "",
    email:           vendor?.email           || "",
    phone:           vendor?.phone           || "",
    lead_days:       vendor?.lead_days       || 3,
    min_order_value: vendor?.min_order_value || 0,
    notes:           vendor?.notes           || "",
  });
  const qc = useQueryClient();
  const mut = useMutation({
    mutationFn: (data) =>
      isEdit ? flora.updateVendor(vendor.id, data) : flora.createVendor(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["flora-vendors"] });
      toast.success(isEdit ? "Vendor updated" : "Vendor added");
      onSaved();
    },
    onError: () => toast.error("Failed to save"),
  });
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-96">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="font-playfair text-lg text-gray-900">{isEdit ? "Edit Vendor" : "Add Vendor"}</h2>
          <button onClick={onClose}><X size={16} className="text-gray-400" /></button>
        </div>
        <div className="p-6 space-y-3">
          <div>
            <label className="label-xs">Vendor Name *</label>
            <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="input-field" placeholder="Mayesh Wholesale" />
          </div>
          <div>
            <label className="label-xs">Contact Name</label>
            <input value={form.contact_name} onChange={e => setForm(f => ({ ...f, contact_name: e.target.value }))}
              className="input-field" />
          </div>
          <div>
            <label className="label-xs">Email</label>
            <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className="input-field" />
          </div>
          <div>
            <label className="label-xs">Phone</label>
            <input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
              className="input-field" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-xs">Lead Days</label>
              <input type="number" min="1" value={form.lead_days}
                onChange={e => setForm(f => ({ ...f, lead_days: parseInt(e.target.value) || 3 }))}
                className="input-field" />
            </div>
            <div>
              <label className="label-xs">Min Order ($)</label>
              <input type="number" value={form.min_order_value}
                onChange={e => setForm(f => ({ ...f, min_order_value: parseFloat(e.target.value) || 0 }))}
                className="input-field" />
            </div>
          </div>
          <div>
            <label className="label-xs">Notes</label>
            <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              rows={2} className="input-field resize-none" />
          </div>
        </div>
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={() => mut.mutate(form)} disabled={mut.isPending}
            className="bg-flora-gold text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50">
            {mut.isPending ? "Saving…" : "Save"}
          </button>
          <button onClick={onClose} className="text-sm text-gray-400 hover:text-gray-700 px-3">Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default function FloraCatalogPage() {
  const [tab, setTab] = useState("flowers");
  const [flowerForm, setFlowerForm] = useState(null);  // null=hidden, true=new, object=edit
  const [vendorForm, setVendorForm] = useState(null);
  const [search, setSearch] = useState("");

  const { data: flowers = [], isLoading: fLoading } = useQuery({
    queryKey: ["flora-flowers"],
    queryFn: () => flora.flowers().then(r => r.data),
  });
  const { data: vendors = [], isLoading: vLoading } = useQuery({
    queryKey: ["flora-vendors"],
    queryFn: () => flora.vendors().then(r => r.data),
  });

  const filteredFlowers = flowers.filter(f =>
    !search || f.display_name.toLowerCase().includes(search.toLowerCase())
  );
  const filteredVendors = vendors.filter(v =>
    !search || v.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-7 space-y-6 bg-flora-cream min-h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-playfair text-2xl text-gray-900">Catalog</h1>
          <p className="text-sm text-gray-400 mt-1">Flower catalog and vendor directory</p>
        </div>
        <button
          onClick={() => tab === "flowers" ? setFlowerForm(true) : setVendorForm(true)}
          className="flex items-center gap-2 bg-flora-gold text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-amber-700 transition-colors">
          <Plus size={15} /> Add {tab === "flowers" ? "Flower" : "Vendor"}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 bg-white border border-gray-200 rounded-xl p-1 w-fit">
        {[
          { key: "flowers", icon: Leaf,  label: `Flowers (${flowers.length})` },
          { key: "vendors", icon: Store, label: `Vendors (${vendors.length})` },
        ].map(({ key, icon: Icon, label }) => (
          <button key={key} onClick={() => { setTab(key); setSearch(""); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
              tab === key ? "bg-flora-gold-lt text-flora-gold" : "text-gray-500 hover:text-gray-700"
            }`}>
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>

      {/* Search */}
      <input value={search} onChange={e => setSearch(e.target.value)}
        placeholder={`Search ${tab}…`}
        className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-flora-gold w-64 bg-white" />

      {/* Flowers Table */}
      {tab === "flowers" && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                {["Flower", "Variety", "Color", "Cost/Stem", "Bunch Size", "Buffer %", "Season", ""].map(h => (
                  <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wide px-5 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fLoading && (
                <tr><td colSpan="8" className="text-center text-gray-400 py-10 text-sm">Loading…</td></tr>
              )}
              {!fLoading && filteredFlowers.length === 0 && (
                <tr><td colSpan="8" className="text-center text-gray-400 py-10 text-sm">
                  No flowers yet — add your catalog to start building recipes.
                </td></tr>
              )}
              {filteredFlowers.map(f => (
                <tr key={f.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-5 py-3 font-medium text-gray-800">{f.common_name}</td>
                  <td className="px-5 py-3 text-gray-500">{f.variety || "—"}</td>
                  <td className="px-5 py-3 text-gray-500">{f.color || "—"}</td>
                  <td className="px-5 py-3 font-semibold text-flora-gold">${f.cost_per_stem?.toFixed(2)}</td>
                  <td className="px-5 py-3 text-gray-600">{f.bunch_size}</td>
                  <td className="px-5 py-3 text-gray-600">{f.default_buffer_pct}%</td>
                  <td className="px-5 py-3 text-xs">
                    {f.season_months?.length === 12 || !f.season_months?.length
                      ? <span className="text-gray-400">Year-round</span>
                      : f.season_months.map(m => MONTHS[m - 1]).join(", ")
                    }
                  </td>
                  <td className="px-5 py-3">
                    <button onClick={() => setFlowerForm(f)}
                      className="text-xs font-semibold text-gray-400 hover:text-flora-gold transition-colors">
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Vendors Table */}
      {tab === "vendors" && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                {["Vendor", "Contact", "Email", "Phone", "Lead Days", "Min Order", ""].map(h => (
                  <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wide px-5 py-3">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {vLoading && (
                <tr><td colSpan="7" className="text-center text-gray-400 py-10 text-sm">Loading…</td></tr>
              )}
              {!vLoading && filteredVendors.length === 0 && (
                <tr><td colSpan="7" className="text-center text-gray-400 py-10 text-sm">
                  No vendors yet — add your wholesale suppliers.
                </td></tr>
              )}
              {filteredVendors.map(v => (
                <tr key={v.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-5 py-3 font-medium text-gray-800">{v.name}</td>
                  <td className="px-5 py-3 text-gray-500">{v.contact_name || "—"}</td>
                  <td className="px-5 py-3 text-gray-500">{v.email || "—"}</td>
                  <td className="px-5 py-3 text-gray-500">{v.phone || "—"}</td>
                  <td className="px-5 py-3 text-gray-600">{v.lead_days} days</td>
                  <td className="px-5 py-3 text-gray-600">${v.min_order_value?.toFixed(0)}</td>
                  <td className="px-5 py-3">
                    <button onClick={() => setVendorForm(v)}
                      className="text-xs font-semibold text-gray-400 hover:text-flora-gold transition-colors">
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      {flowerForm && (
        <FlowerForm
          flower={flowerForm === true ? null : flowerForm}
          onClose={() => setFlowerForm(null)}
          onSaved={() => setFlowerForm(null)}
        />
      )}
      {vendorForm && (
        <VendorForm
          vendor={vendorForm === true ? null : vendorForm}
          onClose={() => setVendorForm(null)}
          onSaved={() => setVendorForm(null)}
        />
      )}

      <style>{`
        .label-xs { display: block; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; margin-bottom: 0.375rem; }
        .input-field { width: 100%; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 0.5rem 0.75rem; font-size: 0.875rem; outline: none; }
        .input-field:focus { border-color: #B8860B; }
        .font-playfair { font-family: 'Playfair Display', serif; }
      `}</style>
    </div>
  );
}
