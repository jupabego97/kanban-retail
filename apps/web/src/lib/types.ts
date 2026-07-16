/** Tipos del dominio alineados con la API FastAPI. */

export type Role = "OWNER" | "MANAGER" | "OPERATOR" | "VIEWER";

export type DemandStatus =
  | "NUEVA"
  | "VALIDANDO"
  | "COTIZANDO"
  | "POR_PEDIR"
  | "EN_CAMINO"
  | "DISPONIBLE"
  | "CERRADA"
  | "DESCARTADA";

export type DemandReason = "OUT_OF_STOCK" | "NOT_CARRIED" | "NEW_RELEASE";

export type DemandChannel = "STORE" | "WHATSAPP" | "PHONE" | "WEB" | "OTHER";

export type Priority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
  created_at?: string;
}

export interface Supplier {
  id: number;
  name: string;
  contact_phone?: string | null;
  email?: string | null;
  lead_days?: number | null;
  notes?: string | null;
  created_at?: string;
}

export interface Product {
  id: number;
  sku?: string | null;
  barcode?: string | null;
  name: string;
  brand?: string | null;
  category?: string | null;
  supplier_id?: number | null;
  is_active: boolean;
  created_at?: string;
}

export interface DemandRequest {
  id: number;
  product_id?: number | null;
  product_name_free?: string | null;
  variant?: string | null;
  quantity: number;
  reason: DemandReason | string;
  channel: DemandChannel | string;
  status: DemandStatus | string;
  priority: Priority | string;
  notes?: string | null;
  customer_contact?: string | null;
  customer_consent: boolean;
  assigned_to_id?: number | null;
  supplier_id?: number | null;
  evidence_url?: string | null;
  sort_order: number;
  version: number;
  opportunity_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface StatusHistory {
  id: number;
  demand_request_id: number;
  from_status?: string | null;
  to_status: string;
  changed_by_id?: number | null;
  note?: string | null;
  created_at: string;
}

export interface BoardColumn {
  status: string;
  items: DemandRequest[];
}

export interface BoardResponse {
  columns: BoardColumn[];
  counts: Record<string, number>;
}

export interface MetricsSummary {
  total_demands: number;
  by_reason: { key: string; count: number }[];
  by_status: { key: string; count: number }[];
  by_channel: { key: string; count: number }[];
  top_products: {
    product_id?: number | null;
    product_name: string;
    count: number;
  }[];
  avg_hours_to_validation: number | null;
  conversion_to_disponible: number;
  discarded_rate: number;
  by_operator: {
    operator_id?: number | null;
    operator_name: string;
    total: number;
    disponible: number;
    descartada: number;
  }[];
  status_counts: Record<string, number>;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const STATUS_LABELS: Record<DemandStatus, string> = {
  NUEVA: "Nueva",
  VALIDANDO: "Validando",
  COTIZANDO: "Cotizando",
  POR_PEDIR: "Por pedir",
  EN_CAMINO: "En camino",
  DISPONIBLE: "Disponible",
  CERRADA: "Cerrada",
  DESCARTADA: "Descartada",
};

export const REASON_LABELS: Record<DemandReason, string> = {
  OUT_OF_STOCK: "Agotado",
  NOT_CARRIED: "No manejado",
  NEW_RELEASE: "Nuevo lanzamiento",
};

export const CHANNEL_LABELS: Record<DemandChannel, string> = {
  STORE: "Tienda",
  WHATSAPP: "WhatsApp",
  PHONE: "Teléfono",
  WEB: "Web",
  OTHER: "Otro",
};

export const PRIORITY_LABELS: Record<Priority, string> = {
  LOW: "Baja",
  MEDIUM: "Media",
  HIGH: "Alta",
  URGENT: "Urgente",
};

export const WIP_LIMITS: Partial<Record<DemandStatus, number>> = {
  VALIDANDO: 8,
  COTIZANDO: 6,
  POR_PEDIR: 10,
  EN_CAMINO: 12,
};

export const BOARD_STATUSES: DemandStatus[] = [
  "NUEVA",
  "VALIDANDO",
  "COTIZANDO",
  "POR_PEDIR",
  "EN_CAMINO",
  "DISPONIBLE",
  "CERRADA",
  "DESCARTADA",
];

export function demandTitle(d: DemandRequest) {
  return d.product_name_free?.trim() || `Producto #${d.product_id ?? d.id}`;
}
