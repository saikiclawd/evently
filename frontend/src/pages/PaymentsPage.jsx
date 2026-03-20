import { DollarSign, AlertCircle, XCircle, CreditCard, Download, RefreshCw, Send } from "lucide-react";
import { usePayments } from "@/hooks/useApi";

export default function PaymentsPage() {
  const { data: payments = [], isLoading } = usePayments({});

  return (
    <div className="p-7 space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-sm font-bold text-gray-900">Payment Tracker</h3>
          <div className="flex gap-2">
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-xs text-gray-700 hover:bg-gray-50">
              <Download size={13} />Export
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-xs text-gray-700 hover:bg-gray-50">
              <RefreshCw size={13} />Sync QB
            </button>
          </div>
        </div>
        {isLoading ? (
          <div className="py-12 text-center text-gray-400 text-sm">Loading payments...</div>
        ) : payments.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">No payments recorded yet</div>
        ) : (
          payments.map((p) => (
            <div key={p.id} className="px-5 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <div>
                  <span className="text-sm font-semibold text-gray-900">${parseFloat(p.amount).toLocaleString()}</span>
                  <span className="text-xs text-gray-400 ml-2">{p.method?.replace("_", " ")}</span>
                </div>
                <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-md ${
                  p.status === "succeeded" ? "bg-green-50 text-green-600"
                  : p.status === "pending" ? "bg-amber-50 text-amber-600"
                  : "bg-red-50 text-red-600"
                }`}>{p.status}</span>
              </div>
              {p.paid_at && <div className="text-xs text-gray-400 mt-1">{new Date(p.paid_at).toLocaleString()}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
