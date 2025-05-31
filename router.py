
import heapq
from typing import Dict, List, Tuple, Any

from network import Network


class Router:

    def route_request(self, constraint_devices: List[str], network: Network):
        print("Routing request with constraints:", constraint_devices)

        # Find the nodes in the network topology that match the constraint devices
        constraint_nodes = [node["id"] for node in network.topology["topology"]["nodes"] if node["device_id"] in constraint_devices]

        print("Constraint nodes:", constraint_nodes)


        # Create a graph from the network topology
        topology_data = network.topology
        graph = self.create_graph_from_topology(topology_data)

        print("Graph created from topology:", graph)

        # Create a reverse graph
        reverse_graph = self.create_reverse_graph(graph)
        print("Reverse graph created:", reverse_graph)


        # Find the starting node and target node

        start_id = next((node["id"] for node in topology_data["topology"]["nodes"] if node.get("start")), None)
        end_id = next((node["id"] for node in topology_data["topology"]["nodes"] if node.get("end")), None)

        print("Starting id:", start_id)
        print("Ending id:", end_id)

        res = self.constrained_all_shortest_paths(graph, reverse_graph, source=start_id, target=end_id,constraints=constraint_nodes)

        print("Result of constrained all shortest paths:", res)
        _, all_paths = res

        return all_paths







    def create_graph_from_topology(self, topology_data):
        """
        Transforms a given network topology into a graph representation.

        Args:
            topology_data (dict): A dictionary representing the network topology
                                  with 'nodes' and 'connections'.

        Returns:
            dict: A dictionary representing the graph where keys are node IDs
                  and values are lists of tuples (connected_node_id, weight).
                  The weight is fixed at 1 for all connections.
        """
        graph = {}

        # Initialize graph with all nodes
        for node in topology_data["topology"]["nodes"]:
            graph[node["id"]] = []


        for connection in topology_data["topology"]["connections"]:
            source = connection["source"]
            target = connection["target"]
            weight = 1  # Assuming a weight of 1 for all connections

            graph[source].append((target, weight))
            graph[target].append((source, weight))

        return graph


    def create_reverse_graph(self, graph: Dict[Any, List[Tuple[Any, float]]]) -> Dict[Any, List[Tuple[Any, float]]]:
        """
        Creates a reverse graph where all edges are reversed.

        Args:
            graph (Dict[Any, List[Tuple[Any, float]]]): The original graph represented as an adjacency list.

        Returns:
            Dict[Any, List[Tuple[Any, float]]]: The reversed graph.
        """
        reverse_graph = {node: [] for node in graph}

        for u in graph:
            for v, weight in graph[u]:
                reverse_graph[v].append((u, weight))

        return reverse_graph



    def dijkstra(self, graph: Dict[Any, List[Tuple[Any, float]]], source: Any) -> Tuple[
        Dict[Any, float], Dict[Any, List[Any]]]:
        """
        Executes Dijkstra's algorithm and records, for each node, all predecessors that lead to a shortest path.

        Args:
            graph (Dict[Any, List[Tuple[Any, float]]]): The graph represented as an adjacency list.
            source (Any): The starting node for the Dijkstra algorithm.

        Returns:
            Tuple[Dict[Any, float], Dict[Any, List[Any]]]: A tuple containing:
                - dist (Dict[Any, float]): A dictionary where keys are nodes and values are their
                  minimum distances from the 'source'.
                - preds (Dict[Any, List[Any]]): A dictionary where keys are nodes and values are
                  lists of their predecessors on a shortest path from the 'source'.
        """

        dist = {node: float('inf') for node in graph}
        preds = {node: [] for node in graph}
        dist[source] = 0

        # Priority queue
        heap = [(0, source)]

        while heap:
            # Extract the node with the smallest distance.
            current_dist, u = heapq.heappop(heap)

            if current_dist > dist[u]: continue

            # Explore neighbors of the current node.
            for v, weight in graph[u]:
                new_dist = dist[u] + weight

                # If a shorter path to v is found
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    preds[v] = [u]  # Set u as the sole predecessor.
                    heapq.heappush(heap, (new_dist, v))  # Add v to the heap with its new distance.

                # If an equally short path to v is found:
                elif new_dist == dist[v]:
                    preds[v].append(u)  # Add u as an additional predecessor.

        return dist, preds

    def enumerate_paths(self, preds: Dict[Any, List[Any]], start: Any, end: Any) -> List[List[Any]]:
        """
        Given a graph of predecessors it generates all possible shortest paths from 'start' to 'end'.
        Uses a Depth-First Search (DFS) approach to reconstruct all unique shortest paths.

        Args:
            preds (Dict[Any, List[Any]]): A dictionary where keys are nodes and values are lists of their predecessors on a shortest path from the original source of the Dijkstra run.
            start (Any): The starting node of the paths to enumerate.
            end (Any): The ending node of the paths to enumerate.

        Returns:
            List[List[Any]]: A list of paths
        """

        all_paths = []

        def dfs(current_node: Any, path: List[Any]):
            # Base case
            if current_node == start:
                all_paths.append(path[::-1])
                return

            if current_node not in preds or not preds[current_node]: return
            for p in preds[current_node]: dfs(p, path + [p])

        dfs(end, [end])

        return all_paths

    def constrained_all_shortest_paths(
            self,
            graph: Dict[Any, List[Tuple[Any, float]]],
            reverse_graph: Dict[Any, List[Tuple[Any, float]]],
            source: Any,
            target: Any,
            constraints: List[Any]
    ) -> Tuple[float, List[List[Any]]]:
        """
        Finds all shortest paths from 'source' to 'target' that pass through at least one of the nodes in 'constraints'.

        Args:
            graph (Dict[Any, List[Tuple[Any, float]]]): The original graph.
            reverse_graph (Dict[Any, List[Tuple[Any, float]]]): The graph with all edges reversed
            source (Any): The starting node for the paths.
            target (Any): The ending node for the paths.
            constraints (List[Any]): A list of nodes.

        Returns:
            Tuple[float, List[List[Any]]]: A tuple containing:
                - best_cost (float): The minimum cost of such a constrained path.
                - all_paths (List[List[Any]]): A list of all unique shortest paths that satisfy the constraints.
        """

        # Case 1: No constraints.
        if not constraints:
            # Run Dijkstra
            dist_s, preds_s = self.dijkstra(graph, source)
            # If the target is unreachable
            if dist_s[target] == float('inf'): return float('inf'), []

            all_paths = self.enumerate_paths(preds_s, source, target)
            return dist_s[target], all_paths

        # Case 2: Constraints are provided.

        # Run Dijkstra from the source on the original graph.
        dist_s, preds_s = self.dijkstra(graph, source)

        # Run Dijkstra from the target on the reversed graph.
        dist_t, preds_t = self.dijkstra(reverse_graph, target)

        # Find the minimum cost to reach any constraint node from source and then reach target from that constraint node.
        best_cost = float('inf')
        best_constraints = []  # Stores constraint nodes that yield the `best_cost`.

        # Iterate through each constraint
        for c in constraints:
            # Ensure the constraint node is reachable from the source
            # and the target is reachable from the constraint node
            if c in dist_s and c in dist_t:
                if dist_s[c] < float('inf') and dist_t[c] < float('inf'):
                    # The total cost through a constraint node `c` is the sum of
                    # (source -> c) and (c -> target).
                    total_cost = dist_s[c] + dist_t[c]
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_constraints = [c]

                    elif total_cost == best_cost:
                        best_constraints.append(c)

        # If no valid path through any constraint node exists
        if best_cost == float('inf'):
            return float('inf'), []

        # For each optimal constraint node, generate all possible path combinations
        all_valid_paths = []

        for c in best_constraints:
            # Enumerate all shortest paths from source to 'c'
            paths_to_c = self.enumerate_paths(preds_s, source, c)

            # Enumerate all shortest paths from 'target' to 'c'
            paths_c_to_target_rev = self.enumerate_paths(preds_t, target, c)
            paths_c_to_target = [path[::-1] for path in paths_c_to_target_rev]

            # Concatenate the paths
            for p1 in paths_to_c:
                for p2 in paths_c_to_target:
                    combined = p1 + p2[1:]  # Slice to avoid duplicating 'c' in the middle of the path.
                    all_valid_paths.append(combined)

        # Remove any duplicate paths that
        unique_paths = []
        seen = set()
        for p in all_valid_paths:
            tup = tuple(p)  # Convert list to tuple for set hashing.
            if tup not in seen:
                seen.add(tup)
                unique_paths.append(p)

        return best_cost, unique_paths


