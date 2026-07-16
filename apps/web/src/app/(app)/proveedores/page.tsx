"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Page, Supplier } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { useAuth } from "@/lib/auth";

export default function ProveedoresPage() {
  const { hasRole } = useAuth();
  const [items, setItems] = useState<Supplier[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    contact_phone: "",
    email: "",
    lead_days: "3",
  });

  async function load() {
    try {
      const page = await api.get<Page<Supplier>>("/api/suppliers", { size: 100 });
      setItems(page.items);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Error");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function createSupplier() {
    try {
      await api.post("/api/suppliers", {
        name: form.name,
        contact_phone: form.contact_phone || null,
        email: form.email || null,
        lead_days: form.lead_days ? Number(form.lead_days) : null,
      });
      toast.success("Proveedor creado");
      setOpen(false);
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "No se pudo crear");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Proveedores</h1>
          <p className="text-muted-foreground text-sm">Contactos y plazos de entrega.</p>
        </div>
        {hasRole("OWNER", "MANAGER") ? (
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>Nuevo proveedor</Button>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Nuevo proveedor</DialogTitle>
              </DialogHeader>
              <div className="grid gap-3">
                <div className="space-y-1">
                  <Label>Nombre</Label>
                  <Input
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  />
                </div>
                <div className="space-y-1">
                  <Label>Teléfono</Label>
                  <Input
                    value={form.contact_phone}
                    onChange={(e) => setForm((f) => ({ ...f, contact_phone: e.target.value }))}
                  />
                </div>
                <div className="space-y-1">
                  <Label>Email</Label>
                  <Input
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  />
                </div>
                <div className="space-y-1">
                  <Label>Días de entrega</Label>
                  <Input
                    type="number"
                    value={form.lead_days}
                    onChange={(e) => setForm((f) => ({ ...f, lead_days: e.target.value }))}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => void createSupplier()}>Guardar</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        ) : null}
      </div>

      <div className="rounded-xl border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Teléfono</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Lead (días)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((s) => (
              <TableRow key={s.id}>
                <TableCell className="font-medium">{s.name}</TableCell>
                <TableCell>{s.contact_phone || "—"}</TableCell>
                <TableCell>{s.email || "—"}</TableCell>
                <TableCell>{s.lead_days ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
