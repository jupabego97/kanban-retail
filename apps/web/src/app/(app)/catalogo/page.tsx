"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Page, Product } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";

export default function CatalogoPage() {
  const { hasRole } = useAuth();
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Product[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", sku: "", barcode: "", brand: "", category: "" });

  async function load() {
    try {
      const page = await api.get<Page<Product>>("/api/products", { q: q || undefined, size: 100 });
      setItems(page.items);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error");
    }
  }

  useEffect(() => {
    const t = setTimeout(() => void load(), 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  async function createProduct() {
    try {
      if (!form.name.trim() || !form.sku.trim()) {
        toast.error("Nombre y SKU son obligatorios");
        return;
      }
      await api.post("/api/products", {
        name: form.name.trim(),
        sku: form.sku.trim(),
        barcode: form.barcode || null,
        brand: form.brand || null,
        category: form.category || null,
      });
      toast.success("Producto creado");
      setOpen(false);
      setForm({ name: "", sku: "", barcode: "", brand: "", category: "" });
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "No se pudo crear");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Catálogo</h1>
          <p className="text-muted-foreground text-sm">Productos locales de la tienda.</p>
        </div>
        <div className="flex gap-2">
          <Input
            className="w-64"
            placeholder="Buscar nombre, SKU, barcode…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          {hasRole("OWNER", "MANAGER", "OPERATOR") ? (
            <Dialog open={open} onOpenChange={setOpen}>
              <Button onClick={() => setOpen(true)}>Nuevo</Button>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Nuevo producto</DialogTitle>
                </DialogHeader>
                <div className="grid gap-3">
                  {(
                    [
                      ["name", "Nombre"],
                      ["sku", "SKU"],
                      ["barcode", "Código de barras"],
                      ["brand", "Marca"],
                      ["category", "Categoría"],
                    ] as const
                  ).map(([key, label]) => (
                    <div key={key} className="space-y-1">
                      <Label>{label}</Label>
                      <Input
                        value={form[key]}
                        onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                      />
                    </div>
                  ))}
                </div>
                <DialogFooter>
                  <Button onClick={() => void createProduct()}>Guardar</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          ) : null}
        </div>
      </div>

      <div className="rounded-xl border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>SKU</TableHead>
              <TableHead>Barcode</TableHead>
              <TableHead>Marca</TableHead>
              <TableHead>Categoría</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="font-medium">{p.name}</TableCell>
                <TableCell>{p.sku || "—"}</TableCell>
                <TableCell>{p.barcode || "—"}</TableCell>
                <TableCell>{p.brand || "—"}</TableCell>
                <TableCell>{p.category || "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
