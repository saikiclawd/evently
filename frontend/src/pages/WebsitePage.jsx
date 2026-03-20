import { Globe, BookOpen, TrendingUp, FileText, RefreshCw, Shield, Palette, Zap } from "lucide-react";
import { useWishlists } from "@/hooks/useApi";

const statusColors = {
  new: "bg-yellow-500/10 text-yellow-400",
  reviewed: "bg-accent/10 text-accent",
  converted: "bg-green-500/10 text-green-400",
  rejected: "bg-red-500/10 text-red-400",
};

const settings = [
  { label: "Inventory Sync", desc: "Real-time availability on your website", enabled: true, icon: RefreshCw },
  { label: "Wishlist Widget", desc: "Let clients build wishlists & submit", enabled: true, icon: BookOpen },
  { label: "Event Insurance", desc: "Offer coverage during checkout", enabled: true, icon: Shield },
  { label: "Custom Branding", desc: "Match your website's look and feel", enabled: true, icon: Palette },
  { label: "Auto-Approval", desc: "Approve wishlist submissions automatically", enabled: false, icon: Zap },
];

export default function WebsitePage() {
  const { data: wishlists = [], isLoading } = useWishlists({});

  return (
    <div className="p-7 space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Recent Wishlists */}
        <div className="bg-dark-card rounded-xl border border-dark-border overflow-hidden">
          <div className="px-5 py-4 border-b border-dark-border">
            <h3 className="text-sm font-bold text-gray-100">Recent Wishlist Submissions</h3>
          </div>
          {isLoading ? (
            <div className="py-12 text-center text-gray-500 text-sm">Loading...</div>
          ) : wishlists.length === 0 ? (
            <div className="py-12 text-center text-gray-500">
              <BookOpen size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">No wishlists submitted yet</p>
              <p className="text-xs text-gray-600 mt-1">Wishlists will appear here when clients submit from your website</p>
            </div>
          ) : (
            wishlists.map((w) => (
              <div key={w.id} className="flex items-center gap-3.5 px-5 py-3.5 border-b border-dark-border last:border-0">
                <div className="w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                  <BookOpen size={16} className="text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-gray-100">{w.visitor_name}</div>
                  <div className="text-xs text-gray-500">
                    {w.items?.length || 0} items · {w.submitted_at ? new Date(w.submitted_at).toLocaleDateString() : ""}
                  </div>
                </div>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${statusColors[w.status] || statusColors.new}`}>
                  {w.status}
                </span>
              </div>
            ))
          )}
        </div>

        {/* Integration Settings */}
        <div className="bg-dark-card rounded-xl border border-dark-border p-5">
          <h3 className="text-sm font-bold text-gray-100 mb-5">Website Integration</h3>
          <div className="space-y-3">
            {settings.map((s, i) => (
              <div key={i} className="flex items-center gap-3.5 p-3.5 bg-dark-surface rounded-xl border border-dark-border">
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  s.enabled ? "bg-green-500/10" : "bg-dark-card"
                }`}>
                  <s.icon size={16} className={s.enabled ? "text-green-400" : "text-gray-500"} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold text-gray-100">{s.label}</div>
                  <div className="text-xs text-gray-500">{s.desc}</div>
                </div>
                <div className={`w-10 h-[22px] rounded-full p-0.5 cursor-pointer transition-colors ${s.enabled ? "bg-green-500" : "bg-dark-border"}`}>
                  <div className={`w-[18px] h-[18px] rounded-full bg-white transition-transform ${s.enabled ? "translate-x-[18px]" : "translate-x-0"}`} />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-dark-surface rounded-xl border border-dark-border">
            <div className="text-[10px] text-gray-500 font-semibold uppercase tracking-wide mb-2">Embed Code</div>
            <code className="text-[11px] text-teal-400 font-mono block break-all leading-relaxed">
              {'<script src="https://eventflow.yourdomain.com/widget.js" data-company="YOUR_ID"></script>'}
            </code>
            <p className="text-[11px] text-gray-500 mt-2">Add this to your website to enable the wishlist widget</p>
          </div>
        </div>
      </div>
    </div>
  );
}
