"use client";

import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

type Preview = {
  entity_type: string;
  total_rows: number;
  valid_rows: number;
  errors: { row: number; error: string }[];
  sample?: Record<string, string>[];
};

export default function ImportarPage() {
  const { hasRole } = useAuth();
  const [entityType, setEntityType] = useState<"products" | "suppliers">("products");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [busy, setBusy] = useState(false);

  if (!hasRole("OWNER", "MANAGER")) {
    return (
      <p className="text-muted-foreground text-sm">
        Solo OWNER/MANAGER pueden importar catálogo.
      </p>
    );
  }

  async function runPreview() {
    if (!file) return toast.error("Seleccione un archivo CSV");
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api.upload<Preview>(
        `/api/imports/preview?entity_type=${entityType}`,
        fd,
      );
      setPreview(res);
      toast.success("Vista previa lista");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error en preview");
    } finally {
      setBusy(false);
    }
  }

  async function commit() {
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api.upload<{ rows_ok: number; rows_error: number }>(
        `/api/imports/commit?entity_type=${entityType}`,
        fd,
      );
      toast.success(`Importados ${res.rows_ok} · errores ${res.rows_error}`);
      setPreview(null);
      setFile(null);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error al importar");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Importar CSV</h1>
        <p className="text-muted-foreground text-sm">
          Preview autenticado y commit auditado. Productos: columnas{" "}
          <code>sku,name,barcode,brand,category</code>. Proveedores:{" "}
          <code>name,contact_phone,email,lead_days</code>.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Archivo</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Tipo</Label>
            <Select
              value={entityType}
              onValueChange={(v) => setEntityType(v as "products" | "suppliers")}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="products">Productos</SelectItem>
                <SelectItem value="suppliers">Proveedores</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <div className="flex gap-2">
            <Button disabled={busy} onClick={() => void runPreview()}>
              Vista previa
            </Button>
            <Button
              disabled={busy || !preview || preview.valid_rows === 0}
              variant="secondary"
              onClick={() => void commit()}
            >
              Confirmar importación
            </Button>
          </div>
        </CardContent>
      </Card>

      {preview ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Preview · {preview.valid_rows}/{preview.total_rows} válidas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {preview.errors.slice(0, 20).map((err) => (
              <p key={`${err.row}-${err.error}`} className="text-destructive">
                Fila {err.row}: {err.error}
              </p>
            ))}
            {preview.errors.length === 0 ? (
              <p className="text-muted-foreground">Sin errores de validación.</p>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
