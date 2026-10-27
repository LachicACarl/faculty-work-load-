import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Reports from "./Reports";
import {
  downloadWorkloadSummary,
  getWorkloadSummary,
  type WorkloadSummaryRow,
} from "../services/api";

vi.mock("../services/api", () => ({
  downloadWorkloadSummary: vi.fn(),
  getWorkloadSummary: vi.fn(),
}));

const downloadWorkloadSummaryMock = vi.mocked(downloadWorkloadSummary);
const getWorkloadSummaryMock = vi.mocked(getWorkloadSummary);

function row(overrides: Partial<WorkloadSummaryRow> = {}): WorkloadSummaryRow {
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

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function installDownloadMocks() {
  const createDescriptor = Object.getOwnPropertyDescriptor(URL, "createObjectURL");
  const revokeDescriptor = Object.getOwnPropertyDescriptor(URL, "revokeObjectURL");
  const createObjectURL = vi.fn(() => "blob:ofwas-test");
  const revokeObjectURL = vi.fn();
  let clickedFilename = "";

  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: createObjectURL,
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    configurable: true,
    value: revokeObjectURL,
  });
  const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(
    function (this: HTMLAnchorElement) {
      clickedFilename = this.download;
    },
  );

  return {
    createObjectURL,
    revokeObjectURL,
    click,
    get clickedFilename() {
      return clickedFilename;
    },
    restore() {
      if (createDescriptor) Object.defineProperty(URL, "createObjectURL", createDescriptor);
      else Reflect.deleteProperty(URL, "createObjectURL");
      if (revokeDescriptor) Object.defineProperty(URL, "revokeObjectURL", revokeDescriptor);
      else Reflect.deleteProperty(URL, "revokeObjectURL");
    },
  };
}

let restoreDownloadMocks = () => {};

beforeEach(() => {
  downloadWorkloadSummaryMock.mockReset();
  getWorkloadSummaryMock.mockReset();
});

afterEach(() => {
  restoreDownloadMocks();
});

describe("Reports page", () => {
  it("shows the initial loading state while the request is pending", async () => {
    const pending = deferred<WorkloadSummaryRow[]>();
    getWorkloadSummaryMock.mockReturnValue(pending.promise);

    render(<Reports />);

    expect(screen.getByRole("status").textContent).toMatch(/loading report rows/i);
    pending.resolve([row()]);
    await screen.findByText("Faculty Alpha");
  });

  it("renders populated report values", async () => {
    getWorkloadSummaryMock.mockResolvedValue([row()]);

    render(<Reports />);

    await screen.findByText("Faculty Alpha");
    expect(screen.getByRole("table")).toBeTruthy();
    expect(screen.getByText("full-time")).toBeTruthy();
    expect(screen.getByText("50.0%")).toBeTruthy();
    expect(screen.getByText("80.0%")).toBeTruthy();
  });

  it("renders the empty result state", async () => {
    getWorkloadSummaryMock.mockResolvedValue([]);

    render(<Reports />);

    expect(await screen.findByText(/no workload report data is available/i)).toBeTruthy();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it.each([
    ["malformed response", new Error("The workload report response had an unexpected format.")],
    ["HTTP failure", new Error("Failed to load report (503)")],
    ["network failure", new TypeError("Failed to fetch")],
  ] as const)("shows an error for %s", async (_label, error) => {
    getWorkloadSummaryMock.mockRejectedValue(error);

    render(<Reports />);

    expect((await screen.findByRole("alert")).textContent).toContain(error.message);
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("clears stale rows on failed refresh and displays a later successful result", async () => {
    const pendingRefresh = deferred<WorkloadSummaryRow[]>();
    getWorkloadSummaryMock
      .mockResolvedValueOnce([row()])
      .mockReturnValueOnce(pendingRefresh.promise)
      .mockResolvedValueOnce([row({ faculty_name: "Faculty Beta", assigned_units: 4 })]);
    const user = userEvent.setup();

    render(<Reports />);
    await screen.findByText("Faculty Alpha");

    await user.click(screen.getByRole("button", { name: /refresh/i }));
    expect(screen.getByRole("status").textContent).toMatch(/loading report rows/i);
    expect(screen.queryByText("Faculty Alpha")).toBeNull();

    pendingRefresh.reject(new Error("refresh failed"));
    expect((await screen.findByRole("alert")).textContent).toContain("refresh failed");
    expect(screen.queryByText("Faculty Alpha")).toBeNull();

    await user.click(screen.getByRole("button", { name: /refresh/i }));
    await waitFor(() => expect(screen.getByText("Faculty Beta")).toBeTruthy());
    expect(screen.queryByText("Faculty Alpha")).toBeNull();
    expect(screen.getByText("4")).toBeTruthy();
  });

  it("downloads a successful CSV through the mocked browser APIs", async () => {
    const blob = new Blob(["Faculty Name\nFaculty Alpha"], { type: "text/csv" });
    getWorkloadSummaryMock.mockResolvedValue([row()]);
    downloadWorkloadSummaryMock.mockResolvedValue({ blob, filename: "workload_summary.csv" });
    const browser = installDownloadMocks();
    restoreDownloadMocks = browser.restore;
    const user = userEvent.setup();

    render(<Reports />);
    await screen.findByText("Faculty Alpha");
    await user.click(screen.getByRole("button", { name: /export csv/i }));

    await screen.findByText("Downloaded workload_summary.csv.");
    expect(browser.createObjectURL).toHaveBeenCalledWith(blob);
    expect(browser.click).toHaveBeenCalledTimes(1);
    expect(browser.clickedFilename).toBe("workload_summary.csv");
    expect(browser.revokeObjectURL).toHaveBeenCalledWith("blob:ofwas-test");
  });

  it.each([
    ["HTTP failure", "Failed to download report (503)"],
    ["unexpected content type", "The report endpoint did not return a CSV file."],
    ["empty body", "The report response was empty."],
    ["network failure", "Failed to fetch"],
  ])("does not initiate a download after %s", async (_label, message) => {
    getWorkloadSummaryMock.mockResolvedValue([row()]);
    downloadWorkloadSummaryMock.mockRejectedValue(new Error(message));
    const browser = installDownloadMocks();
    restoreDownloadMocks = browser.restore;
    const user = userEvent.setup();

    render(<Reports />);
    await screen.findByText("Faculty Alpha");
    await user.click(screen.getByRole("button", { name: /export csv/i }));

    expect((await screen.findByRole("alert")).textContent).toContain(message);
    expect(browser.createObjectURL).not.toHaveBeenCalled();
    expect(browser.click).not.toHaveBeenCalled();
  });
});
