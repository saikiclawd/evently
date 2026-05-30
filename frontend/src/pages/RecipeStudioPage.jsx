import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { flora } from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, Save, BookOpen, Trash2, Copy, CheckCircle, ChevronDown, X } from "lucide-react";

const CATEGORIES = [
  { value: "centerpiece",    label: "Centerpiece" },
  { value: "bouquet_bridal", label: "Bouquet (Bridal)" },
  { value: "bouquet_bm",     label: "Bouquet (Bridesmaid)" },
  { value: "arch_full",      label: "Arch (Full)" },
  { value: "arch_half",      label: "Arch (Half)" },
  { value: "chuppah",        label: "Chuppah / Huppah" },
  { value: "runner",         label: "Floral Runner" },
  { value: "sweetheart",     label: "Sweetheart Table" },
  { value: "ceremony",       label: "Ceremony Florals" },
  { value: "backdrop",       label: "Backdrop" },
  { value: "hanging",        label: "Hanging / Cloud" },
  { value: "aisle",          label: "Aisle Markers" },
  { value: "stage",          label: "Stage Florals" },
  { value: "boutonniere",    label: "Boutonniere" },
  { value: "cake",           label: "Cake Florals" },
  { value: "welcome",        label: "Welcome Arrangement" },
  { value: "other",          label: "Other" },
];

const STATUS_COLORS = {
  draft:     "bg-gray-100 text-gray-600",
  published: "bg-flora-sage-lt text-flora-sage",
  archived:  "bg-red-50 text-red-500",
};

function StemRow({ stem, flowers, onChange, onRemove }) {
  return (
    <div className="grid grid-cols-[1fr_80px_80px_80px_36px] gap-2 items-center py-2 border-b border-gray-100 last:border-0">
      <select
        value={stem.flower_id || ""}
        onChange={e => onChange({ ...stem, flower_id: e.target.value })}
        className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:border-flora-gold"
      >
        <option value="">Select flower…</option>
        {flowers.map(f => (
          <option key={f.id} value={f.id}>{f.display_name}</option>
        ))}
      </select>
      <input
        type="number" min="1"
        value={stem.quantity || 1}
        onChange={e => onChange({ ...stem, quantity: parseInt(e.target.value) || 1 })}
        className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 text-center focus:outline-none focus:border-flora-gold"
        placeholder="Qty"
      />
      <input
        type="number" step="0.01" min="0"
        value={stem.unit_cost_override || ""}
        onChange={e => onChange({ ...stem, unit_cost_override: e.target.value ? parseFloat(e.target.value) : null })}
        className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 text-center focus:outline-none focus:border-flora-gold"
        placeholder="$/stem"
      />
      <input
        type="number" min="0" max="100"
        value={stem.buffer_pct_override || ""}
        onChange={e => onChange({ ...stem, buffer_pct_override: e.target.value ? parseFloat(e.target.value) : null })}
        className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 text-center focus:outline-none focus:border-flora-gold"
        placeholder="%"
      />
      <button onClick={onRemove} className="text-gray-300 hover:text-red-400 transition-colors flex items-center justify-center">
        <X size={15} />
      </button>
    </div>
  );
}

