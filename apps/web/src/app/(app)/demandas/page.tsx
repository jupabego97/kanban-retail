"use client";

import { Suspense } from "react";
import { KanbanBoard } from "@/components/demand/kanban-board";
import { Skeleton } from "@/components/ui/skeleton";

export default function DemandasPage() {
  return (
    <div className="flex h-[calc(100vh-5.5rem)] flex-col gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Tablero de demanda</h1>
        <p className="text-muted-foreground text-sm">
          Priorice lo que los clientes piden y hoy no puede vender.
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-full w-full" />}>
        <KanbanBoard />
      </Suspense>
    </div>
  );
}
