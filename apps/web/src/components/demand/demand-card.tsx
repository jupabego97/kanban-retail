"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { AlertTriangle, Package } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CHANNEL_LABELS,
  PRIORITY_LABELS,
  REASON_LABELS,
  demandTitle,
  type DemandChannel,
  type DemandRequest,
  type DemandReason,
  type Priority,
} from "@/lib/types";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";

function ageTone(createdAt: string) {
  const days = (Date.now() - new Date(createdAt).getTime()) / 86400000;
  if (days < 3) return "text-emerald-400";
  if (days <= 7) return "text-amber-400";
  return "text-rose-400 animate-pulse";
}

export function DemandCard({
  demand,
  onOpen,
  overlay,
}: {
  demand: DemandRequest;
  onOpen?: (d: DemandRequest) => void;
  overlay?: boolean;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: demand.id,
    data: { status: demand.status },
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <Card
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={() => onOpen?.(demand)}
      className={cn(
        "cursor-grab border-border/70 bg-card/90 active:cursor-grabbing",
        isDragging && "opacity-40",
        overlay && "shadow-2xl ring-2 ring-primary/40",
        demand.reason === "NEW_RELEASE" && "border-dashed",
      )}
    >
      <CardHeader className="space-y-1 p-3 pb-1">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="line-clamp-2 text-sm font-medium leading-snug">
            {demandTitle(demand)}
          </CardTitle>
          <Badge variant="outline" className="shrink-0 text-[10px]">
            #{demand.id}
          </Badge>
        </div>
        {demand.variant ? (
          <p className="text-muted-foreground text-xs">{demand.variant}</p>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-2 p-3 pt-1">
        <div className="flex flex-wrap gap-1">
          <Badge variant="secondary" className="text-[10px]">
            {REASON_LABELS[demand.reason as DemandReason] ?? demand.reason}
          </Badge>
          <Badge variant="outline" className="text-[10px]">
            x{demand.quantity}
          </Badge>
          <Badge
            className={cn(
              "text-[10px]",
              demand.priority === "URGENT" && "bg-rose-600 text-white",
              demand.priority === "HIGH" && "bg-orange-600 text-white",
            )}
            variant="outline"
          >
            {PRIORITY_LABELS[demand.priority as Priority] ?? demand.priority}
          </Badge>
        </div>
        <div className="text-muted-foreground flex items-center justify-between text-[11px]">
          <span className="inline-flex items-center gap-1">
            <Package className="size-3" />
            {CHANNEL_LABELS[demand.channel as DemandChannel] ?? demand.channel}
          </span>
          <span className={ageTone(demand.created_at)}>
            {formatDistanceToNow(new Date(demand.created_at), {
              addSuffix: true,
              locale: es,
            })}
          </span>
        </div>
        {demand.notes ? (
          <p className="text-muted-foreground line-clamp-2 text-[11px]">{demand.notes}</p>
        ) : null}
        {demand.reason === "OUT_OF_STOCK" ? (
          <p className="text-amber-400 inline-flex items-center gap-1 text-[10px]">
            <AlertTriangle className="size-3" /> Quiebre de stock
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
