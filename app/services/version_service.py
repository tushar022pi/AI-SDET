class VersionService:

    def compare_versions(self, version1_nodes, version2_nodes):

        v1_nodes = {}

        for node in version1_nodes:
            # Ignore document title when comparing requirements
            if "controller manual" in node.heading.lower():
                continue

            v1_nodes[node.logical_node_id] = node

        changed = []
        unchanged = []
        new_nodes = []

        for node in version2_nodes:

            # Ignore document title
            if "controller manual" in node.heading.lower():
                continue

            if node.logical_node_id not in v1_nodes:
                new_nodes.append(node.heading)

            else:
                old_node = v1_nodes[node.logical_node_id]

                if old_node.content_hash == node.content_hash:
                    unchanged.append(node.heading)
                else:
                    changed.append({
                        "heading": node.heading,
                        "old_hash": old_node.content_hash,
                        "new_hash": node.content_hash
                    })

        return {
            "unchanged": unchanged,
            "changed": changed,
            "new_nodes": new_nodes
        }