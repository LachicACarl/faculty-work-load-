/**
 * API Service - Handles all communication with the backend
 * Base URL: http://127.0.0.1:8001
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

// Types
export interface OptimizationRequest {
  policy_id?: number;
  ft_max_units?: number;
  pt_max_units?: number;
  overload_limit?: number;
  specialization_required?: boolean;
  balance_priority?: number;
}

export interface AllocationDetail {
  faculty_name: string;
  section_code: string;
  subject_name: string;
  units: number;
  match_quality: number;
  match_level: "Exact" | "Partial" | "Unmatched";
  explanation: string;
  approval_status: "pending" | "approved" | "flagged";
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

export interface FacultyData {
  id: number;
  employee_id: string;
  full_name: string;
  employment_type: "full-time" | "part-time";
  tenure_status: string;
  max_units: number;
  overload_allowed: boolean;
  available: boolean;
}

export interface PolicyProfile {
  id: number;
  name: string;
  ft_max_units: number;
  pt_max_units: number;
  overload_limit: number;
  specialization_required: boolean;
  balance_priority: number;
}

export interface KPIHistory {
  timestamp: string;
  faculty_utilization: number;
  avg_match_quality: number;
  conflict_frequency: number;
}

// Helper function for API calls
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
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
    throw new Error(error.detail || `API error: ${response.statusText}`);
  }

  return response.json();
}

// Health Check
export async function getHealth() {
  return apiCall("/health");
}

// Workload Optimization
export async function runOptimization(request: OptimizationRequest) {
  return apiCall<OptimizationResponse>("/api/workload/optimize", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getPolicyProfiles() {
  return apiCall<PolicyProfile[]>("/api/workload/policy-profiles");
}

export async function getAllocations(runId: string) {
  return apiCall<AllocationDetail[]>(`/api/workload/allocations?run_id=${runId}`);
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
  return apiCall<FacultyData[]>("/api/faculty/");
}

export async function getFacultyById(id: number) {
  return apiCall<FacultyData>(`/api/faculty/${id}`);
}

export async function createFaculty(data: Partial<FacultyData>) {
  return apiCall<FacultyData>("/api/faculty/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateFaculty(id: number, data: Partial<FacultyData>) {
  return apiCall<FacultyData>(`/api/faculty/${id}`, {
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
  return apiCall("/api/curriculum/subjects");
}

export async function getSections(semester?: string) {
  const url = semester
    ? `/api/curriculum/sections?semester=${semester}`
    : "/api/curriculum/sections";
  return apiCall(url);
}

// Analytics
export async function getKPIHistory() {
  return apiCall<KPIHistory[]>("/api/analytics/kpi-history");
}

export async function getConflictAnalysis() {
  return apiCall("/api/analytics/conflict-analysis");
}

// Reports
export async function getWorkloadSummary() {
  return apiCall("/api/reports/workload-summary");
}

export async function downloadWorkloadSummary() {
  const response = await fetch(`${API_BASE_URL}/api/reports/workload-summary.csv`);
  if (!response.ok) {
    throw new Error("Failed to download report");
  }
  return response.blob();
}

// Institutional
export async function getInstitutionalSnapshot() {
  return apiCall("/api/institutional/snapshot");
}
