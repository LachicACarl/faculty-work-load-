/** API Service - Handles all communication with the backend. */
const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE_URL = configuredApiBaseUrl || (import.meta.env.DEV ? "http://127.0.0.1:8001" : "");

function getApiBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new Error(
      "OFWAS backend is not configured. Set VITE_API_BASE_URL to the approved backend origin in the frontend deployment settings."
    );
  }

  let parsedUrl: URL;
  try {
    parsedUrl = new URL(API_BASE_URL);
  } catch {
    throw new Error("OFWAS backend configuration is invalid. VITE_API_BASE_URL must be an absolute HTTP(S) origin.");
  }

  const isHttp = parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:";
  const hasOriginOnly = parsedUrl.pathname === "/" && !parsedUrl.search && !parsedUrl.hash;
  if (!isHttp || !hasOriginOnly || parsedUrl.username || parsedUrl.password) {
    throw new Error("OFWAS backend configuration is invalid. VITE_API_BASE_URL must contain only an HTTP(S) origin.");
  }

  const hostname = parsedUrl.hostname.toLowerCase();
  const isLoopback =
    hostname === "localhost" ||
    hostname.endsWith(".localhost") ||
    hostname.startsWith("127.") ||
    hostname === "[::1]";
  if (import.meta.env.PROD && (parsedUrl.protocol !== "https:" || isLoopback)) {
    throw new Error(
      "OFWAS backend configuration is not suitable for production. Set VITE_API_BASE_URL to the verified HTTPS backend origin."
    );
  }

  return parsedUrl.origin;
}

// Types
export interface AllocationDetail {
  id: number;
  faculty_name: string;
  faculty_id: number;
  section_code: string;
  subject_code: string;
  subject_name: string;
  semester: string;
  units: number;
  match_quality: number;
  match_level: "Exact" | "Partial" | "Unmatched";
  workload_balance: number;
  conflict_score: number;
  explanation: string;
  approval_status: "pending" | "approved" | "flagged";
}

export interface OptimizationRequest {
  policy_id?: number;
  ft_max_units?: number;
  pt_max_units?: number;
  overload_limit?: number;
  specialization_required?: boolean;
  balance_priority?: number;
}

export interface OptimizationResponse {
  run_id: string;
  timestamp: string;
  status: "success" | "partial" | "failed";
  allocations: AllocationDetail[];
  total_fitness: number;
  avg_match_quality: number;
  total_conflicts: number;
  facultyWithConflicts: string[];
  metrics: Record<string, any>;
}
export interface FacultyListItem {
  id: number;
  employee_id: string;
  full_name: string;
  employment_type: string;
  max_units: number;
  available: boolean;
}

export interface QualificationInput {
  degree: string;
  specialization: string;
  institution: string;
  year_awarded: number;
  proficiency_level?: number;
}

export interface AvailabilityInput {
  day_of_week: number;
  start_time: string;
  end_time: string;
  recurring?: boolean;
}

export interface FacultyCreateRequest {
  employee_id: string;
  full_name: string;
  employment_type: string;
  tenure_status: string;
  max_units: number;
  overload_allowed?: number;
  available?: boolean;
  qualifications?: QualificationInput[];
  availability?: AvailabilityInput[];
}

export interface QualificationResponse extends QualificationInput {
  id: number;
  faculty_id: number;
  proficiency_level: number;
}

export interface AvailabilityResponse extends AvailabilityInput {
  id: number;
  faculty_id: number;
  recurring: boolean;
}

export interface FacultyDetailResponse extends FacultyCreateRequest {
  id: number;
  user_id: number | null;
  created_at: string;
  overload_allowed: number;
  available: boolean;
  qualifications: QualificationResponse[];
  availability: AvailabilityResponse[];
}

export interface KPIHistory {
  kpi_points: Array<{ timestamp: string; metric_name: string; value: number }>;
  metric_summary: {
    data_source: string;
    avg_utilization: number;
    avg_match_quality: number;
    total_conflicts: number;
    faculty_count: number;
    allocation_count: number;
  };
}

export interface WorkloadSummaryRow {
  faculty_name: string;
  employment_type: string;
  assigned_units: number;
  max_units: number;
  utilization_percent: number;
  num_sections: number;
  avg_match_quality: number;
  conflicts: number;
}

export interface SectionRecord {
  id: number;
  subject_id: number;
  section_code: string;
  semester: string;
  schedule_day: number;
  schedule_start_time: string;
  schedule_end_time: string;
  room: string | null;
  enrollment: number;
  is_planning: boolean;
  assigned: boolean;
}

export interface SubjectRecord {
  id: number;
  code: string;
  name: string;
  units: number;
  required_specialization: string | null;
  min_class_size: number;
  max_class_size: number;
  active: boolean;
}

export interface SubjectCreateRequest {
  code: string;
  name: string;
  units: number;
  required_specialization?: string | null;
  min_class_size?: number;
  max_class_size?: number;
  active?: boolean;
}

