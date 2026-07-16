"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  closestCorners,
  useSensor,
  useSensors,
  useDroppable,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import { toast } from "sonner";
import { useSearchParams } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DemandCard } from "@/components/demand/demand-card";
import { DemandDrawer } from "@/components/demand/demand-drawer";
import { api, ApiError } from "@/lib/api";
import {
  BOARD_STATUSES,
  STATUS_LABELS,
  WIP_LIMITS,
  type BoardResponse,
  type DemandRequest,
  type DemandStatus,
} from "@/lib/types";
import { cn } from "@/lib/utils";

type Columns = Record<DemandStatus, DemandRequest[]>;

function emptyColumns(): Columns {
  return BOARD_STATUSES.reduce((acc, s) => {
    acc[s] = [];
    return acc;
  }, {} as Columns);
}

function Column({
  status,
  items,
  onOpen,
}: {
  status: DemandStatus;
  items: DemandRequest[];
  onOpen: (d: DemandRequest) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const wip = WIP_LIMITS[status];
  const overWip = wip != null && items.length > wip;

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "bg-muted/30 flex h-full w-72 shrink-0 flex-col rounded-xl border",
        status === "DESCARTADA" && "border-dashed border-rose-500/40 bg-rose-950/20",
        isOver && "ring-2 ring-primary/40",
      )}
    >
      <div className="flex items-center justify-between gap-2 border-b px-3 py-2">
        <div>
          <p className="text-sm font-semibold">{STATUS_LABELS[status]}</p>
          <p className="text-muted-foreground text-[11px]">
            {items.length}
            {wip != null ? ` / WIP ${wip}` : ""}
          </p>
        </div>
        <Badge variant={overWip ? "destructive" : "secondary"}>{items.length}</Badge>
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto p-2">
        <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          {items.map((item) => (
            <DemandCard key={item.id} demand={item} onOpen={onOpen} />
          ))}
        </SortableContext>
        {items.length === 0 ? (
          <p className="text-muted-foreground px-1 py-6 text-center text-xs">Sin tarjetas</p>
        ) : null}
      </div>
    </div>
  );
}

