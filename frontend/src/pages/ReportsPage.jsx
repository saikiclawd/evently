import { DollarSign, TrendingUp, Package, Users } from "lucide-react";
import { useRevenueReport, usePipeline } from "@/hooks/useApi";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const pipelineColors = {
  draft: "#64748B", proposal_sent: "#F59E0B", signed: "#3B82F6",
  deposit_paid: "#58A6FF", confirmed: "#22C55E", paid_in_full: "#14B8A6",
  completed: "#06B6D4", cancelled: "#EF4444",
};

export default function ReportsPage() {
  const { data: revenueData } = useRevenueReport({ year: 2026 });
  const { data: pipeline } = usePipeline();

  const monthly = revenueData?.monthly || [];
  const maxRev = Math.max(...monthly.map((m) => m.revenue), 1);

  return (
    <div className="p-7 space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Revenue Chart */}
        <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-sm font-bold text-gray-100">Revenue Overview</h3>
              <p className="text-xs text-gray-500 mt-0.5">{revenueData?.year || 2026} monthly breakdown</p>
            </div>
          </div>
          <div className="flex items-end gap-1.5 h-44">
            {MONTHS.map((label, i) => {
              const entry = monthly.find((m) => m.month === i + 1);
              const rev = entry?.revenue || 0;
              const h = maxRev > 0 ? (rev / maxRev) * 160 : 0;
              const isCurrent = i === new Date().getMonth();
              return (
                <div key={label} className="flex-1 flex flex-col items-center gap-1 group">
                  <div className="text-[9px] text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity font-mono">
                    ${(rev / 1000).toFixed(1)}k
                  </div>
                  <div
                    className={`w-full rounded transition-all duration-300 ${isCurrent ? "bg-accent" : "bg-dark-border"}`}
                    style={{ height: Math.max(h, 4) }}
                  />
                  <span className="text-[9px] text-gray-500">{label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Sales Pipeline */}
        <div className="bg-dark-card rounded-xl p-6 border border-dark-border">
          <h3 className="text-sm font-bold text-gray-100 mb-5">Sales Pipeline</h3>
          <div className="space-y-3">
            {(pipeline || []).map((s) => (
              <div key={s.stage} className="flex items-center gap-3 py-2 border-b border-dark-border last:border-0">
                <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: pipelineColors[s.stage] || "#64748B" }} />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-200">{s.stage?.replace("_", " ")}</div>
                </div>
                <span className="text-xs text-gray-500">{s.count} projects</span>
                <span className="text-sm font-bold text-gray-100 font-mono min-w-[70px] text-right">
                  ${(s.value / 1000).toFixed(1)}k
                </span>
              </div>
            ))}
            {(!pipeline || pipeline.length === 0) && (
              <p className="text-sm text-gray-500 text-center py-8">No pipeline data yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
