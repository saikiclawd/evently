import { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight, RefreshCw, Calendar, MapPin } from "lucide-react";
import { useProjects } from "@/hooks/useApi";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];

export default function CalendarPage() {
  const [year, setYear] = useState(2026);
  const [month, setMonth] = useState(3); // April (0-indexed)
  const [selectedDay, setSelectedDay] = useState(null);

  const { data } = useProjects({ per_page: 100 });
  const projects = data?.projects || [];

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const eventsByDay = useMemo(() => {
    const map = {};
    projects.forEach((p) => {
      if (!p.event_start) return;
      const d = new Date(p.event_start);
      if (d.getFullYear() === year && d.getMonth() === month) {
        const day = d.getDate();
        if (!map[day]) map[day] = [];
        map[day].push(p);
      }
    });
    return map;
  }, [projects, year, month]);

  const prev = () => { if (month === 0) { setMonth(11); setYear(year - 1); } else setMonth(month - 1); setSelectedDay(null); };
  const next = () => { if (month === 11) { setMonth(0); setYear(year + 1); } else setMonth(month + 1); setSelectedDay(null); };

  const selectedEvents = selectedDay ? (eventsByDay[selectedDay] || []) : [];

  return (
    <div className="p-7">
      <div className="flex items-center gap-4 mb-5">
        <button onClick={prev} className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-dark-card border border-dark-border">
          <ChevronLeft size={16} />
        </button>
        <h2 className="text-lg font-bold text-gray-100">{MONTHS[month]} {year}</h2>
        <button onClick={next} className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-dark-card border border-dark-border">
          <ChevronRight size={16} />
        </button>
        <button className="ml-auto flex items-center gap-1.5 px-3 py-2 rounded-lg border border-dark-border text-xs font-semibold text-gray-300 hover:bg-dark-surface">
          <RefreshCw size={14} />Sync Google Calendar
        </button>
      </div>

      <div className="grid grid-cols-[1fr_320px] gap-5">
        {/* Calendar Grid */}
        <div className="bg-dark-card rounded-xl border border-dark-border p-5">
          <div className="grid grid-cols-7 gap-1 mb-2">
            {DAYS.map((d) => (
              <div key={d} className="text-center text-[11px] font-semibold text-gray-500 py-2">{d}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: firstDay }).map((_, i) => <div key={`e-${i}`} />)}
            {Array.from({ length: daysInMonth }, (_, i) => {
              const day = i + 1;
              const hasEvents = eventsByDay[day];
              const isSelected = selectedDay === day;
              const isToday = new Date().getDate() === day && new Date().getMonth() === month && new Date().getFullYear() === year;
              return (
                <button key={day} onClick={() => setSelectedDay(day)}
                  className={`aspect-square rounded-xl flex flex-col items-center justify-center gap-1 text-sm transition-all ${
                    isSelected ? "border-2 border-accent bg-accent/5 text-accent font-bold"
                    : hasEvents ? "bg-dark-surface hover:bg-dark-border text-gray-100 font-semibold"
                    : "text-gray-500 hover:bg-dark-surface"
                  } ${isToday ? "ring-1 ring-accent/30" : ""}`}>
                  {day}
                  {hasEvents && (
                    <div className="flex gap-0.5">
                      {hasEvents.slice(0, 3).map((_, j) => (
                        <div key={j} className="w-1 h-1 rounded-full bg-accent" />
                      ))}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Day Detail */}
        <div className="bg-dark-card rounded-xl border border-dark-border p-5">
          <h3 className="text-sm font-bold text-gray-100 mb-4">
            {selectedDay ? `${MONTHS[month]} ${selectedDay}, ${year}` : "Select a day"}
          </h3>
          {!selectedDay ? (
            <div className="text-center py-12 text-gray-500">
              <Calendar size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-xs">Click a day to see events</p>
            </div>
          ) : selectedEvents.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Calendar size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-xs">No events scheduled</p>
            </div>
          ) : (
            <div className="space-y-3">
              {selectedEvents.map((p) => (
                <div key={p.id} className="p-3.5 rounded-lg bg-dark-surface border border-dark-border">
                  <div className="text-sm font-semibold text-gray-100">{p.event_name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{p.client?.name}</div>
                  {p.venue_name && (
                    <div className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                      <MapPin size={11} />{p.venue_name}
                    </div>
                  )}
                  <span className={`inline-block mt-2 text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                    p.stage === "confirmed" ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400"
                  }`}>{p.stage?.replace("_", " ")}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
