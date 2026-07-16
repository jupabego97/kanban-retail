"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { DemandChannel, DemandReason, Page, Priority, Product } from "@/lib/types";
import { REASON_LABELS, CHANNEL_LABELS, PRIORITY_LABELS } from "@/lib/types";

type FormState = {
  product_id: number | null;
  product_name_free: string;
  variant: string;
  quantity: number;
  reason: DemandReason;
  channel: DemandChannel;
  priority: Priority;
  notes: string;
  customer_contact: string;
  customer_consent: boolean;
  evidence_url: string;
};

const initial: FormState = {
  product_id: null,
  product_name_free: "",
  variant: "",
  quantity: 1,
  reason: "OUT_OF_STOCK",
  channel: "STORE",
  priority: "MEDIUM",
  notes: "",
  customer_contact: "",
  customer_consent: false,
  evidence_url: "",
};

export function CaptureForm() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [suggestions, setSuggestions] = useState<Product[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState<FormState>(initial);

  useEffect(() => {
    const t = setTimeout(() => {
      if (!q.trim()) {
        setSuggestions([]);
        return;
      }
      void (async () => {
        try {
          const page = await api.get<Page<Product>>("/api/products", { q, size: 8 });
          setSuggestions(page.items);
          if (/^\d{6,}$/.test(q.trim()) && page.items.length === 1) {
            const p = page.items[0];
            setForm((f) => ({
              ...f,
              product_id: p.id,
              product_name_free: p.name,
            }));
          }
        } catch {
          setSuggestions([]);
        }
      })();
    }, 180);
    return () => clearTimeout(t);
  }, [q]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.product_id && !form.product_name_free.trim()) {
      toast.error("Seleccione un producto o escriba el nombre");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/demands", {
        product_id: form.product_id,
        product_name_free: form.product_name_free || null,
        variant: form.variant || null,
        quantity: form.quantity,
        reason: form.reason,
        channel: form.channel,
        priority: form.priority,
        notes: form.notes || null,
        evidence_url: form.evidence_url || null,
        customer_consent: form.customer_consent,
        customer_contact: form.customer_consent ? form.customer_contact || null : null,
      });
      toast.success("Demanda registrada");
      setForm(initial);
      setQ("");
      router.push("/demandas");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo guardar");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="mx-auto max-w-2xl">
      <CardHeader>
        <CardTitle>Captura rápida de demanda</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={(e) => void onSubmit(e)}>
          <div className="space-y-2">
            <Label>Buscar producto / código de barras</Label>
            <Input
              autoFocus
              placeholder="Escriba nombre o escanee código…"
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setForm((f) => ({
                  ...f,
                  product_id: null,
                  product_name_free: e.target.value,
                }));
              }}
            />
            {suggestions.length > 0 ? (
              <ul className="rounded-md border">
                {suggestions.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      className="hover:bg-muted w-full px-3 py-2 text-left text-sm"
                      onClick={() => {
                        setForm((f) => ({
                          ...f,
                          product_id: p.id,
                          product_name_free: p.name,
                        }));
                        setQ(p.name);
                        setSuggestions([]);
                      }}
                    >
                      <span className="font-medium">{p.name}</span>
                      <span className="text-muted-foreground ml-2 text-xs">
                        {p.sku || p.barcode || ""}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
            <p className="text-muted-foreground text-xs">
              Si el producto no existe, guarde el nombre libre con motivo adecuado.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Cantidad</Label>
              <Input
                type="number"
                min={1}
                value={form.quantity}
                onChange={(e) =>
                  setForm((f) => ({ ...f, quantity: Number(e.target.value) || 1 }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Variante</Label>
              <Input
                placeholder="Talla, color, modelo…"
                value={form.variant}
                onChange={(e) => setForm((f) => ({ ...f, variant: e.target.value }))}
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label>Motivo</Label>
              <Select
                value={form.reason}
                onValueChange={(v) =>
                  setForm((f) => ({ ...f, reason: v as DemandReason }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(REASON_LABELS).map(([k, v]) => (
                    <SelectItem key={k} value={k}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Canal</Label>
              <Select
                value={form.channel}
                onValueChange={(v) =>
                  setForm((f) => ({ ...f, channel: v as DemandChannel }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CHANNEL_LABELS).map(([k, v]) => (
                    <SelectItem key={k} value={k}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Prioridad</Label>
              <Select
                value={form.priority}
                onValueChange={(v) =>
                  setForm((f) => ({ ...f, priority: v as Priority }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PRIORITY_LABELS).map(([k, v]) => (
                    <SelectItem key={k} value={k}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Notas del vendedor</Label>
            <Textarea
              rows={3}
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            />
          </div>

          <div className="space-y-2">
            <Label>Evidencia (URL opcional)</Label>
            <Input
              placeholder="https://…"
              value={form.evidence_url}
              onChange={(e) => setForm((f) => ({ ...f, evidence_url: e.target.value }))}
            />
          </div>

          <div className="flex items-start gap-3 rounded-md border p-3">
            <Checkbox
              checked={form.customer_consent}
              onCheckedChange={(v) =>
                setForm((f) => ({ ...f, customer_consent: Boolean(v) }))
              }
            />
            <div>
              <Label>El cliente autoriza contacto</Label>
              <p className="text-muted-foreground text-xs">
                Solo guarde teléfono/email si hay consentimiento explícito.
              </p>
            </div>
          </div>

          {form.customer_consent ? (
            <div className="space-y-2">
              <Label>Contacto del cliente</Label>
              <Input
                placeholder="WhatsApp / email"
                value={form.customer_contact}
                onChange={(e) =>
                  setForm((f) => ({ ...f, customer_contact: e.target.value }))
                }
              />
            </div>
          ) : null}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => router.push("/demandas")}>
              Cancelar
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Guardando…" : "Registrar demanda"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
