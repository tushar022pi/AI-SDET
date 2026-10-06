import re

from app.services.hash_service import generate_hash


class HierarchyBuilder:

    @staticmethod
    def normalize_heading(text):
        """
        Normalize heading text so the same heading can be
        matched across document versions.
        """

        text = text.strip().lower()

        # Remove document version information
        # Example:
        # "CT-200 Controller Manual — Version 1"
        # becomes:
        # "ct-200 controller manual —"
        text = re.sub(r"\bversion\s+\d+\b", "", text)

        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)

        # Remove leading section numbers
        # Examples:
        # "1. Installation" -> "installation"
        # "2. Initial Setup" -> "initial setup"
        # "3. Network Configuration" -> "network configuration"
        text = re.sub(r"^\d+[\.\)\-:\s]+", "", text)

        return text.strip()

    @staticmethod
    def create_logical_id(parent_path, heading):
        """
        Create a stable logical identity from document structure
        instead of content.
        """

        normalized = HierarchyBuilder.normalize_heading(heading)

        if parent_path:
            return f"{parent_path}/{normalized}"

        return normalized

    def build(self, pages, headings):

        nodes = []

        # ---------------------------------------------------------
        # STEP 1: Extract body text for every heading
        # ---------------------------------------------------------

        for i, heading in enumerate(headings):

            body_text = ""

            current_page = heading["page"]

            page_text = ""

            for page in pages:

                if page["page"] == current_page:
                    page_text = page["text"]
                    break

            heading_text = heading["heading"]

            start_index = page_text.find(heading_text)

            if start_index != -1:

                start_index += len(heading_text)

                if i < len(headings) - 1:

                    next_heading = headings[i + 1]

                    if next_heading["page"] == current_page:

                        end_index = page_text.find(
                            next_heading["heading"]
                        )

                        if end_index != -1:

                            body_text = page_text[
                                start_index:end_index
                            ]

                        else:

                            body_text = page_text[start_index:]

                    else:

                        body_text = page_text[start_index:]

                else:

                    body_text = page_text[start_index:]

            # -----------------------------------------------------
            # STEP 2: Determine hierarchy level
            # -----------------------------------------------------

            if heading["font_size"] >= 20:
                level = 1
            else:
                level = 2

            nodes.append(
                {
                    "id": len(nodes) + 1,
                    "heading": heading_text,
                    "page": current_page,
                    "level": level,
                    "parent": None,
                    "children": [],
                    "body_text": body_text.strip(),
                    "content_hash": generate_hash(
                        body_text.strip()
                    ),
                    "logical_node_id": None,
                }
            )

        # ---------------------------------------------------------
        # STEP 3: Build parent relationships
        # ---------------------------------------------------------

        parent_stack = []

        for node in nodes:

            level = node["level"]

            while (
                parent_stack
                and parent_stack[-1]["level"] >= level
            ):
                parent_stack.pop()

            if parent_stack:
                node["parent"] = parent_stack[-1]["id"]

            parent_stack.append(node)

        # ---------------------------------------------------------
        # STEP 4: Create stable logical identities
        # ---------------------------------------------------------

        logical_paths = {}

        for node in nodes:

            parent_id = node["parent"]

            if parent_id is None:

                parent_path = ""

            else:

                parent_node = next(
                    (
                        item
                        for item in nodes
                        if item["id"] == parent_id
                    ),
                    None
                )

                parent_path = (
                    parent_node["logical_node_id"]
                    if parent_node
                    else ""
                )

            logical_id = self.create_logical_id(
                parent_path,
                node["heading"]
            )

            base_id = logical_id

            count = logical_paths.get(base_id, 0) + 1

            logical_paths[base_id] = count

            if count > 1:
                logical_id = f"{base_id}#{count}"

            node["logical_node_id"] = logical_id

        # ---------------------------------------------------------
        # STEP 5: Build children relationships
        # ---------------------------------------------------------

        node_map = {
            node["id"]: node
            for node in nodes
        }

        for node in nodes:

            parent_id = node["parent"]

            if parent_id is not None:

                parent_node = node_map.get(parent_id)

                if parent_node:

                    parent_node["children"].append(
                        node["id"]
                    )

        return nodes