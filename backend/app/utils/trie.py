class TrieNode:
    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.values: set[str] = set()


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, value: str) -> None:
        normalized = value.casefold().strip()
        node = self.root
        for char in normalized:
            node = node.children.setdefault(char, TrieNode())
            node.values.add(value)

    def delete(self, value: str) -> None:
        normalized = value.casefold().strip()
        node = self.root
        path: list[tuple[TrieNode, str, TrieNode]] = []
        for char in normalized:
            child = node.children.get(char)
            if child is None:
                return
            path.append((node, char, child))
            node = child
        for parent, char, child in reversed(path):
            child.values.discard(value)
            if not child.values and not child.children:
                del parent.children[char]

    def prefix_search(self, prefix: str, limit: int = 8) -> list[str]:
        node = self.root
        for char in prefix.casefold().strip():
            node = node.children.get(char)
            if node is None:
                return []
        return sorted(node.values)[:limit]
