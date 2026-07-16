"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { api } from "@/lib/api";
import type { DemandRequest, Page } from "@/lib/types";
import { demandTitle } from "@/lib/types";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<DemandRequest[]>([]);
  const router = useRouter();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "n" && !e.metaKey && !e.ctrlKey && !e.altKey) {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || (e.target as HTMLElement)?.isContentEditable)
          return;
        e.preventDefault();
        router.push("/demandas/captura");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router]);

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => {
      void (async () => {
        try {
          const page = await api.get<Page<DemandRequest>>("/api/demands", {
            q: q || undefined,
            size: 12,
          });
          setResults(page.items);
        } catch {
          setResults([]);
        }
      })();
    }, 200);
    return () => clearTimeout(t);
  }, [q, open]);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput
        placeholder="Buscar demanda, producto o serial…"
        value={q}
        onValueChange={setQ}
      />
      <CommandList>
        <CommandEmpty>Sin resultados.</CommandEmpty>
        <CommandGroup heading="Navegación">
          <CommandItem
            onSelect={() => {
              setOpen(false);
              router.push("/demandas");
            }}
          >
            Tablero Kanban
          </CommandItem>
          <CommandItem
            onSelect={() => {
              setOpen(false);
              router.push("/demandas/captura");
            }}
          >
            Nueva captura (N)
          </CommandItem>
          <CommandItem
            onSelect={() => {
              setOpen(false);
              router.push("/metricas");
            }}
          >
            Métricas
          </CommandItem>
        </CommandGroup>
        <CommandGroup heading="Demandas">
          {results.map((d) => (
            <CommandItem
              key={d.id}
              onSelect={() => {
                setOpen(false);
                router.push(`/demandas?id=${d.id}`);
              }}
            >
              #{d.id} · {demandTitle(d)} · {d.status}
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
