from app.models.document_node import DocumentNode


class NodeService:

    def save_nodes(
        self,
        db,
        nodes,
        version=1
    ):

        for node in nodes:

            db_node = DocumentNode(
                heading=node["heading"],
                level=node["level"],
                body_text=node["body_text"],
                content_hash=node["content_hash"],
                parent_id=node["parent"],

                document_version=version,

                logical_node_id=node["logical_node_id"],

                is_changed=False
            )

            db.add(db_node)

        db.commit()

        return {
            "message": f"Version {version} saved successfully"
        }