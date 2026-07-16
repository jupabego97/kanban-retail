"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import {
  CHANNEL_LABELS,
  PRIORITY_LABELS,
  REASON_LABELS,
  STATUS_LABELS,
  demandTitle,
  type DemandChannel,
  type DemandRequest,
  type DemandReason,
  type DemandStatus,
  type Priority,
  type StatusHistory,
} from "@/lib/types";
import { useAuth } from "@/lib/auth";

export function DemandDrawer({
  demandId,
  open,
  onOpenChange,
  onChanged,
}: {
  demandId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onChanged?: () => void;
}) {
  const { hasRole } = useAuth();
  const [demand, setDemand] = useState<DemandRequest | null>(null);
  const [history, setHistory] = useState<StatusHistory[]>([]);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !demandId) return;
    void (async () => {
      setLoading(true);
      try {
        const [d, h] = await Promise.all([
          api.get<DemandRequest>(`/api/demands/${demandId}`),
          api.get<StatusHistory[]>(`/api/demands/${demandId}/history`),
        ]);
        setDemand(d);
        setHistory(h);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "No se pudo cargar");
      } finally {
        setLoading(false);
      }
    })();
  }, [open, demandId]);

  async function consolidate() {
    if (!demand) return;
    try {
      await api.post(`/api/demands/${demand.id}/consolidate`, { note: note || undefined });
      toast.success("Interés consolidado");
      setNote("");
      onChanged?.();
      const refreshed = await api.get<DemandRequest>(`/api/demands/${demand.id}`);
      setDemand(refreshed);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error al consolidar");
    }
  }

  const canEdit = hasRole("OWNER", "MANAGER", "OPERATOR");

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>
            {demand ? demandTitle(demand) : loading ? "Cargando…" : "Demanda"}
          </SheetTitle>
          <SheetDescription>
            {demand ? `Solicitud #${demand.id} · v${demand.version}` : "Detalle de la solicitud"}
          </SheetDescription>
        </SheetHeader>

        {demand ? (
          <div className="mt-4 space-y-4 px-1">
            <div className="flex flex-wrap gap-2">
              <Badge>{STATUS_LABELS[demand.status as DemandStatus] ?? demand.status}</Badge>
              <Badge variant="secondary">
                {REASON_LABELS[demand.reason as DemandReason] ?? demand.reason}
              </Badge>
              <Badge variant="outline">
                {CHANNEL_LABELS[demand.channel as DemandChannel] ?? demand.channel}
              </Badge>
              <Badge variant="outline">
                {PRIORITY_LABELS[demand.priority as Priority] ?? demand.priority}
              </Badge>
            </div>

            <Tabs defaultValue="detalle">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="detalle">Detalle</TabsTrigger>
                <TabsTrigger value="historial">Historial</TabsTrigger>
                <TabsTrigger value="interes">Interés</TabsTrigger>
              </TabsList>
              <TabsContent value="detalle" className="space-y-3 text-sm">
                <Row label="Cantidad" value={String(demand.quantity)} />
                <Row label="Variante" value={demand.variant || "—"} />
                <Row label="Contacto" value={demand.customer_contact || "—"} />
                <Row
                  label="Consentimiento"
                  value={demand.customer_consent ? "Sí" : "No"}
                />
                <Row label="Notas" value={demand.notes || "—"} />
                {demand.evidence_url ? (
                  <a
                    className="text-primary text-sm underline"
                    href={demand.evidence_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Ver evidencia
                  </a>
                ) : null}
              </TabsContent>
              <TabsContent value="historial" className="space-y-3">
                {history.length === 0 ? (
                  <p className="text-muted-foreground text-sm">Sin historial aún.</p>
                ) : (
                  history.map((h) => (
                    <div key={h.id} className="rounded-md border p-3 text-sm">
                      <p className="font-medium">
                        {(h.from_status &&
                          (STATUS_LABELS[h.from_status as DemandStatus] ?? h.from_status)) ||
                          "—"}{" "}
                        → {STATUS_LABELS[h.to_status as DemandStatus] ?? h.to_status}
                      </p>
                      <p className="text-muted-foreground text-xs">
                        {new Date(h.created_at).toLocaleString("es-CO")}
                      </p>
                      {h.note ? <p className="mt-1 text-xs">{h.note}</p> : null}
                    </div>
                  ))
                )}
              </TabsContent>
              <TabsContent value="interes" className="space-y-3">
                <p className="text-muted-foreground text-sm">
                  Registra otro cliente que preguntó por el mismo producto sin crear una tarjeta
                  nueva.
                </p>
                <Textarea
                  placeholder="Nota opcional del interés…"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  disabled={!canEdit}
                />
                <Button onClick={() => void consolidate()} disabled={!canEdit}>
                  Consolidar interés
                </Button>
              </TabsContent>
            </Tabs>
            <Separator />
            <p className="text-muted-foreground text-xs">
              Arrastra la tarjeta en el tablero para cambiar de estado. Esc cierra este panel.
            </p>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-border/50 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  );
}
