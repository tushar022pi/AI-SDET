from app.services.hash_service import generate_hash


class HierarchyBuilder:

    def build(self, pages, headings):

        nodes = []

        # Process each heading
        for i, heading in enumerate(headings):

            body_text = ""

            current_page = heading["page"]

            page_text = ""

            # Find matching page text
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

                    # Next heading on same page
                    if next_heading["page"] == current_page:

                        end_index = page_text.find(
                            next_heading["heading"]
                        )

                        if end_index != -1:
                            body_text = page_text[start_index:end_index]
                        else:
                            body_text = page_text[start_index:]

                    else:
                        body_text = page_text[start_index:]

                else:
                    body_text = page_text[start_index:]

            # Determine hierarchy level
            if heading["font_size"] >= 20:
                level = 1
            else:
                level = 2

            nodes.append({
                "id": len(nodes) + 1,
                "heading": heading_text,
                "page": current_page,
                "level": level,
                "parent": None,
                "children": [],
                "body_text": body_text.strip(),
                "content_hash": generate_hash(body_text)
            })

        # Assign parent relationships
        root_id = None

        for node in nodes:

            if node["level"] == 1:
                root_id = node["id"]

            elif node["level"] == 2:
                node["parent"] = root_id

        # Build children list
        for node in nodes:

            parent_id = node["parent"]

            if parent_id:

                for parent_node in nodes:

                    if parent_node["id"] == parent_id:
                        parent_node["children"].append(
                            node["id"]
                        )

        return nodes