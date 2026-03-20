import { useState } from "react";
import { Plus, Search, QrCode, Upload, X } from "lucide-react";
import { useInventory, useCategories, useCreateInventoryItem } from "@/hooks/useApi";
import toast from "react-hot-toast";

function CreateItemModal({ open, onClose }) {
  const [form, setForm] = useState({ name: "", category: "", price: "", total_quantity: "", description: "", tags: "" });
  const createItem = useCreateInventoryItem();
  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createItem.mutateAsync({
        ...form,
        price: parseFloat(form.price),
        total_quantity: parseInt(form.total_quantity),
        tags: form.tags ? form.tags.split(",").map((t) => t.trim()) : [],
      });
      toast.success("Item created!");
      onClose();
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to create item");
    }
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white border border-gray-200 rounded-xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-5">
          <h3 className="text-lg font-bold text-gray-900">Add Inventory Item</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input placeholder="Item name *" value={form.name} onChange={update("name")} required
            className="w-full px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent" />
          <div className="grid grid-cols-2 gap-3">
            <input placeholder="Category *" value={form.category} onChange={update("category")} required
              className="px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent" />
            <input placeholder="Price *" type="number" step="0.01" value={form.price} onChange={update("price")} required
              className="px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent" />
          </div>
          <input placeholder="Total quantity *" type="number" value={form.total_quantity} onChange={update("total_quantity")} required
            className="w-full px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent" />
          <textarea placeholder="Description" value={form.description} onChange={update("description")} rows={2}
            className="w-full px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent resize-none" />
          <input placeholder="Tags (comma-separated)" value={form.tags} onChange={update("tags")}
            className="w-full px-3 py-2.5 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent" />
          <button type="submit" disabled={createItem.isPending}
            className="w-full py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50">
            {createItem.isPending ? "Creating..." : "Create Item"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function InventoryPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading } = useInventory({ search, category, page, per_page: 24 });
  const { data: categories } = useCategories();

  const items = data?.items || [];
  const total = data?.total || 0;

  return (
    <div className="p-7">
      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-5 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search inventory..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 bg-gray-50 text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:border-accent"
          />
        </div>
        <div className="flex gap-1 bg-gray-50 border border-gray-200 rounded-lg p-0.5">
          <button onClick={() => { setCategory(""); setPage(1); }}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${!category ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-800"}`}>
            All
          </button>
          {(categories || []).map((c) => (
            <button key={c} onClick={() => { setCategory(c); setPage(1); }}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${category === c ? "bg-blue-600 text-white" : "text-gray-400 hover:text-gray-800"}`}>
              {c}
            </button>
          ))}
        </div>
        <div className="ml-auto flex gap-2">
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-white">
            <QrCode size={14} />Barcoding
          </button>
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700">
            <Plus size={14} />Add Item
          </button>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="text-center py-20 text-gray-400 text-sm">Loading inventory...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-20">
          <Package size={40} className="text-gray-400 mx-auto mb-3" />
          <p className="text-gray-400 text-sm">No items found</p>
          <button onClick={() => setShowCreate(true)} className="mt-3 text-blue-600 text-sm font-semibold hover:underline">
            Add your first item
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {items.map((item) => {
            const utilPct = item.total_quantity > 0 ? ((item.total_quantity - item.available_quantity) / item.total_quantity * 100).toFixed(0) : 0;
            const availPct = item.total_quantity > 0 ? (item.available_quantity / item.total_quantity * 100) : 100;
            return (
              <div key={item.id}
                className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:border-accent/40 hover:-translate-y-0.5 hover:shadow-md transition-all cursor-pointer group">
                {/* Image placeholder */}
                <div className="h-24 bg-gradient-to-br from-dark-surface to-dark-bg flex items-center justify-center relative">
                  <span className="text-4xl">{item.primary_photo_url ? "📷" : "📦"}</span>
                  {item.is_low_stock && (
                    <span className="absolute top-2 right-2 text-[10px] font-bold px-2 py-0.5 rounded bg-yellow-500/15 text-amber-600">LOW STOCK</span>
                  )}
                </div>
                <div className="p-4">
                  <div className="flex justify-between items-start mb-1">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-gray-900 truncate">{item.name}</div>
                      <div className="text-xs text-gray-400 mt-0.5">{item.category}</div>
                    </div>
                    <span className="text-base font-bold text-blue-600 font-mono">${item.price}</span>
                  </div>
                  {item.tags?.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {item.tags.slice(0, 3).map((t) => (
                        <span key={t} className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">{t}</span>
                      ))}
                    </div>
                  )}
                  <div className="mt-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-500">Availability</span>
                      <span className="font-semibold text-gray-700">{item.available_quantity}/{item.total_quantity}</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{
                        width: `${availPct}%`,
                        background: availPct < 20 ? "#dc2626" : availPct < 40 ? "#d97706" : "#16a34a",
                      }} />
                    </div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-2">
                    <span>{utilPct}% utilized</span>
                    <span>{item.total_bookings || 0} bookings</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {(data?.pages || 0) > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          {Array.from({ length: data.pages }, (_, i) => (
            <button key={i} onClick={() => setPage(i + 1)}
              className={`w-8 h-8 rounded-lg text-xs font-semibold ${page === i + 1 ? "bg-blue-600 text-white" : "bg-white text-gray-400 hover:text-gray-800 border border-gray-200"}`}>
              {i + 1}
            </button>
          ))}
        </div>
      )}

      <CreateItemModal open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}
