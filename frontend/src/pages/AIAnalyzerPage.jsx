import { useState, useRef, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { flora } from "@/lib/api";
import toast from "react-hot-toast";
import { Upload, Sparkles, X, Flower2, Leaf, CheckCircle, AlertCircle, HelpCircle, BookOpen } from "lucide-react";

const CONFIDENCE_CONFIG = {
  high:   { label: "High",   color: "bg-emerald-50 text-emerald-700", icon: CheckCircle },
  medium: { label: "Medium", color: "bg-amber-50 text-amber-700",     icon: AlertCircle },
  low:    { label: "Low",    color: "bg-gray-100 text-gray-500",       icon: HelpCircle },
};

const FOLIAGE_NAMES = ["eucalyptus", "ruscus", "fern", "ivy", "bay", "olive", "greenery", "foliage",
  "leaf", "leaves", "grass", "seeded", "silver dollar", "baby", "wax flower", "gypsophila"];

function isFolliage(name = "") {
  return FOLIAGE_NAMES.some(f => name.toLowerCase().includes(f));
}

function ConfidenceBadge({ level }) {
  const cfg = CONFIDENCE_CONFIG[level] || CONFIDENCE_CONFIG.medium;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${cfg.color}`}>
      <Icon size={9} /> {cfg.label}
    </span>
  );
}

function FlowerCard({ flower }) {
  const foliage = isFolliage(flower.common_name) || isFolliage(flower.variety || "");
  return (
    <div className="flex items-start gap-3 py-3 border-b border-gray-50 last:border-0">
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
        foliage ? "bg-emerald-50" : "bg-flora-gold-lt"
      }`}>
        {foliage ? <Leaf size={14} className="text-emerald-600" /> : <Flower2 size={14} className="text-flora-gold" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-sm text-gray-800">{flower.common_name}</span>
          {flower.variety && <span className="text-xs text-gray-400">· {flower.variety}</span>}
          {flower.color && (
            <span className="text-[10px] text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">{flower.color}</span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-sm font-bold text-flora-gold">{flower.estimated_stems}</span>
          <span className="text-xs text-gray-400">stems</span>
          <ConfidenceBadge level={flower.confidence} />
        </div>
      </div>
    </div>
  );
}

function SaveRecipeModal({ result, onClose, onSaved }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState(result.arrangement_type || "centerpiece");
  const qc = useQueryClient();

  const saveMut = useMutation({
    mutationFn: () => flora.createRecipe({
      name,
      category,
      status: "draft",
      tags: ["ai-generated"],
      stems: result.flowers.map(f => ({
        flower_name: `${f.common_name}${f.variety ? ` (${f.variety})` : ""}`,
        quantity: f.estimated_stems,
      })),
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["flora-recipes"] });
      toast.success("Recipe draft saved — open Recipe Studio to finish it");
      onSaved();
    },
    onError: () => toast.error("Failed to save recipe"),
  });

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-[480px] p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-playfair text-lg text-gray-900">Save as Recipe Draft</h3>
          <button onClick={onClose} className="text-gray-300 hover:text-gray-600"><X size={18} /></button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Recipe Name
            </label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Garden Romance Centerpiece"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-flora-gold"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Category
            </label>
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-flora-gold"
            >
              {["bouquet","centerpiece","arch","boutonniere","ceremony","installation","other"].map(c => (
                <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
              ))}
            </select>
          </div>

          <div className="bg-flora-cream rounded-lg p-3 text-xs text-gray-500">
            <strong className="text-gray-700">
              {result.flowers.length} flower types · {result.total_stems_estimate} total stems
            </strong>
            <br />
            Saved as a draft. Open Recipe Studio to set pricing, labor time, and link flowers to your catalog.
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2 text-sm text-gray-500 hover:border-gray-300">
            Cancel
          </button>
          <button
            onClick={() => saveMut.mutate()}
            disabled={!name.trim() || saveMut.isPending}
            className="flex-1 bg-flora-gold text-white rounded-lg py-2 text-sm font-semibold hover:bg-amber-600 transition-colors disabled:opacity-40"
          >
            {saveMut.isPending ? "Saving…" : "Save Draft"}
          </button>
        </div>
      </div>
      <style>{`.font-playfair { font-family: 'Playfair Display', serif; }`}</style>
    </div>
  );
}

