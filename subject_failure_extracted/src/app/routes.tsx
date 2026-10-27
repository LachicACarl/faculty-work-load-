import { lazy, Suspense, type ComponentType, type LazyExoticComponent } from "react";
import { createBrowserRouter } from "react-router";
import Layout from "./Layout";

const Login = lazy(() => import("../pages/Login"));
const Dashboard = lazy(() => import("../pages/Dashboard"));
const FacultyPage = lazy(() => import("../pages/Faculty"));
const ScenarioBuilder = lazy(() => import("../pages/ScenarioBuilder"));
const AllocationReview = lazy(() => import("../pages/AllocationReview"));

function RouteLoading() {
  return <div role="status" aria-live="polite">Loading page…</div>;
}

function withSuspense(Component: LazyExoticComponent<ComponentType>) {
  return (
    <Suspense fallback={<RouteLoading />}>
      <Component />
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    Component: () => withSuspense(Login),
  },
  {
    path: "/dashboard",
    Component: Layout,
    children: [
      { index: true, Component: () => withSuspense(Dashboard) },
      { path: "faculty", Component: () => withSuspense(FacultyPage) },
      { path: "scenario-builder", Component: () => withSuspense(ScenarioBuilder) },
      { path: "allocation-review", Component: () => withSuspense(AllocationReview) },
    ],
  },
]);
