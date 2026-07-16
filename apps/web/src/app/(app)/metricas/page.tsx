"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import {
  CHANNEL_LABELS,
  REASON_LABELS,
  STATUS_LABELS,
  type DemandChannel,
  type DemandReason,
  type DemandStatus,
  type MetricsSummary,
} from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`;
}

export default function MetricasPage() {
  const [data, setData] = useState<MetricsSummary | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const m = await api.get<MetricsSummary>("/api/metrics");
        setData(m);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Error al cargar métricas");
      }
    })();
  }, []);

  const reasonChart = useMemo(
    () =>
      (data?.by_reason ?? []).map((r) => ({
        name: REASON_LABELS[r.key as DemandReason] ?? r.key,
        count: r.count,
      })),
    [data],
  );

  const statusChart = useMemo(
    () =>
      (data?.by_status ?? []).map((r) => ({
        name: STATUS_LABELS[r.key as DemandStatus] ?? r.key,
        count: r.count,
      })),
    [data],
  );

  function exportCsv() {
    if (!data) return;
    const rows = [
      ["producto", "consultas"],
      ...data.top_products.map((p) => [p.product_name, String(p.count)]),
    ];
    const blob = new Blob([rows.map((r) => r.join(",")).join("\n")], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "oportunidades-demanda.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!data) {
    return <p className="text-muted-foreground text-sm">Cargando métricas…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Métricas accionables</h1>
          <p className="text-muted-foreground text-sm">
            Cada KPI enlaza a una lista filtrada del tablero.
          </p>
        </div>
        <Button variant="outline" onClick={exportCsv}>
          Exportar CSV oportunidades
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Kpi
          title="Solicitudes"
          value={String(data.total_demands)}
          href="/demandas"
        />
        <Kpi
          title="Horas a validación"
          value={
            data.avg_hours_to_validation == null
              ? "—"
              : data.avg_hours_to_validation.toFixed(1)
          }
          href="/demandas"
        />
        <Kpi
          title="Conversión a disponible"
          value={pct(data.conversion_to_disponible)}
          href="/demandas"
        />
        <Kpi
          title="Tasa de descarte"
          value={pct(data.discarded_rate)}
          href="/demandas"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Por motivo</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={reasonChart}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="oklch(0.7 0.15 250)" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Por estado</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusChart}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="oklch(0.72 0.14 160)" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top productos preguntados</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {data.top_products.map((p) => (
              <Link
                key={`${p.product_id}-${p.product_name}`}
                href="/demandas"
                className="hover:bg-muted flex items-center justify-between rounded-md border px-3 py-2 text-sm"
              >
                <span>{p.product_name}</span>
                <span className="text-muted-foreground">{p.count}</span>
              </Link>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Carga por operador</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {data.by_operator.map((op) => (
              <div
                key={`${op.operator_id}-${op.operator_name}`}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
              >
                <span>{op.operator_name}</span>
                <span className="text-muted-foreground text-xs">
                  total {op.total} · ok {op.disponible} · desc {op.descartada}
                </span>
              </div>
            ))}
            {(data.by_channel ?? []).length > 0 ? (
              <div className="pt-2">
                <p className="mb-2 text-sm font-medium">Canales</p>
                {data.by_channel.map((c) => (
                  <p key={c.key} className="text-muted-foreground text-xs">
                    {CHANNEL_LABELS[c.key as DemandChannel] ?? c.key}: {c.count}
                  </p>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Kpi({ title, value, href }: { title: string; value: string; href: string }) {
  return (
    <Link href={href}>
      <Card className="hover:border-primary/40 transition-colors">
        <CardHeader className="pb-2">
          <CardTitle className="text-muted-foreground text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-semibold tracking-tight">{value}</p>
        </CardContent>
      </Card>
    </Link>
  );
}