export default function AIAnalyzerPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [showSave, setShowSave] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const analyzeMut = useMutation({
    mutationFn: (f) => {
      const fd = new FormData();
      fd.append("image", f);
      return flora.analyzeImage(fd).then(r => r.data);
    },
    onSuccess: (data) => {
      setResult(data);
      toast.success("Analysis complete");
    },
    onError: (err) => {
      toast.error(err?.response?.data?.error || "Analysis failed — check your GROQ_API_KEY");
    },
  });

  const handleFile = useCallback((f) => {
    if (!f || !f.type.startsWith("image/")) {
      toast.error("Please upload an image file (JPG, PNG, WEBP)");
      return;
    }
    setFile(f);
    setResult(null);
    setPreview(URL.createObjectURL(f));
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const clearImage = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const totalStems = result?.flowers?.reduce((s, f) => s + (f.estimated_stems || 0), 0) || 0;

  return (
    <div className="p-7 space-y-6 bg-flora-cream min-h-full">
      {/* Header */}
      <div>
        <h1 className="font-playfair text-2xl text-gray-900 flex items-center gap-2">
          <Sparkles size={22} className="text-flora-gold" /> AI Stem Analyzer
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Upload a floral photo — Groq AI identifies flowers and estimates stem counts
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6 items-start">

        {/* LEFT — Upload */}
        <div className="space-y-4">
          {/* Drop Zone */}
          <div
            onClick={() => !preview && inputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={`relative rounded-2xl border-2 border-dashed transition-colors overflow-hidden
              ${preview ? "border-transparent cursor-default" : "cursor-pointer"}
              ${dragging ? "border-flora-gold bg-flora-gold-lt" : preview ? "border-gray-100" : "border-gray-200 hover:border-flora-gold bg-white"}`}
          >
            {preview ? (
              <>
                <img src={preview} alt="Upload preview" className="w-full object-cover max-h-80 rounded-2xl" />
                <button
                  onClick={clearImage}
                  className="absolute top-3 right-3 bg-white/90 rounded-full p-1.5 shadow text-gray-500 hover:text-red-500 transition-colors"
                >
                  <X size={14} />
                </button>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-14 px-6 text-center">
                <div className="w-14 h-14 rounded-2xl bg-flora-gold-lt flex items-center justify-center mb-4">
                  <Upload size={22} className="text-flora-gold" />
                </div>
                <p className="text-sm font-semibold text-gray-700">Drag & drop a photo here</p>
                <p className="text-xs text-gray-400 mt-1">or click to browse</p>
                <p className="text-xs text-gray-300 mt-3">JPG · PNG · WEBP · max 10 MB</p>
                <p className="text-xs text-gray-400 mt-3">
                  Works with bouquets, centerpieces, arches, Pinterest screenshots
                </p>
              </div>
            )}
          </div>

          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={e => e.target.files[0] && handleFile(e.target.files[0])}
          />

          {file && (
            <button
              onClick={() => analyzeMut.mutate(file)}
              disabled={analyzeMut.isPending}
              className="w-full flex items-center justify-center gap-2 bg-flora-gold text-white font-semibold py-3 rounded-xl hover:bg-amber-600 transition-colors disabled:opacity-50"
            >
              <Sparkles size={16} />
              {analyzeMut.isPending ? "Analyzing…" : "Analyze Stems"}
            </button>
          )}

          {analyzeMut.isPending && (
            <div className="bg-white rounded-xl border border-gray-100 p-4 text-center">
              <div className="text-sm text-gray-500">Groq AI is identifying your flowers…</div>
              <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-flora-gold rounded-full animate-pulse w-2/3" />
              </div>
            </div>
          )}
        </div>

        {/* RIGHT — Results */}
        <div>
          {!result && !analyzeMut.isPending && (
            <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center h-full flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center mb-3">
                <Sparkles size={20} className="text-gray-300" />
              </div>
              <p className="text-sm font-medium text-gray-400">Results will appear here</p>
              <p className="text-xs text-gray-300 mt-1">Upload a photo and click Analyze</p>
            </div>
          )}

          {result && (
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
              {/* Result header */}
              <div className="bg-gray-900 px-5 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold uppercase tracking-widest text-flora-gold mb-1">
                      {result.arrangement_type}
                    </div>
                    <div className="font-playfair text-white text-lg">
                      {totalStems} stems identified
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-white/40 uppercase tracking-wide">Varieties</div>
                    <div className="font-playfair text-2xl text-white">{result.flowers?.length || 0}</div>
                  </div>
                </div>
                {result.notes && (
                  <p className="text-white/50 text-xs mt-2 italic">{result.notes}</p>
                )}
              </div>

              {/* Flower list */}
              <div className="px-5 py-2 divide-y divide-gray-50">
                {(result.flowers || []).map((f, i) => (
                  <FlowerCard key={i} flower={f} />
                ))}
              </div>

              {/* Footer */}
              <div className="px-5 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
                <div className="text-xs text-gray-400">
                  Powered by Groq · Llama 4 Scout
                </div>
                <button
                  onClick={() => setShowSave(true)}
                  className="flex items-center gap-1.5 bg-flora-gold text-white text-xs font-bold px-4 py-2 rounded-lg hover:bg-amber-600 transition-colors"
                >
                  <BookOpen size={12} /> Save as Recipe
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tips */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { emoji: "📸", title: "Best photos", body: "Clear, well-lit images. Single arrangement fills the frame." },
          { emoji: "🌹", title: "What it identifies", body: "Flower type, variety, color, and estimated individual stem count." },
          { emoji: "📋", title: "Save to recipes", body: "Results can be saved as a draft recipe and refined in Recipe Studio." },
        ].map(({ emoji, title, body }) => (
          <div key={title} className="bg-white rounded-xl border border-gray-100 p-4">
            <div className="text-xl mb-2">{emoji}</div>
            <div className="text-sm font-semibold text-gray-700 mb-1">{title}</div>
            <div className="text-xs text-gray-400 leading-relaxed">{body}</div>
          </div>
        ))}
      </div>

      {showSave && result && (
        <SaveRecipeModal
          result={result}
          onClose={() => setShowSave(false)}
          onSaved={() => setShowSave(false)}
        />
      )}

      <style>{`.font-playfair { font-family: 'Playfair Display', serif; }`}</style>
    </div>
  );
}
