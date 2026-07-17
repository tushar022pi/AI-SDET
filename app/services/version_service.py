class VersionService:

    def compare_versions(
        self,
        version1_nodes,
        version2_nodes
    ):

        v1_hashes = {}

        for node in version1_nodes:
            v1_hashes[node.logical_node_id] = node

        changed = []
        unchanged = []
        new_nodes = []

        for node in version2_nodes:

            if node.logical_node_id not in v1_hashes:
                new_nodes.append(node.heading)

            else:

                old_node = v1_hashes[node.logical_node_id]

                if old_node.content_hash == node.content_hash:
                    unchanged.append(node.heading)

                else:
                    changed.append(node.heading)

        return {
            "unchanged": unchanged,
            "changed": changed,
            "new_nodes": new_nodes
        }