export function KanbanBoard() {
  const [columns, setColumns] = useState<Columns>(emptyColumns);
  const [snapshot, setSnapshot] = useState<Columns>(emptyColumns);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState<DemandRequest | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const searchParams = useSearchParams();

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor),
  );

  const load = useCallback(async () => {
    try {
      const board = await api.get<BoardResponse>("/api/demands/board");
      const next = emptyColumns();
      for (const col of board.columns) {
        const status = col.status as DemandStatus;
        if (next[status]) next[status] = col.items;
      }
      setColumns(next);
      setSnapshot(next);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error al cargar tablero");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const id = searchParams.get("id");
    if (id) {
      setSelectedId(Number(id));
      setDrawerOpen(true);
    }
  }, [searchParams]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return columns;
    const next = emptyColumns();
    for (const status of BOARD_STATUSES) {
      next[status] = columns[status].filter((d) => {
        const hay = `${d.product_name_free ?? ""} ${d.variant ?? ""} ${d.notes ?? ""} ${d.id}`;
        return hay.toLowerCase().includes(q);
      });
    }
    return next;
  }, [columns, query]);

  function findContainer(id: string | number): DemandStatus | null {
    if (BOARD_STATUSES.includes(id as DemandStatus)) return id as DemandStatus;
    for (const status of BOARD_STATUSES) {
      if (columns[status].some((d) => d.id === id)) return status;
    }
    return null;
  }

  function findDemand(id: number): DemandRequest | undefined {
    for (const status of BOARD_STATUSES) {
      const found = columns[status].find((d) => d.id === id);
      if (found) return found;
    }
    return undefined;
  }

  function onDragStart(event: DragStartEvent) {
    const card = findDemand(Number(event.active.id));
    setActive(card ?? null);
    setSnapshot(columns);
  }

  function onDragOver(event: DragOverEvent) {
    const { active: a, over } = event;
    if (!over) return;
    const activeId = Number(a.id);
    const from = findContainer(activeId);
    const to = findContainer(over.id);
    if (!from || !to || from === to) return;

    setColumns((prev) => {
      const fromItems = [...prev[from]];
      const toItems = [...prev[to]];
      const idx = fromItems.findIndex((d) => d.id === activeId);
      if (idx < 0) return prev;
      const [moved] = fromItems.splice(idx, 1);
      const overIndex = toItems.findIndex((d) => d.id === over.id);
      const insertAt = overIndex >= 0 ? overIndex : toItems.length;
      toItems.splice(insertAt, 0, { ...moved, status: to });
      return { ...prev, [from]: fromItems, [to]: toItems };
    });
  }

  async function onDragEnd(event: DragEndEvent) {
    const { active: a, over } = event;
    setActive(null);
    if (!over) {
      setColumns(snapshot);
      return;
    }

    const activeId = Number(a.id);
    const original = snapshot;
    let fromStatus: DemandStatus | null = null;
    for (const status of BOARD_STATUSES) {
      if (original[status].some((d) => d.id === activeId)) {
        fromStatus = status;
        break;
      }
    }
    const toStatus = findContainer(over.id);
    if (!fromStatus || !toStatus) {
      setColumns(snapshot);
      return;
    }

    if (fromStatus === toStatus) {
      setColumns((prev) => {
        const items = [...prev[toStatus]];
        const oldIndex = items.findIndex((d) => d.id === activeId);
        const newIndex = items.findIndex((d) => d.id === Number(over.id));
        if (oldIndex < 0 || newIndex < 0) return prev;
        return { ...prev, [toStatus]: arrayMove(items, oldIndex, newIndex) };
      });
    }

    const card = original[fromStatus].find((d) => d.id === activeId);
    if (!card) return;

    try {
      if (fromStatus !== toStatus) {
        await api.patch(`/api/demands/${activeId}/status`, {
          status: toStatus,
          version: card.version,
        });
        toast.success(`Movida a ${STATUS_LABELS[toStatus]}`);
      }

      // Persistir orden de la columna destino con el estado local optimista
      setColumns((prev) => {
        const reorderItems = prev[toStatus].map((d, index) => ({
          id: d.id,
          sort_order: index,
          status: toStatus,
        }));
        void api.patch("/api/demands/reorder", { items: reorderItems }).then(() => load());
        return prev;
      });
    } catch (e) {
      setColumns(snapshot);
      toast.error(e instanceof ApiError ? e.message : "Transición no permitida");
      await load();
    }
  }

  if (loading) {
    return (
      <div className="flex gap-3 overflow-x-auto p-1">
        {BOARD_STATUSES.map((s) => (
          <Skeleton key={s} className="h-[70vh] w-72 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center gap-3">
        <Input
          placeholder="Filtrar tablero…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="max-w-md"
        />
        <p className="text-muted-foreground hidden text-xs md:block">
          Arrastre con reglas de estado · CMD/CTRL+K buscar · N nueva captura
        </p>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={onDragStart}
        onDragOver={onDragOver}
        onDragEnd={(e) => void onDragEnd(e)}
      >
        <div className="flex min-h-0 flex-1 gap-3 overflow-x-auto pb-2">
          {BOARD_STATUSES.map((status) => (
            <Column
              key={status}
              status={status}
              items={filtered[status]}
              onOpen={(d) => {
                setSelectedId(d.id);
                setDrawerOpen(true);
              }}
            />
          ))}
        </div>
        <DragOverlay>{active ? <DemandCard demand={active} overlay /> : null}</DragOverlay>
      </DndContext>

      <DemandDrawer
        demandId={selectedId}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onChanged={() => void load()}
      />
    </div>
  );
}
