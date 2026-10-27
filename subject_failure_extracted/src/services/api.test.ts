import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  downloadWorkloadSummary,
  getKPIHistory,
  getWorkloadSummary,
  type KPIHistory,
  type WorkloadSummaryRow,
} from "./api";

function kpi(overrides: Partial<KPIHistory> = {}): KPIHistory {
  return {
    kpi_points: [
      { timestamp: "2026-10-24", metric_name: "faculty_utilization", value: 62.5 },
    ],
    metric_summary: {
      data_source: "current_database_aggregates",
      avg_utilization: 62.5,
      avg_match_quality: 0.8,
      total_conflicts: 1,
      faculty_count: 2,
      allocation_count: 3,
    },
    ...overrides,
  };
}

function reportRow(overrides: Partial<WorkloadSummaryRow> = {}): WorkloadSummaryRow {
  return {
    faculty_name: "Faculty Alpha",
    employment_type: "full-time",
    assigned_units: 3,
    max_units: 6,
    utilization_percent: 50,
    num_sections: 1,
    avg_match_quality: 0.8,
    conflicts: 0,
    ...overrides,
  };
}

function jsonResponse(body: unknown, status = 200, statusText = "OK"): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    headers: { get: () => null },
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

function csvResponse(
  blob: Blob,
  contentType = "text/csv; charset=utf-8",
  disposition = 'attachment; filename="workload_summary.csv"',
): Response {
  return {
    ok: true,
    status: 200,
    statusText: "OK",
    headers: {
      get: (name: string) => {
        if (name.toLowerCase() === "content-type") return contentType;
        if (name.toLowerCase() === "content-disposition") return disposition;
        return null;
      },
    },
    blob: vi.fn().mockResolvedValue(blob),
  } as unknown as Response;
}

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});

describe("Analytics API service", () => {
  it("accepts a valid KPI payload", async () => {
    const payload = kpi();
    fetchMock.mockResolvedValue(jsonResponse(payload));

    await expect(getKPIHistory()).resolves.toEqual(payload);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/analytics/kpi-history");
  });

  it("accepts empty history and zero-valued aggregates", async () => {
    const payload = kpi({
      kpi_points: [],
      metric_summary: {
        data_source: "current_database_aggregates",
        avg_utilization: 0,
        avg_match_quality: 0,
        total_conflicts: 0,
        faculty_count: 0,
        allocation_count: 0,
      },
    });
    fetchMock.mockResolvedValue(jsonResponse(payload));

    await expect(getKPIHistory()).resolves.toEqual(payload);
  });

  it.each([
    ["wrong kpi_points shape", { ...kpi(), kpi_points: {} }],
    ["missing required field", { ...kpi(), metric_summary: { ...kpi().metric_summary, allocation_count: undefined } }],
    ["wrong numeric type", { ...kpi(), metric_summary: { ...kpi().metric_summary, avg_utilization: "62.5" } }],
    ["non-finite number", { ...kpi(), metric_summary: { ...kpi().metric_summary, avg_utilization: Number.NaN } }],
    ["malformed point", { ...kpi(), kpi_points: [{ timestamp: "today", metric_name: "utilization", value: "high" }] }],
  ] as const)("rejects a KPI payload with %s", async (_label, payload) => {
    fetchMock.mockResolvedValue(jsonResponse(payload));

    await expect(getKPIHistory()).rejects.toThrow("analytics response had an unexpected format");
  });

  it("surfaces HTTP errors as ApiError with the status and detail", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Backend unavailable" }, 503, "Service Unavailable"));

    await expect(getKPIHistory()).rejects.toMatchObject({
      name: "ApiError",
      status: 503,
      message: "Backend unavailable",
    });
  });

  it("propagates network rejection", async () => {
    const failure = new TypeError("Failed to fetch");
    fetchMock.mockRejectedValue(failure);

    await expect(getKPIHistory()).rejects.toBe(failure);
  });
});

describe("Reports API service", () => {
  it("accepts a valid report row", async () => {
    const payload = [reportRow()];
    fetchMock.mockResolvedValue(jsonResponse(payload));

    await expect(getWorkloadSummary()).resolves.toEqual(payload);
  });

  it("accepts an empty report result", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));

    await expect(getWorkloadSummary()).resolves.toEqual([]);
  });

  it.each([
    ["non-array result", { rows: [reportRow()] }],
    ["missing required field", [{ ...reportRow(), conflicts: undefined }]],
    ["incorrect field type", [{ ...reportRow(), assigned_units: "3" }]],
    ["non-finite numeric field", [{ ...reportRow(), utilization_percent: Number.POSITIVE_INFINITY }]],
  ] as const)("rejects Reports data with %s", async (_label, payload) => {
    fetchMock.mockResolvedValue(jsonResponse(payload));

    await expect(getWorkloadSummary()).rejects.toThrow("workload report response had an unexpected format");
  });

  it("surfaces HTTP errors through the shared API error contract", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Reports unavailable" }, 503, "Service Unavailable"));

    await expect(getWorkloadSummary()).rejects.toMatchObject({
      name: "ApiError",
      status: 503,
      message: "Reports unavailable",
    });
    await expect(getWorkloadSummary()).rejects.toBeInstanceOf(ApiError);
  });

  it("propagates network rejection", async () => {
    const failure = new TypeError("Failed to fetch");
    fetchMock.mockRejectedValue(failure);

    await expect(getWorkloadSummary()).rejects.toBe(failure);
  });
});

describe("CSV API service", () => {
  it("accepts CSV content and extracts its attachment filename", async () => {
    const blob = new Blob(["Faculty Name\nFaculty Alpha"], { type: "text/csv" });
    fetchMock.mockResolvedValue(csvResponse(blob));

    await expect(downloadWorkloadSummary()).resolves.toEqual({
      blob,
      filename: "workload_summary.csv",
    });
    expect(fetchMock.mock.calls[0][0]).toContain("/api/reports/workload-summary.csv");
  });

  it("rejects a CSV request with an unexpected content type", async () => {
    fetchMock.mockResolvedValue(csvResponse(new Blob(["html"]), "text/html"));

    await expect(downloadWorkloadSummary()).rejects.toThrow("did not return a CSV file");
  });

  it("rejects an empty CSV response body", async () => {
    fetchMock.mockResolvedValue(csvResponse(new Blob([])));

    await expect(downloadWorkloadSummary()).rejects.toThrow("report response was empty");
  });

  it("rejects CSV HTTP failures", async () => {
    fetchMock.mockResolvedValue({
      ...jsonResponse({ detail: "CSV unavailable" }, 503, "Service Unavailable"),
      blob: vi.fn(),
    } as unknown as Response);

    await expect(downloadWorkloadSummary()).rejects.toThrow("CSV unavailable");
  });

  it("propagates CSV network rejection", async () => {
    const failure = new TypeError("Failed to fetch");
    fetchMock.mockRejectedValue(failure);

    await expect(downloadWorkloadSummary()).rejects.toBe(failure);
  });
});
