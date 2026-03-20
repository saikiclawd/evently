"""
EventFlow Pro — Route Optimizer (AI Auto-Route)

Uses Google OR-Tools to solve the Traveling Salesman Problem (TSP)
for multi-stop delivery routes.
"""
import math
from app.extensions import db
from app.models.operations import Route, RouteStop


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in miles."""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _estimate_drive_minutes(distance_miles):
    """Estimate drive time assuming 25 mph average (urban delivery)."""
    return int(distance_miles / 25 * 60)


def optimize_route(route):
    """
    Optimize stop order for a route using OR-Tools TSP solver.
    Falls back to nearest-neighbor heuristic if OR-Tools unavailable.
    """
    stops = route.stops.order_by(RouteStop.stop_order).all()

    if len(stops) <= 2:
        return {"message": "Route too short to optimize", "stops": len(stops)}

    # Filter stops with coordinates
    geo_stops = [s for s in stops if s.lat and s.lng]
    if len(geo_stops) < 2:
        return {"message": "Not enough stops with coordinates"}

    try:
        optimized_order = _solve_tsp_ortools(geo_stops)
    except ImportError:
        optimized_order = _solve_nearest_neighbor(geo_stops)

    # Apply new order
    total_distance = 0
    total_drive_time = 0

    for new_idx, stop_idx in enumerate(optimized_order):
        stop = geo_stops[stop_idx]
        stop.stop_order = new_idx

        if new_idx > 0:
            prev = geo_stops[optimized_order[new_idx - 1]]
            dist = _haversine_distance(prev.lat, prev.lng, stop.lat, stop.lng)
            drive_min = _estimate_drive_minutes(dist)
            stop.drive_minutes_from_prev = drive_min
            total_distance += dist
            total_drive_time += drive_min

    route.total_distance_miles = round(total_distance, 1)
    route.total_drive_minutes = total_drive_time
    route.optimized_order = optimized_order

    return {
        "message": "Route optimized",
        "stops": len(geo_stops),
        "total_distance_miles": route.total_distance_miles,
        "total_drive_minutes": route.total_drive_minutes,
    }


def _solve_tsp_ortools(stops):
    """Solve TSP using Google OR-Tools."""
    from ortools.constraint_solver import routing_enums_pb2, pywrapcp

    n = len(stops)

    # Build distance matrix
    dist_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist_matrix[i][j] = int(
                    _haversine_distance(stops[i].lat, stops[i].lng, stops[j].lat, stops[j].lng) * 100
                )

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return dist_matrix[from_node][to_node]

    transit_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = 5

    solution = routing.SolveWithParameters(search_params)

    if solution:
        order = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            order.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        return order

    # Fallback
    return _solve_nearest_neighbor(stops)


def _solve_nearest_neighbor(stops):
    """Simple nearest-neighbor heuristic fallback."""
    n = len(stops)
    visited = [False] * n
    order = [0]
    visited[0] = True

    for _ in range(n - 1):
        current = order[-1]
        best_dist = float("inf")
        best_idx = -1

        for j in range(n):
            if not visited[j]:
                dist = _haversine_distance(
                    stops[current].lat, stops[current].lng,
                    stops[j].lat, stops[j].lng,
                )
                if dist < best_dist:
                    best_dist = dist
                    best_idx = j

        if best_idx >= 0:
            visited[best_idx] = True
            order.append(best_idx)

    return order