export interface SectionCreateRequest {
  subject_id: number;
  section_code: string;
  semester: string;
  schedule_day: number;
  schedule_start_time: string;
  schedule_end_time: string;
  room?: string | null;
  enrollment?: number;
  is_planning?: boolean;
  assigned?: boolean;
}

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function parseKPIHistory(value: unknown): KPIHistory {
  if (!isRecord(value) || !Array.isArray(value.kpi_points) || !isRecord(value.metric_summary)) {
    throw new Error("The analytics response had an unexpected format.");
  }

  const summary = value.metric_summary;
  const summaryIsValid =
    typeof summary.data_source === "string" &&
    isFiniteNumber(summary.avg_utilization) &&
    isFiniteNumber(summary.avg_match_quality) &&
    isFiniteNumber(summary.total_conflicts) &&
    isFiniteNumber(summary.faculty_count) &&
    isFiniteNumber(summary.allocation_count);
  const pointsAreValid = value.kpi_points.every((point) =>
    isRecord(point) &&
    typeof point.timestamp === "string" &&
    typeof point.metric_name === "string" &&
    isFiniteNumber(point.value)
  );

  if (!summaryIsValid || !pointsAreValid) {
    throw new Error("The analytics response had an unexpected format.");
  }
  return value as unknown as KPIHistory;
}

function parseWorkloadSummary(value: unknown): WorkloadSummaryRow[] {
  if (!Array.isArray(value)) {
    throw new Error("The workload report response had an unexpected format.");
  }

  const rowsAreValid = value.every((row) =>
    isRecord(row) &&
    typeof row.faculty_name === "string" &&
    typeof row.employment_type === "string" &&
    isFiniteNumber(row.assigned_units) &&
    isFiniteNumber(row.max_units) &&
    isFiniteNumber(row.utilization_percent) &&
    isFiniteNumber(row.num_sections) &&
    isFiniteNumber(row.avg_match_quality) &&
    isFiniteNumber(row.conflicts)
  );
  if (!rowsAreValid) {
    throw new Error("The workload report response had an unexpected format.");
  }
  return value as WorkloadSummaryRow[];
}

// Helper function for API calls
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${getApiBaseUrl()}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = error.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => {
          const location = Array.isArray(item.loc) ? item.loc.join(".") : "";
          return `${location ? `${location}: ` : ""}${item.msg || "Invalid value"}`;
        }).join("; ")
      : typeof detail === "string"
        ? detail
        : `API error: ${response.statusText}`;
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;
  if (response.headers.get("content-length") === "0") return undefined as T;
  return response.json();
}

export async function runOptimization(request: OptimizationRequest) {
  return apiCall<OptimizationResponse>("/api/workload/optimize", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
// Health Check
export async function getHealth() {
  return apiCall("/health");
}

export async function getAllocations(runId?: string) {
  const suffix = runId ? `?run_id=${encodeURIComponent(runId)}` : "";
  return apiCall<AllocationDetail[]>(`/api/workload/allocations${suffix}`);
}

export async function updateAllocationStatus(
  allocationId: number,
  status: "pending" | "approved" | "flagged"
) {
  return apiCall(`/api/workload/allocations/${allocationId}/status?status=${status}`, {
    method: "PUT",
  });
}

// Faculty Management
export async function getFaculty() {
  return apiCall<FacultyListItem[]>("/api/faculty/");
}

export async function getFacultyById(id: number) {
  return apiCall<FacultyDetailResponse>(`/api/faculty/${id}`);
}

export async function createFaculty(data: FacultyCreateRequest) {
  return apiCall<FacultyDetailResponse>("/api/faculty/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateFaculty(id: number, data: FacultyCreateRequest) {
  return apiCall<FacultyDetailResponse>(`/api/faculty/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteFaculty(id: number) {
  return apiCall(`/api/faculty/${id}`, {
    method: "DELETE",
  });
}

// Curriculum
export async function getSubjects() {
  return apiCall<SubjectRecord[]>("/api/curriculum/subjects");
}

export async function createSubject(data: SubjectCreateRequest) {
  return apiCall<SubjectRecord>("/api/curriculum/subjects", { method: "POST", body: JSON.stringify(data) });
}

export async function getSections(semester?: string) {
  const url = semester
    ? `/api/curriculum/sections?semester=${encodeURIComponent(semester)}`
    : "/api/curriculum/sections";
  return apiCall<SectionRecord[]>(url);
}

export async function createSection(data: SectionCreateRequest) {
  return apiCall<SectionRecord>("/api/curriculum/sections", { method: "POST", body: JSON.stringify(data) });
}

// Analytics
export async function getKPIHistory() {
  return parseKPIHistory(await apiCall<unknown>("/api/analytics/kpi-history"));
}

export async function getConflictAnalysis() {
  return apiCall("/api/analytics/conflict-analysis");
}

// Reports
export async function getWorkloadSummary() {
  return parseWorkloadSummary(await apiCall<unknown>("/api/reports/workload-summary"));
}

export async function downloadWorkloadSummary() {
  const response = await fetch(`${getApiBaseUrl()}/api/reports/workload-summary.csv`);
  if (!response.ok) {
    const error: { detail?: unknown } = await response.json().catch(() => ({}));
    throw new Error(typeof error.detail === "string" ? error.detail : `Failed to download report (${response.status})`);
  }
  if (!(response.headers.get("content-type") ?? "").toLowerCase().includes("text/csv")) {
    throw new Error("The report endpoint did not return a CSV file.");
  }
  const blob = await response.blob();
  if (blob.size === 0) throw new Error("The report response was empty.");
  const disposition = response.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
  const filename = decodeURIComponent(match?.[1] ?? match?.[2] ?? "workload_summary.csv");
  return { blob, filename };
}

// Institutional
export async function getInstitutionalSnapshot() {
  return apiCall("/api/institutional/snapshot");
}
