// ── CRM Pipeline Kanban — Twenty-CRM-inspired lifecycle board ──
import { DndContext, useDraggable, useDroppable, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { Mail, ListTodo, GripVertical } from "lucide-react";
import { useClientPipeline, useMoveClientStage } from "@/hooks/useApi";

const STAGE_META = {
  lead:         { label: "Lead",         color: "bg-gray-100 text-gray-600" },
  qualified:    { label: "Qualified",    color: "bg-blue-50 text-blue-600" },
  active:       { label: "Active",       color: "bg-amber-50 text-amber-600" },
  past_client:  { label: "Past Client",  color: "bg-green-50 text-green-600" },
  lost:         { label: "Lost",         color: "bg-red-50 text-red-500" },
};

function ClientCard({ client, stage, onOpen }) {
  // Drag listeners live only on the grip handle below — keeping them off the
  // card body means a plain click still opens the detail drawer (dnd-kit's
  // pointer listeners on the same element as onClick can swallow the click).
  //
  // The source stage travels with the drag via `data` rather than being
  // looked up from the board cache on drop — scanning the cache is racy if
  // a card is dragged again before the previous move's refetch lands.
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: client.id,
    data: { stage },
  });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, zIndex: 50 }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      onClick={() => onOpen(client.id)}
      className={`group bg-white rounded-lg border border-gray-200 p-3 mb-2 cursor-pointer hover:border-accent/40 transition-colors ${
        isDragging ? "opacity-50 shadow-lg" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="text-sm font-bold text-gray-900 truncate">{client.name}</div>
        <button
          {...listeners}
          {...attributes}
          onClick={(e) => e.stopPropagation()}
          className="text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
          title="Drag to move stage"
        >
          <GripVertical size={14} />
        </button>
      </div>
      {client.email && (
        <div className="flex items-center gap-1 text-xs text-gray-400 truncate mb-2">
          <Mail size={11} />{client.email}
        </div>
      )}
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {client.tags?.slice(0, 2).map((t) => (
            <span key={t} className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">{t}</span>
          ))}
        </div>
        {client.open_task_count > 0 && (
          <div className="flex items-center gap-1 text-[10px] text-amber-600 font-semibold">
            <ListTodo size={11} />{client.open_task_count}
          </div>
        )}
      </div>
    </div>
  );
}

function StageColumn({ stage, clients, onOpen }) {
  const { setNodeRef, isOver } = useDroppable({ id: stage });
  const meta = STAGE_META[stage];

  return (
    <div
      ref={setNodeRef}
      className={`flex-1 min-w-[240px] rounded-xl p-2.5 transition-colors ${
        isOver ? "bg-accent/5 ring-2 ring-accent/30" : "bg-gray-50"
      }`}
    >
      <div className="flex items-center justify-between px-1 mb-2.5">
        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${meta.color}`}>{meta.label}</span>
        <span className="text-xs text-gray-400 font-semibold">{clients.length}</span>
      </div>
      <div className="min-h-[60px]">
        {clients.map((c) => (
          <ClientCard key={c.id} client={c} stage={stage} onOpen={onOpen} />
        ))}
        {clients.length === 0 && (
          <div className="text-center py-6 text-[11px] text-gray-300">No clients</div>
        )}
      </div>
    </div>
  );
}

export default function ClientPipelineBoard({ onOpen }) {
  const { data, isLoading } = useClientPipeline();
  const moveStage = useMoveClientStage();
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  if (isLoading) {
    return <div className="text-center py-20 text-gray-400 text-sm">Loading pipeline…</div>;
  }

  const stages = data?.stages || Object.keys(STAGE_META);
  const board = data?.board || {};

  function handleDragEnd(event) {
    const { active, over } = event;
    if (!over) return;
    const clientId = active.id;
    const newStage = over.id;
    const sourceStage = active.data.current?.stage;
    if (sourceStage === newStage) return;
    moveStage.mutate({ id: clientId, stage: newStage });
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {stages.map((stage) => (
          <StageColumn key={stage} stage={stage} clients={board[stage] || []} onOpen={onOpen} />
        ))}
      </div>
    </DndContext>
  );
}
