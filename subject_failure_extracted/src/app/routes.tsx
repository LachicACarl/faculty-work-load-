import { createBrowserRouter } from "react-router";
import Login from "../pages/Login";
import Layout from "./Layout";
import Dashboard from "../pages/Dashboard";
import FacultyPage from "../pages/Faculty";
import ScenarioBuilder from "../pages/ScenarioBuilder";
import AllocationReview from "../pages/AllocationReview";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Login,
  },
  {
    path: "/dashboard",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "faculty", Component: FacultyPage },
      { path: "scenario-builder", Component: ScenarioBuilder },
      { path: "allocation-review", Component: AllocationReview },
    ],
  },
]);
