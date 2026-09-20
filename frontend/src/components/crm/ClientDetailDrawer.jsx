// ── CRM Client Detail Drawer — Overview / Contacts / Notes / Tasks / Timeline ──
import { useState } from "react";
import { X, User, StickyNote, ListTodo, Clock, Plus, Star, Check } from "lucide-react";
import toast from "react-hot-toast";
import {
  useClient, useClientContacts, useAddContact,
  useClientNotes, useAddNote,
  useClientTasks, useAddTask, useUpdateTask,
  useClientTimeline,
} from "@/hooks/useApi";

const TABS = [
  { key: "overview", label: "Overview", icon: User },
  { key: "contacts", label: "Contacts", icon: User },
  { key: "notes",    label: "Notes",    icon: StickyNote },
  { key: "tasks",    label: "Tasks",    icon: ListTodo },
  { key: "timeline", label: "Timeline", icon: Clock },
];

function OverviewTab({ client }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-[10px] text-gray-500 uppercase tracking-wide">Events</div>
          <div className="text-lg font-bold text-gray-900">{client.event_count || 0}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-[10px] text-gray-500 uppercase tracking-wide">Total Spent</div>
          <div className="text-lg font-bold text-green-600 font-mono">${(client.total_spent || 0).toLocaleString()}</div>
        </div>
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between border-b border-gray-100 py-2">
          <span className="text-gray-400">Email</span><span className="text-gray-800">{client.email || "—"}</span>
        </div>
        <div className="flex justify-between border-b border-gray-100 py-2">
          <span className="text-gray-400">Phone</span><span className="text-gray-800">{client.phone || "—"}</span>
        </div>
        <div className="flex justify-between border-b border-gray-100 py-2">
          <span className="text-gray-400">Lead Source</span><span className="text-gray-800">{client.lead_source || "—"}</span>
        </div>
        <div className="flex justify-between border-b border-gray-100 py-2">
          <span className="text-gray-400">Owner</span><span className="text-gray-800">{client.owner?.name || "Unassigned"}</span>
        </div>
        <div className="flex justify-between py-2">
          <span className="text-gray-400">Address</span><span className="text-gray-800 text-right max-w-[220px]">{client.address || "—"}</span>
        </div>
      </div>
    </div>
  );
}

function ContactsTab({ clientId }) {
  const { data: contacts, isLoading } = useClientContacts(clientId);
  const addContact = useAddContact(clientId);
  const [form, setForm] = useState({ name: "", role: "", email: "", phone: "" });
  const [showForm, setShowForm] = useState(false);

  function submit() {
    if (!form.name.trim()) return;
    addContact.mutate(form, {
      onSuccess: () => { setForm({ name: "", role: "", email: "", phone: "" }); setShowForm(false); toast.success("Contact added"); },
      onError: () => toast.error("Failed to add contact"),
    });
  }

  return (
    <div className="space-y-3">
      {isLoading ? (
        <div className="text-center py-8 text-gray-400 text-sm">Loading…</div>
      ) : (
        (contacts || []).map((c) => (
          <div key={c.id} className="flex items-center gap-3 bg-gray-50 rounded-lg p-3">
            <div className="w-9 h-9 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
              {c.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-semibold text-gray-900 truncate">{c.name}</span>
                {c.is_primary && <Star size={11} className="text-amber-400 fill-amber-400 flex-shrink-0" />}
              </div>
              <div className="text-xs text-gray-400 truncate">{c.role}{c.role && c.email ? " · " : ""}{c.email}</div>
            </div>
          </div>
        ))
      )}

      {showForm ? (
        <div className="border border-gray-200 rounded-lg p-3 space-y-2">
          <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-accent" />
          <input placeholder="Role (Bride, Planner...)" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-accent" />
          <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-accent" />
          <input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-accent" />
          <div className="flex gap-2">
            <button onClick={() => setShowForm(false)} className="flex-1 border border-gray-200 rounded-lg py-1.5 text-xs text-gray-500">Cancel</button>
            <button onClick={submit} disabled={addContact.isPending} className="flex-1 bg-blue-600 text-white rounded-lg py-1.5 text-xs font-semibold hover:bg-blue-700 disabled:opacity-40">
              {addContact.isPending ? "Saving…" : "Add Contact"}
            </button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowForm(true)} className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg border border-dashed border-gray-300 text-xs font-semibold text-gray-500 hover:border-accent hover:text-accent">
          <Plus size={13} />Add Contact
        </button>
      )}
    </div>
  );
}

function NotesTab({ clientId }) {
  const { data: notes, isLoading } = useClientNotes(clientId);
  const addNote = useAddNote(clientId);
  const [body, setBody] = useState("");

  function submit() {
    if (!body.trim()) return;
    addNote.mutate({ body }, {
      onSuccess: () => { setBody(""); toast.success("Note added"); },
      onError: () => toast.error("Failed to add note"),
    });
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Log a call, meeting, or update…"
          rows={2}
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:border-accent"
        />
        <button onClick={submit} disabled={addNote.isPending || !body.trim()}
          className="px-3 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 disabled:opacity-40">
          Add
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-gray-400 text-sm">Loading…</div>
      ) : (
        (notes || []).map((n) => (
          <div key={n.id} className={`rounded-lg p-3 ${n.is_pinned ? "bg-amber-50 border border-amber-100" : "bg-gray-50"}`}>
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{n.body}</p>
            <div className="text-[10px] text-gray-400 mt-1.5">
              {n.author?.name || "System"} · {new Date(n.created_at).toLocaleString()}
            </div>
          </div>
        ))
      )}
      {!isLoading && (notes || []).length === 0 && (
        <div className="text-center py-8 text-gray-300 text-xs">No notes yet</div>
      )}
    </div>
  );
}