function RecipeForm({ recipe, flowers, onClose, onSaved }) {
  const qc = useQueryClient();
  const isEdit = !!recipe;

  const [form, setForm] = useState({
    name:          recipe?.name          || "",
    category:      recipe?.category      || "centerpiece",
    markup_pct:    recipe?.markup_pct    || 20,
    labor_minutes: recipe?.labor_minutes || 0,
    tags:          (recipe?.tags || []).join(", "),
  });
  const [stems, setStems] = useState(
    recipe?.stems?.length
      ? recipe.stems.map(s => ({ ...s, _id: s.id || Math.random() }))
      : [{ _id: Math.random(), flower_id: "", quantity: 1 }]
  );

  const saveMutation = useMutation({
    mutationFn: (payload) =>
      isEdit ? flora.updateRecipe(recipe.id, payload) : flora.createRecipe(payload),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["flora-recipes"] });
      toast.success(isEdit ? "Recipe saved" : "Recipe created");
      onSaved(res.data);
    },
    onError: () => toast.error("Failed to save recipe"),
  });

  const totalStems = stems.reduce((s, r) => s + (parseInt(r.quantity) || 0), 0);
  const totalCost  = stems.reduce((s, r) => {
    const flower = flowers.find(f => f.id === r.flower_id);
    const cost   = r.unit_cost_override ?? (flower?.cost_per_stem ?? 0);
    return s + (parseInt(r.quantity) || 0) * parseFloat(cost);
  }, 0);

  const handleSave = () => {
    if (!form.name.trim()) return toast.error("Recipe name is required");
    const validStems = stems.filter(s => s.flower_id && s.quantity > 0);
    if (!validStems.length) return toast.error("Add at least one stem");
    saveMutation.mutate({
      ...form,
      tags: form.tags.split(",").map(t => t.trim()).filter(Boolean),
      stems: validStems,
      change_summary: isEdit ? "Updated stems" : "Initial version",
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <h2 className="font-playfair text-lg text-gray-900">
          {isEdit ? "Edit Recipe" : "New Recipe"}
        </h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Name + Category */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Recipe Name</label>
            <input
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-flora-gold"
              placeholder="e.g. Garden Romance Centerpiece"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Category</label>
            <select
              value={form.category}
              onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-flora-gold"
            >
              {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>
        </div>

        {/* Markup + Labor */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Markup %</label>
            <input
              type="number" min="0" max="300"
              value={form.markup_pct}
              onChange={e => setForm(f => ({ ...f, markup_pct: parseFloat(e.target.value) || 0 }))}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-flora-gold"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Labor (minutes / unit)</label>
            <input
              type="number" min="0"
              value={form.labor_minutes}
              onChange={e => setForm(f => ({ ...f, labor_minutes: parseInt(e.target.value) || 0 }))}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-flora-gold"
            />
          </div>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Tags (comma-separated)</label>
          <input
            value={form.tags}
            onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-flora-gold"
            placeholder="garden, romantic, blush"
          />
        </div>

        {/* Stem Line Items */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Stem Ingredients</label>
            <button
              onClick={() => setStems(s => [...s, { _id: Math.random(), flower_id: "", quantity: 1 }])}
              className="flex items-center gap-1 text-xs font-semibold text-flora-gold hover:text-flora-rose transition-colors"
            >
              <Plus size={13} /> Add Stem
            </button>
          </div>

          {/* Column headers */}
          <div className="grid grid-cols-[1fr_80px_80px_80px_36px] gap-2 mb-1">
            {["Flower", "Qty", "$/Stem", "Buffer%", ""].map((h, i) => (
              <div key={i} className="text-[10px] font-bold text-gray-400 uppercase tracking-wide text-center first:text-left">{h}</div>
            ))}
          </div>

          {stems.map((stem, idx) => (
            <StemRow
              key={stem._id}
              stem={stem}
              flowers={flowers}
              onChange={updated => setStems(s => s.map((r, i) => i === idx ? updated : r))}
              onRemove={() => setStems(s => s.filter((_, i) => i !== idx))}
            />
          ))}

          {/* Totals */}
          <div className="mt-3 bg-flora-cream rounded-lg p-3 flex items-center justify-between">
            <span className="text-sm text-gray-500 font-medium">{totalStems} stems / unit</span>
            <span className="text-base font-bold text-flora-gold font-playfair">
              ${totalCost.toFixed(2)} / unit
            </span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-200 flex gap-3">
        <button
          onClick={handleSave}
          disabled={saveMutation.isPending}
          className="flex items-center gap-2 bg-flora-gold text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50"
        >
          <Save size={15} /> {saveMutation.isPending ? "Saving…" : "Save Recipe"}
        </button>
        <button onClick={onClose} className="text-sm text-gray-400 hover:text-gray-700 px-3 py-2">Cancel</button>
      </div>
    </div>
  );
}

export default function RecipeStudioPage() {
  const qc = useQueryClient();
  const [selected, setSelected] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const [filterCat, setFilterCat] = useState("");

  const { data: recipes = [], isLoading } = useQuery({
    queryKey: ["flora-recipes"],
    queryFn: () => flora.recipes().then(r => r.data),
  });
  const { data: flowers = [] } = useQuery({
    queryKey: ["flora-flowers"],
    queryFn: () => flora.flowers({ active_only: "true" }).then(r => r.data),
  });
  const { data: selectedRecipe } = useQuery({
    queryKey: ["flora-recipe", selected],
    queryFn: () => flora.getRecipe(selected).then(r => r.data),
    enabled: !!selected && !showForm,
  });

  const publishMutation = useMutation({
    mutationFn: (id) => flora.publishRecipe(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["flora-recipes"] }); toast.success("Published"); },
  });
  const dupMutation = useMutation({
    mutationFn: (id) => flora.duplicateRecipe(id),
    onSuccess: (r) => { qc.invalidateQueries({ queryKey: ["flora-recipes"] }); toast.success("Duplicated"); setSelected(r.data.id); },
  });

  const filtered = recipes.filter(r => {
    const matchSearch = !search || r.name.toLowerCase().includes(search.toLowerCase());
    const matchCat    = !filterCat || r.category === filterCat;
    return matchSearch && matchCat;
  });

  return (
    <div className="h-full flex overflow-hidden bg-flora-cream">
      {/* LEFT — Recipe List */}
      <div className="w-72 border-r border-gray-200 bg-white flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <h1 className="font-playfair text-lg text-gray-900">Recipe Studio</h1>
            <button
              onClick={() => { setSelected(null); setShowForm(true); }}
              className="w-7 h-7 rounded-lg bg-flora-gold text-white flex items-center justify-center hover:bg-amber-700 transition-colors"
            >
              <Plus size={15} />
            </button>
          </div>
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search recipes…"
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-flora-gold"
          />
          <select
            value={filterCat} onChange={e => setFilterCat(e.target.value)}
            className="w-full mt-2 border border-gray-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-flora-gold text-gray-500"
          >
            <option value="">All categories</option>
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {isLoading && <div className="text-center text-gray-400 text-sm py-8">Loading…</div>}
          {!isLoading && filtered.length === 0 && (
            <div className="text-center text-gray-400 text-sm py-8">
              <BookOpen size={28} className="mx-auto mb-2 opacity-30" />
              No recipes yet
            </div>
          )}
          {filtered.map(r => (
            <button
              key={r.id}
              onClick={() => { setSelected(r.id); setShowForm(false); }}
              className={`w-full text-left px-3 py-3 rounded-lg mb-1 transition-colors ${
                selected === r.id && !showForm
                  ? "bg-flora-gold-lt border border-flora-gold/30"
                  : "hover:bg-gray-50"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-800 truncate pr-2">{r.name}</span>
                <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${STATUS_COLORS[r.status] || STATUS_COLORS.draft}`}>
                  {r.status}
                </span>
              </div>
              <div className="text-xs text-gray-400 mt-0.5">
                {CATEGORIES.find(c => c.value === r.category)?.label} · {r.total_stems} stems · ${r.cost_per_unit?.toFixed(2)}/unit
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* RIGHT — Editor / Detail */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {showForm ? (
          <RecipeForm
            recipe={selected ? selectedRecipe : null}
            flowers={flowers}
            onClose={() => { setShowForm(false); }}
            onSaved={(r) => { setSelected(r.id); setShowForm(false); }}
          />
        ) : !selected ? (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
            <BookOpen size={48} className="mb-4 opacity-20" />
            <p className="text-base font-medium">Select a recipe or create one</p>
            <button
              onClick={() => setShowForm(true)}
              className="mt-4 flex items-center gap-2 bg-flora-gold text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-amber-700 transition-colors"
            >
              <Plus size={15} /> New Recipe
            </button>
          </div>
        ) : selectedRecipe ? (
          <div className="flex-1 overflow-y-auto p-7">
            {/* Recipe header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="font-playfair text-2xl text-gray-900">{selectedRecipe.name}</h2>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${STATUS_COLORS[selectedRecipe.status]}`}>
                    {selectedRecipe.status}
                  </span>
                  <span className="text-xs text-gray-400">
                    {CATEGORIES.find(c => c.value === selectedRecipe.category)?.label}
                  </span>
                  {(selectedRecipe.tags || []).map(t => (
                    <span key={t} className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">{t}</span>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowForm(true)}
                  className="flex items-center gap-1.5 text-sm font-semibold text-flora-gold border border-flora-gold px-3 py-1.5 rounded-lg hover:bg-flora-gold-lt transition-colors"
                >
                  Edit
                </button>
                {selectedRecipe.status === "draft" && (
                  <button
                    onClick={() => publishMutation.mutate(selectedRecipe.id)}
                    className="flex items-center gap-1.5 text-sm font-semibold text-white bg-flora-sage px-3 py-1.5 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <CheckCircle size={14} /> Publish
                  </button>
                )}
                <button
                  onClick={() => dupMutation.mutate(selectedRecipe.id)}
                  className="flex items-center gap-1.5 text-sm font-semibold text-gray-500 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Copy size={13} /> Copy
                </button>
              </div>
            </div>

            {/* KPI strip */}
            <div className="grid grid-cols-4 gap-4 mb-7">
              {[
                { label: "Stems / Unit", value: selectedRecipe.total_stems },
                { label: "Cost / Unit", value: `$${selectedRecipe.cost_per_unit?.toFixed(2)}` },
                { label: "Markup", value: `${selectedRecipe.markup_pct}%` },
                { label: "Labor", value: `${selectedRecipe.labor_minutes}min` },
              ].map(({ label, value }) => (
                <div key={label} className="bg-white rounded-xl p-4 border border-gray-200 text-center">
                  <div className="font-playfair text-xl text-flora-gold">{value}</div>
                  <div className="text-xs text-gray-400 mt-1 font-medium uppercase tracking-wide">{label}</div>
                </div>
              ))}
            </div>

            {/* Stem table */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
                <h3 className="text-sm font-bold text-gray-700">Stem Ingredients</h3>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    {["Flower", "Variety", "Color", "Qty / Unit", "Buffer", "Cost / Stem", "Line Cost"].map(h => (
                      <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wide px-5 py-3">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(selectedRecipe.stems || []).map(s => (
                    <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="px-5 py-3 font-medium text-gray-800">{s.flower_name}</td>
                      <td className="px-5 py-3 text-gray-500">{s.flower_variety || "—"}</td>
                      <td className="px-5 py-3 text-gray-500">{s.flower_color || "—"}</td>
                      <td className="px-5 py-3 font-semibold text-gray-800">{s.quantity}</td>
                      <td className="px-5 py-3 text-gray-500">{s.buffer_pct_override ? `${s.buffer_pct_override}%` : "default"}</td>
                      <td className="px-5 py-3 text-gray-600">${s.unit_cost?.toFixed(2)}</td>
                      <td className="px-5 py-3 font-semibold text-flora-gold">${s.line_cost?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-flora-cream">
                    <td colSpan="3" className="px-5 py-3 font-bold text-gray-700">Total</td>
                    <td className="px-5 py-3 font-bold text-gray-900">{selectedRecipe.total_stems} stems</td>
                    <td colSpan="2" />
                    <td className="px-5 py-3 font-bold text-flora-gold font-playfair text-base">
                      ${selectedRecipe.cost_per_unit?.toFixed(2)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">Loading…</div>
        )}
      </div>
    </div>
  );
}
