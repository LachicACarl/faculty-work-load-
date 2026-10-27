import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Analytics from "./Analytics";
import { getKPIHistory, type KPIHistory } from "../services/api";

vi.mock("../services/api", () => ({
  getKPIHistory: vi.fn(),
}));

const getKPIHistoryMock = vi.mocked(getKPIHistory);

function makeKPI(overrides: Partial<KPIHistory["metric_summary"]> = {}): KPIHistory {
  return {
    kpi_points: [],
    metric_summary: {
      data_source: "current_database_aggregates",
      avg_utilization: 62.5,
      avg_match_quality: 0.8,
      total_conflicts: 1,
      faculty_count: 2,
      allocation_count: 3,
      ...overrides,
    },
  };
}

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

beforeEach(() => {
  getKPIHistoryMock.mockReset();
});

describe("Analytics page", () => {
  it("shows the initial loading state while the request is pending", async () => {
    const pending = deferred<KPIHistory>();
    getKPIHistoryMock.mockReturnValue(pending.promise);

    render(<Analytics />);

    expect(screen.getByRole("status").textContent).toMatch(/loading analytics/i);
    pending.resolve(makeKPI());
    await screen.findByText("Faculty records");
  });

  it("renders populated current aggregates", async () => {
    getKPIHistoryMock.mockResolvedValue(makeKPI());

    render(<Analytics />);

    await screen.findByText("Faculty records");
    expect(screen.getByText("Current allocations")).toBeTruthy();
    expect(screen.getByText("62.5%")).toBeTruthy();
    expect(screen.getByText("Current conflicts")).toBeTruthy();
    expect(screen.getByText("Historical trends")).toBeTruthy();
  });

  it("renders the empty and zero-value state without inventing history", async () => {
    getKPIHistoryMock.mockResolvedValue(makeKPI({
      avg_utilization: 0,
      avg_match_quality: 0,
      total_conflicts: 0,
      faculty_count: 0,
      allocation_count: 0,
    }));

    render(<Analytics />);

    await screen.findByText("Faculty records");
    expect(screen.getByText("No workload observations yet.")).toBeTruthy();
    expect(screen.queryByText("Historical trends")).toBeNull();
    expect(screen.queryByText("0.0%")).toBeNull();
  });

  it.each([
    ["malformed response", new Error("The analytics response had an unexpected format.")],
    ["HTTP failure", new Error("API error: Service Unavailable")],
    ["network failure", new TypeError("Failed to fetch")],
  ] as const)("shows an error for %s", async (_label, error) => {
    getKPIHistoryMock.mockRejectedValue(error);

    render(<Analytics />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain(error.message);
    expect(screen.queryByText("Current allocations")).toBeNull();
  });

  it("hides stale metrics after a failed refresh and restores the next valid response", async () => {
    const pendingRefresh = deferred<KPIHistory>();
    getKPIHistoryMock
      .mockResolvedValueOnce(makeKPI())
      .mockReturnValueOnce(pendingRefresh.promise)
      .mockResolvedValueOnce(makeKPI({ avg_utilization: 81.25 }));
    const user = userEvent.setup();

    render(<Analytics />);
    await screen.findByText("62.5%");

    await user.click(screen.getByRole("button", { name: /refresh/i }));
    expect(screen.getByRole("status").textContent).toMatch(/loading analytics/i);
    expect(screen.queryByText("62.5%")).toBeNull();

    pendingRefresh.reject(new Error("refresh failed"));
    expect((await screen.findByRole("alert")).textContent).toContain("refresh failed");
    expect(screen.queryByText("62.5%")).toBeNull();

    await user.click(screen.getByRole("button", { name: /refresh/i }));
    await waitFor(() => expect(screen.getByText("81.3%")).toBeTruthy());
    expect(screen.queryByText("62.5%")).toBeNull();
  });
});