function TasksTab({ clientId }) {
  const { data: taskList, isLoading } = useClientTasks(clientId);
  const addTask = useAddTask(clientId);
  const updateTask = useUpdateTask();
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");

  function submit() {
    if (!title.trim()) return;
    addTask.mutate({ title, due_date: dueDate || undefined }, {
      onSuccess: () => { setTitle(""); setDueDate(""); toast.success("Task added"); },
      onError: () => toast.error("Failed to add task"),
    });
  }

  function toggleDone(task) {
    updateTask.mutate({ id: task.id, data: { status: task.status === "done" ? "todo" : "done" } });
  }

  const priorityColor = { high: "text-red-500", medium: "text-amber-500", low: "text-gray-400" };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="New task…"
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent" />
        <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)}
          className="border border-gray-200 rounded-lg px-2 py-2 text-xs text-gray-600 focus:outline-none focus:border-accent" />
        <button onClick={submit} disabled={addTask.isPending || !title.trim()}
          className="px-3 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 disabled:opacity-40">
          Add
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-gray-400 text-sm">Loading…</div>
      ) : (
        (taskList || []).map((t) => (
          <div key={t.id} className="flex items-center gap-3 bg-gray-50 rounded-lg p-3">
            <button
              onClick={() => toggleDone(t)}
              className={`w-5 h-5 rounded-full border flex items-center justify-center flex-shrink-0 ${
                t.status === "done" ? "bg-green-500 border-green-500" : "border-gray-300 hover:border-accent"
              }`}
            >
              {t.status === "done" && <Check size={12} className="text-white" />}
            </button>
            <div className="flex-1 min-w-0">
              <div className={`text-sm ${t.status === "done" ? "line-through text-gray-400" : "text-gray-800"}`}>{t.title}</div>
              {t.due_date && (
                <div className="text-[10px] text-gray-400">Due {new Date(t.due_date).toLocaleDateString()}</div>
              )}
            </div>
            <span className={`text-[10px] font-semibold uppercase ${priorityColor[t.priority] || "text-gray-400"}`}>{t.priority}</span>
          </div>
        ))
      )}
      {!isLoading && (taskList || []).length === 0 && (
        <div className="text-center py-8 text-gray-300 text-xs">No tasks yet</div>
      )}
    </div>
  );
}

function TimelineTab({ clientId }) {
  const { data, isLoading } = useClientTimeline(clientId);
  const events = data?.events || [];

  if (isLoading) return <div className="text-center py-8 text-gray-400 text-sm">Loading…</div>;
  if (events.length === 0) return <div className="text-center py-8 text-gray-300 text-xs">No activity yet</div>;

  return (
    <div className="space-y-3">
      {events.map((e) => (
        <div key={`${e.type}-${e.id}`} className="flex gap-3">
          <div className="w-2 h-2 rounded-full bg-accent mt-1.5 flex-shrink-0" />
          <div className="flex-1 min-w-0 pb-3 border-b border-gray-100">
            {e.type === "note" ? (
              <p className="text-sm text-gray-800">{e.body}</p>
            ) : (
              <p className="text-sm text-gray-600 capitalize">{e.action?.replace(/_/g, " ")}</p>
            )}
            <div className="text-[10px] text-gray-400 mt-1">{new Date(e.created_at).toLocaleString()}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ClientDetailDrawer({ clientId, onClose }) {
  const [tab, setTab] = useState("overview");
  const { data: client, isLoading } = useClient(clientId);

  if (!clientId) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative w-full max-w-md bg-white h-full shadow-xl flex flex-col">
        {isLoading || !client ? (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">Loading…</div>
        ) : (
          <>
            <div className="px-5 pt-5 pb-3 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">{client.name}</h2>
                  <span className="inline-block mt-1 text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-md bg-blue-50 text-blue-600">
                    {client.lifecycle_stage?.replace("_", " ")}
                  </span>
                </div>
                <button onClick={onClose} className="text-gray-300 hover:text-gray-600"><X size={18} /></button>
              </div>
            </div>

            <div className="flex border-b border-gray-200 px-2">
              {TABS.map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setTab(key)}
                  className={`px-3 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                    tab === key ? "border-accent text-accent" : "border-transparent text-gray-400 hover:text-gray-700"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {tab === "overview" && <OverviewTab client={client} />}
              {tab === "contacts" && <ContactsTab clientId={clientId} />}
              {tab === "notes" && <NotesTab clientId={clientId} />}
              {tab === "tasks" && <TasksTab clientId={clientId} />}
              {tab === "timeline" && <TimelineTab clientId={clientId} />}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
